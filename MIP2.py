import gurobipy as gp
from gurobipy import GRB, quicksum

from read_result import read_plane_num_result, read_flow_result
from obj.Instance import Instance
from obj.FlightSequence import FlightSequence
from obj.PlaneScheduled import PlaneScheduled

plane_num_of_city_pair = read_plane_num_result('output/plane_num_result.json')
flows_of_cites = read_flow_result('output/flow_result.json')

# 获取所有货流
flows = []
for od_pair in flows_of_cites:
    flows.extend(flows_of_cites[od_pair])

n_cities = 17
# 参数设置
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

# 构造算例
instance = Instance("data/data.xlsx", speeds, max_num, hub_cost)
cities = instance.cities
planes = instance.planes

# 查看当前的飞机数目安排
for e in plane_num_of_city_pair:
    print(f"{cities[e[0]].name}-{cities[e[1]].name}:\t外包{plane_num_of_city_pair[e][0]}kg\t自有B737飞机{plane_num_of_city_pair[e][1]}架"
          f"\t自有B757飞机{plane_num_of_city_pair[e][2]}架\t自有A300飞机{plane_num_of_city_pair[e][3]}架")
for od_pair in flows_of_cites:
    for flow_dict in flows_of_cites[od_pair]:
        # print(flow_dict.route)
        print(flow_dict)

# 设置各个城市可行的起飞时间（以小时为单位），为简化问题，认为每个城市可行的起飞时间集合相同
delta = 4
E = [(i, j) for i in range(n_cities) for j in range(n_cities) if i != j]
A = [i * delta for i in range(int(24 / delta))]
A = {e: A for e in E}
# 设置各个机场的中转时间，为简化考虑，认为每个机场的中转时间都是4h
trans_time = 4
transship_time = [trans_time for i in range(n_cities)]


# 对每个OD对上的每个货流，都枚举其所有可能的飞行方案
def enumerate_feasible_flight_sequence(route, earliest_start_time=0, latest_end_time=24):
    feasible_flight_sequences = []
    if len(route) == 2:     # 直接枚举即可
        start = route[0]
        end = route[1]
        for i in range(len(A[start, end])):
            # 起点机场可起飞的时间
            feasible_take_off_time = A[start, end][i]
            if feasible_take_off_time < earliest_start_time:
                continue    # 只考虑迟于最早出发时间的的起飞时间
            # 从start到end可用的飞机
            for plane_type_id in plane_num_of_city_pair[start, end]:
                if plane_num_of_city_pair[start, end][plane_type_id] > 0:    # 当前线路上使用了该飞机
                    if feasible_take_off_time + planes[plane_type_id].time_matrix[start][end] + \
                            transship_time[end] < latest_end_time:
                        # 航段可行，加入flight sequences
                        stay_time = planes[plane_type_id].time_matrix[start][end] + transship_time[end]
                        if plane_type_id != 0:  # 对自有货机，需精确至相应类型内的飞机编号
                            for plane_id in range(plane_num_of_city_pair[start, end][plane_type_id]):
                                new_flight_sequence = FlightSequence([i], stay_time, [(plane_type_id, plane_id)])
                                feasible_flight_sequences.append(new_flight_sequence)
                        else:   # 对外包机
                            new_flight_sequence = FlightSequence([i], stay_time, [(0, 0)])
                            feasible_flight_sequences.append(new_flight_sequence)
        return feasible_flight_sequences

    start = route[0]
    end = route[1]
    for i in range(len(A[start, end])):
        # 起点机场可起飞的时间
        feasible_take_off_time = A[start, end][i]
        if feasible_take_off_time < earliest_start_time:
            continue
        # 从start到end可用的飞机
        for plane_type_id in plane_num_of_city_pair[start, end]:
            if plane_num_of_city_pair[start, end][plane_type_id] > 0:  # 当前线路上使用了该飞机
                if feasible_take_off_time + planes[plane_type_id].time_matrix[start][end] + \
                        transship_time[end] < latest_end_time:
                    # 当前航段可行
                    earliest_start_time_of_next_city = (feasible_take_off_time + planes[plane_type_id].time_matrix[start][end] +
                                                        transship_time[end])
                    stay_time = planes[plane_type_id].time_matrix[start][end] + transship_time[end]
                    for flight_sequence in enumerate_feasible_flight_sequence(route[1:], earliest_start_time_of_next_city, latest_end_time):
                        if plane_type_id != 0:
                            for plane_id in range(plane_num_of_city_pair[start, end][plane_type_id]):
                                plane_type_and_ids = [(plane_type_id, plane_id)] + flight_sequence.plane_type_and_ids
                                take_off_slot_ids = [i] + flight_sequence.take_off_slot_ids
                                total_stay_time = stay_time + flight_sequence.total_stay_time
                                new_flight_sequence = FlightSequence(take_off_slot_ids, total_stay_time, plane_type_and_ids)
                                feasible_flight_sequences.append(new_flight_sequence)
                        else:
                            plane_type_and_ids = [(0, 0)] + flight_sequence.plane_type_and_ids
                            take_off_slot_ids = [i] + flight_sequence.take_off_slot_ids
                            total_stay_time = stay_time + flight_sequence.total_stay_time
                            new_flight_sequence = FlightSequence(take_off_slot_ids, total_stay_time, plane_type_and_ids)
                            feasible_flight_sequences.append(new_flight_sequence)

    return feasible_flight_sequences

# 定义一些辅助集合
F = dict()

for flow in flows:
    feasible_flight_sequences = enumerate_feasible_flight_sequence(flow.route)
    for flight_seq in feasible_flight_sequences:
        F[flight_seq] = flow    # 建立飞行方案与货流的对应关系
    # print(flow)
    # print(len(feasible_flight_sequences))
    # for seq in feasible_flight_sequences:
    #     print(f"take_off_slot_ids = {seq.take_off_slot_ids}\ttotal_stay_time = {seq.total_stay_time}h\tplane_type_and_ids = {seq.plane_type_and_ids}")

K = list(range(len(planes)))
N = list(range(n_cities))
E_H = [(i, j) for i in range(n_cities) for j in range(n_cities) if i < j]
R = flows
J = []
for od_pair in plane_num_of_city_pair:
    for plane_type_id in plane_num_of_city_pair[od_pair]:
        if plane_type_id != 0:
            if od_pair[0] > od_pair[1]: # 对自有货机，考虑单边即可
                break
            for plane_id in range(plane_num_of_city_pair[od_pair][plane_type_id]):
                J.append(PlaneScheduled(od_pair[0], od_pair[1], plane_type_id, plane_id))
        else:
            if plane_num_of_city_pair[od_pair][0] > 0:
                J.append(PlaneScheduled(od_pair[0], od_pair[1], plane_type_id, 0))

# 建立模型
model = gp.Model("CargoAssignmentAndTimeTableSetting")

# 添加决策变量
x = {f: model.addVar(vtype=GRB.CONTINUOUS) for f in F}
y = {(e, a, j): model.addVar(vtype=GRB.BINARY) for e in E for a in range(len(A[e])) for j in J if j.type_id != 0}
z = {j: model.addVar(vtype=GRB.BINARY) for j in J}
# 增加决策变量，外包机每个起飞时间点每条弧上外包重量
w = {(e, a, j): model.addVar(vtype=GRB.CONTINUOUS) for e in E for a in range(len(A[e])) for j in J if j.type_id == 0}

# 只有服务于e弧段的飞机j的y[e, a, j]才有可能为1
for e, a, j in y:
    if j.end1 == min(e) and j.end2 == max(e):
        continue
    y[e, a, j].ub = 0

# 只有服务于e弧段的外包机的w[e, a, j]才有可能大于0
for e, a, j in w:
    if j.end1 == e[0] and j.end2 == e[1]:
        continue
    w[e, a, j].ub = 0

# 添加目标函数
# (1) 最小化滞留时间
print("set objective")
model.setObjective(quicksum([f.total_stay_time * x[f] for f in F]), GRB.MINIMIZE)

# 添加约束条件
# (2) 如果飞行方案服务的是运输流r，运输量应等于之前求得的最优解
print("set constraint1")
for r in R:
    lhs = 0
    for f in F:
        if F[f] == r:
            lhs += x[f]
    model.addConstr(lhs == r.amount, name=f"Cons1_{r}")

# (3) 使用的飞机数目/外包重量应与上一个模型求解结果对应
print("set constraint2")
for e in E:
    for plane_type_id in K:
        if plane_type_id != 0:
            model.addConstr(quicksum([y[e, a, j] for a in range(len(A[e])) for j in J if j.type_id == plane_type_id]) ==
                            plane_num_of_city_pair[e][plane_type_id], name="Cons2-1")
        else:
            model.addConstr(quicksum([w[e, a, j] for a in range(len(A[e])) for j in J if j.type_id == 0]) == plane_num_of_city_pair[e][0], name=f"Cons2-2")

print("set constraint3")
sigma = dict()
for f in F:
    flow = F[f]
    for i in range(len(flow.route) - 1):
        e = (flow.route[i], flow.route[i + 1])
        type_id = f.plane_type_and_ids[i][0]
        plane_id = f.plane_type_and_ids[i][1]
        a = f.take_off_slot_ids[i]
        # 找到对应航段的对应飞机
        if type_id == 0:
            for j in J:
                if j.type_id == 0 and j.end1 == e[0] and j.end2 == e[1]:
                    sigma[f, j, e, a] = 1
                    # w[e, a, j].ub = GRB.INFINITY
                    break
        else:
            for j in J:
                if j.type_id == type_id and j.plane_id == plane_id and j.end1 == min(e) and j.end2 == max(e):
                    sigma[f, j, e, a] = 1
                    # y[e, a, j].ub = 1
                    break

for e in E:
    print(e[0], e[1])
    for a in range(len(A[e])):
        for j in J:
            lhs = 0
            for f_, j_, e_, a_ in sigma:
                if j_ == j and e_ == e and a_ == a:
                    lhs += x[f_]

            if j.type_id != 0:
                model.addConstr(lhs <= planes[j.type_id].capacity * y[e, a, j],
                                name=f"Cons3_{e}_{a}_{j.type_id}_{j.plane_id}_{j.end1}_{j.end2}")
            else:
                model.addConstr(lhs <= w[e, a, j], name=f"Cons3_{e}_{a}_{j.type_id}_{j.plane_id}_{j.end1}_{j.end2}")

M = 24

print("set constraint4")
for e in E_H:
    e_rvs = (e[1], e[0])
    for j in J:
        if j.type_id != 0 and j.end1 == e[0] and j.end2 == e[1]:
            model.addConstr(quicksum([A[e][a] * y[e, a, j] for a in range(len(A[e]))]) -
                            quicksum([A[e_rvs][a] * y[e_rvs, a, j] for a in range(len(A[e_rvs]))]) >=
                            planes[j.type_id].time_matrix[e[1]][e[0]] + transship_time[e[0]] - M * z[j], name=f"Cons4-1_{e}_{j.type_id}_{j.plane_id}_{j.end1}_{j.end2}")
            model.addConstr(quicksum([A[e_rvs][a] * y[e_rvs, a, j] for a in range(len(A[e_rvs]))]) -
                            quicksum([A[e][a] * y[e, a, j] for a in range(len(A[e]))]) >=
                            planes[j.type_id].time_matrix[e[0]][e[1]] + transship_time[e[1]] - M * (1 - z[j]), name=f"Cons4-2_{e}_{j.type_id}_{j.plane_id}_{j.end1}_{j.end2}")

print("set constraint5")
# 防止对称解
for e in E_H:
    for i in range(len(J)):
        for j in range(i + 1, len(J)):
            j1 = J[i]
            j2 = J[j]
            if j1.type_id != j2.type_id:
                continue
            if j1.type_id == 0:
                continue
            if j1.end1 == min(e) and j1.end2 == max(e) and j2.end1 == min(e) and j2.end2 == max(e):
                model.addConstr(quicksum([A[e][a] * y[e, a, j1] for a in range(len(A[e]))]) <=
                                quicksum([A[e][a] * y[e, a, j2] for a in range(len(A[e]))]), name="Cons5")

# 每架自有飞机只能单边飞行一次
for j in J:
    if j.type_id != 0:
        e = (j.end1, j.end2)
        model.addConstr(quicksum(y[e, a, j] for a in range(len(A[e]))) == 1)
        e = (j.end2, j.end1)
        model.addConstr(quicksum(y[e, a, j] for a in range(len(A[e]))) == 1)

model.optimize()

for e, a, j in y:
    if y[e, a, j].x > 0.5:
        print(f"飞机({cities[j.end1].name}-{cities[j.end2].name})[类型:{planes[j.type_id].name} 编号:{j.plane_id}]: {cities[e[0]].name}->{cities[e[1]].name} {A[e][a]}时起飞")

for f in F:
    if x[f].x > 1e-3:     # 有货流使用该飞行方案
        flow = F[f]
        s = ""
        for i in range(len(flow.route) - 1):
            from_city = cities[flow.route[i]].name
            to_city = cities[flow.route[i + 1]].name
            plane_type = planes[f.plane_type_and_ids[i][0]].name
            plane_id = f.plane_type_and_ids[i][1]
            e = (flow.route[i], flow.route[i + 1])
            take_off_time = A[e][f.take_off_slot_ids[i]]
            s += f"{from_city}--{plane_type}飞机{plane_id}[{take_off_time}时起飞]({round(x[f].x,3)}kg)-->{to_city} "
        print(s)
