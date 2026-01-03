import json
from obj.Flow import Flow


# 读取飞机类型和数目分配情况
def read_plane_num_result(json_file):
    with open(json_file, 'r') as file:
        plane_num = json.load(file)

    plane_num = {tuple(map(int, k.split('_'))): v for k, v in plane_num.items()}

    new_plane_num = dict()
    for od_pair, plane_type_dict in plane_num.items():
        new_plane_type_dict = dict()
        for k, v in plane_type_dict.items():
            new_plane_type_dict[int(k)] = v
        new_plane_num[od_pair] = new_plane_type_dict
    plane_num = new_plane_num
    return plane_num


# 读取货流情况
def read_flow_result(json_file):
    with open(json_file, 'r') as file:
        flows = json.load(file)

    flows = {tuple(map(int, k.split('_'))): v for k, v in flows.items()}

    new_flows = dict()
    # 使用from_dict方法从字典中创建对象
    for od_pair, flow_dicts in flows.items():
        flow_lst = []
        for flow_dict in flow_dicts:
            flow_lst.append(Flow.from_dict(flow_dict))
        new_flows[od_pair] = flow_lst
    flows = new_flows

    return flows


if __name__ == '__main__':
    plane_num = read_plane_num_result('output/plane_num_result.json')
    print(plane_num)
    print(plane_num[0, 1])
    print(plane_num[1, 0])

    flows = read_flow_result('output/flow_result.json')
    for od_pair in flows:
        print(od_pair)
        for flow_dict in flows[od_pair]:
            # print(flow_dict.route)
            print(flow_dict)
