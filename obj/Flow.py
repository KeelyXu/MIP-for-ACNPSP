class Flow:

    def __init__(self, route, amount, str_route=None):
        self.route = route
        self.amount = amount
        self.str_route = str_route

    def to_dict(self):
        return {'route': self.route, 'amount': self.amount, 'str_route': self.str_route}

    def __str__(self):
        return self.str_route + f": {round(self.amount, 2)}kg"

    @staticmethod
    def from_dict(data):
        return Flow(data['route'], data['amount'], data['str_route'])


if __name__ == '__main__':
    import json

    # # 写入文件
    # flows = []
    # flow1 = Flow([1, 2, 3], 100)
    # flow2 = Flow([0, 4, 3], 10, "0 -> 4 -> 3")
    # for flow in [flow1, flow2]:
    #     flows.append(flow.to_dict())
    # with open('test.json', 'w') as file:
    #     json.dump(flows, file)

    # 读取文件
    with open('test.json', 'r') as file:
        flow_dicts = json.load(file)

    # 使用from_dict方法从字典中创建对象
    flows = []
    for flow_dict in flow_dicts:
        flows.append(Flow.from_dict(flow_dict))

    for flow in flows:
        print(flow.route)
        print(flow.amount)
        print(flow.str_route)
        print()
