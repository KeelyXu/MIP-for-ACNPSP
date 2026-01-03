import gurobipy as gp
from gurobipy import GRB, quicksum
import json

from obj.Instance import Instance
from obj.Flow import Flow


def construct_routes(from_to, start, end):
    if start == end:
        return [[end]]

    routes = []
    for next in from_to[start]:
        routes.extend(construct_routes(from_to, next, end))
    for route in routes:
        route.insert(0, start)
    return routes

n_cities = 17

# 设置一些参数（这些参数并非题目给出的，因此有修改余地）
# 飞机飞行速度
speeds = {"Outsourcing": 600, "B737": 750, "B757": 800, "A300": 800}
# 每种类型飞机的最大可用数目（外包货物总重量不做限制）
max_num = {"Outsourcing": 10000000, "B737": 10, "B757": 10, "A300": 10}
# 枢纽建造成本
hub_cost = dict()
for hub_code in [10, 21, 755, 852, 886]:   # 一线城市
    hub_cost[hub_code] = 12
for hub_code in [23, 27, 28, 29, 371, 510, 571, 731]:  # 二线城市
    hub_cost[hub_code] = 15
for hub_code in [24, 536, 591, 991]:  # 三线城市
    hub_cost[hub_code] = 18
# 设置0-1矩阵，表示路线是否有外包货机可用
outsource_available = [[1] * n_cities for _ in range(n_cities)]
# 折扣系数
alpha = 0.8
# 每个O-D对最多允许经过的枢纽个数
max_visit_hub_num = 2

# 构造算例
instance = Instance("data/data.xlsx", speeds, max_num, hub_cost)
cities = instance.cities
planes = instance.planes
demand_matrix = instance.demand_matrix

# 定义一些辅助的集合
K = list(range(len(planes)))
N = list(range(n_cities))
E = [(i, j) for i in range(n_cities) for j in range(n_cities) if i != j]

# 建立Gurobi模型
model = gp.Model("AirCargoNetwork")

# 定义决策变量
y = model.addVars(n_cities, vtype=GRB.BINARY, name="y")

x = dict()
for i, j in E:
    for o, d in E:
        x[i, j, o, d] = model.addVar(vtype=GRB.CONTINUOUS, name=f"x_({i},{j})^({o},{d})")

ms = dict()
for k in K:
    if k == 0:
        continue
    for i, j in E:
        ms[0, i, j, k] = model.addVar(vtype=GRB.INTEGER, name=f"m_(0,{i},{j})^{k}")
        ms[1, i, j, k] = model.addVar(vtype=GRB.INTEGER, name=f"m_(1,{i},{j})^{k}")

mo = dict()
for i, j in E:
    mo[i, j] = model.addVar(vtype=GRB.INTEGER, name=f"m_({i},{j})^0")
    # mo[i, j] = model.addVar(vtype=GRB.CONTINUOUS, name=f"m_({i},{j})^0")

z = dict()
for i, j in E:
    for o, d in E:
        z[i, j, o, d] = model.addVar(vtype=GRB.BINARY, name=f"z_({i},{j})^({o},{d})")

s = dict()
for i in N:
    for o, d in E:
        s[i, o, d] = model.addVar(vtype=GRB.INTEGER, name=f"s_({i},{o})^{d}")

# 定义目标函数
sum_hub_cost = quicksum([city.hub_cost * y[city.id] for city in cities])
sum_self_own_without_discount = quicksum([planes[k].cost_matrix[i][j] * ms[0, i, j, k] for i, j in E for k in K if k != 0])
sum_self_own_with_discount = alpha * quicksum([planes[k].cost_matrix[i][j] * ms[1, i, j, k] for i, j in E for k in K if k != 0])
sum_outsource_cost = quicksum([planes[0].cost_matrix[i][j] * mo[i, j] for i, j in E])
# (1)
model.setObjective(sum_hub_cost + sum_self_own_with_discount + sum_self_own_without_discount + sum_outsource_cost, GRB.MINIMIZE)

# 添加约束条件
# (2): 如果某地不是枢纽，不能有非起点为该地的货物从该点转出
M = sum([sum(lst) for lst in demand_matrix])
for o, d in E:
    for i, j in E:
        if i != o:
            model.addConstr(x[i, j, o, d] <= M * y[i])

# (3): 如果某地不是枢纽，不能有非目的地为该地的货物转入该点
for o, d in E:
    for i, j in E:
        if j != d:
            model.addConstr(x[i, j, o, d] <= M * y[j])

# (4): 中转节点流平衡
for o, d in E:
    for l in N:
        if l != o and l != d:
            model.addConstr(quicksum([x[i, l, o, d] for i in N if i != l]) == quicksum([x[l, j, o, d] for j in N if j != l]))

# (5): O-D对中从O点流出的货物等于O-D对的需求
for o, d in E:
    model.addConstr(quicksum([x[o, j, o, d] for j in N if j != o]) == demand_matrix[o][d])

# (6): O-D对中从D点流入的货物等于O-D对的需求
for o, d in E:
    model.addConstr(quicksum([x[i, d, o, d] for i in N if i != d]) == demand_matrix[o][d])

# (7): 如果某线路没有外包货机可用，限制该线路上的外包重量为0
for i, j in E:
    if outsource_available[i][j] == 0:
        mo[i, j].ub = 0
        mo[i, j].lb = 0
        # model.addConstr(mo[i, j] == 0)

# (8): 每条线路上的最大运输量不能超过线路的最大运力
for i, j in E:
    model.addConstr(quicksum([x[i, j, o, d] for o, d in E]) <=
                    quicksum([planes[k].capacity * (ms[0, i, j, k] + ms[1, i, j, k]) for k in K if k != 0]) + planes[0].capacity * mo[i, j])

# (9)(10): 往返飞机数是相同的
for i, j in E:
    for k in K:
        if k != 0:
            model.addConstr(ms[0, i, j, k] == ms[0, j, i, k])
            model.addConstr(ms[1, i, j, k] == ms[1, j, i, k])

# (11): 自有可用飞机数目限制
for k in K:
    if k != 0:
        model.addConstr(quicksum([ms[0, i, j, k] + ms[1, i, j, k] for i, j in E]) <= 2 * planes[k].max_num)

# (12): 只有启用的线路上才能有货物运输
for o, d in E:
    for i, j in E:
        model.addConstr(x[i, j, o, d] <= M * z[i, j, o, d])

# (13): 顺序号递增约束
M = max_visit_hub_num + 2
for o, d in E:
    for i, j in E:
        model.addConstr(s[i, o, d] + 1 - s[j, o, d] - M * (1 - z[i, j, o, d]) <= 0)

# (14): O-D对中起点顺序号为0
for o, d in E:
    s[o, o, d].ub = 0
    s[o, o, d].lb = 0
    # model.addConstr(s[o, o, d] == 0)

# (15): O-D对中终点的顺序号不能大于允许经过的最大枢纽数+1
for o, d in E:
    model.addConstr(s[d, o, d] <= max_visit_hub_num + 1)

# (16): O-D对中不会有流出D的货物
for o, d in E:
    for j in N:
        if j != d:
            x[d, j, o, d].ub = 0
            x[d, j, o, d].lb = 0
            # model.addConstr(x[d, j, o, d] == 0)

# (17): O-D对中不会有流入O的货物
for o, d in E:
    for i in N:
        if i != o:
            x[i, o, o, d].ub = 0
            x[i, o, o, d].lb = 0
            # model.addConstr(x[i, o, o, d] == 0)

# (18)(19)(20)(21)对应约束已包含在变量定义中

# (22): 如果航段起点不是枢纽，无法使用折扣
for i in N:
    for k in K:
        if k != 0:
            M = planes[k].max_num
            model.addConstr(quicksum([ms[1, i, j, k] for j in N if j != i]) <= M * y[i])

# (23): 如果航段终点不是枢纽，无法使用折扣
for j in N:
    for k in K:
        if k != 0:
            M = planes[k].max_num
            model.addConstr(quicksum(ms[1, i, j, k] for i in N if i != j) <= M * y[j])


# 求解模型
# model.setParam("TimeLimit", 100)
model.optimize()

print('*' * 100)
print('*' * 100)
print()
# 获取求解结果，并解释相应含义
# 查看枢纽选址
hubs = []
for i in N:
    if y[i].x > 0.5:  # 城市被选为枢纽
        hubs.append(i)

s = "枢纽城市："
for hub_id in hubs:
    s += cities[hub_id].name + " "
print(s)

print()
print('*' * 100)
print()

# 查看两两城市间使用的飞机类型及数目
plane_num = dict()
for i, j in E:
    plane_num_of_ij = dict()
    s = f"{cities[i].name}-{cities[j].name}:\t"
    s += f"外包{round(mo[i, j].x, 2)}kg\t"
    for k in K:
        if k != 0:
            n = round(ms[0, i, j, k].x + ms[1, i, j, k].x)
            s += f"自有{planes[k].name}飞机{n}架\t"
            plane_num_of_ij[k] = n
        else:
            plane_num_of_ij[k] = round(mo[i, j].x)
    plane_num[i, j] = plane_num_of_ij
    print(s)

print()
print('*' * 100)
print()

# 查看货流情况
flows = dict()
for o, d in E:
    print(f"(O, D) = ({cities[o].name}, {cities[d].name}) 货流情况")
    from_to = dict()
    flow_of_OD = []
    for i, j in E:
        if x[i, j, o, d].x > 1e-3:  # OD在路径上有货流
            # print(f"{cities[i].name} -> {cities[j].name}: {round(x[i, j, o, d].x, 2)}kg")
            if i not in from_to:
                from_to[i] = [j]
            else:
                from_to[i].append(j)
    if len(from_to) > 0:    # 两个城市间的O-D是存在需求的
        # 拼接路径
        routes = construct_routes(from_to, o, d)
        # 每条路径上最小的流就是这个路径对应的flow amount
        for route in routes:
            min_flow_amount = 1e8
            for i in range(len(route) - 1):
                if x[route[i], route[i + 1], o, d].x < min_flow_amount:
                    min_flow_amount = x[route[i], route[i + 1], o, d].x
            s = f"{cities[o].name}"
            for city_id in range(1, len(route)):
                s += f" -> {cities[route[city_id]].name}"
            flow = Flow(route, min_flow_amount, s)
            flow_of_OD.append(flow)
            print(flow)
    else:
        print("O-D需求为0")
    flows[o, d] = flow_of_OD
    print()

print('*' * 100)
print('*' * 100)

# 将结果写入文件
# 写入json时要把tuple转为str
json_plane_num = {'_'.join(map(str, k)): v for k, v in plane_num.items()}
with open('output/plane_num_result.json', 'w') as file:
    json.dump(json_plane_num, file)

json_flows = {'_'.join(map(str, k)): [flow.to_dict() for flow in v] for k, v in flows.items()}
with open('output/flow_result.json', 'w') as file:
    json.dump(json_flows, file)
