import pandas as pd
from geopy.distance import geodesic, distance

from obj.City import City
from obj.Plane import Plane


class Instance:

    def __init__(self, excel_path, speeds, max_num, hub_cost):
        df_city = pd.read_excel(excel_path, sheet_name='城市')
        cities = []
        for index, row in df_city.iterrows():
            code = row["城市代号"]
            name = row["城市名"]
            lat = row["纬度"]
            lon = row["经度"]
            city = City(index, code, name, lat, lon, hub_cost[code])
            cities.append(city)

        distance_matrix = [[0] * len(cities) for _ in range(len(cities))]
        # 计算两两城市之间的距离
        for i in range(len(cities)):
            for j in range(i + 1, len(cities)):
                city1 = cities[i]
                city2 = cities[j]
                coords1 = (city1.lat, city1.lon)
                coords2 = (city2.lat, city2.lon)
                # 计算距离
                distance = geodesic(coords1, coords2).kilometers
                distance_matrix[i][j] = distance_matrix[j][i] = round(distance)

        # 计算每种机型在两两城市间飞行的飞行时间和飞行成本
        Outsourcing = Plane(0, "Outsourcing", 1,
                            (0.06, 0.06, 0.06), speeds["Outsourcing"], max_num["Outsourcing"])
        B737 = Plane(1, "B737", 14000,
                     (4.5, 4, 3.5), speeds["B737"], max_num["B737"])
        B757 = Plane(2, "B757", 28000, (7.5, 7, 6.5),
                     speeds["B757"], max_num["B757"])
        A300 = Plane(3, "A300", 40000, (8.5, 8, 7.5),
                     speeds["A300"], max_num["A300"])
        planes = [Outsourcing, B737, B757, A300]

        for plane in planes:
            plane.calculate_cost_matrix_and_time_matrix(distance_matrix)

        # 读取O-D对的数据
        df_demand = pd.read_excel(excel_path, sheet_name='OD需求', index_col=0, header=0).iloc[:-1, :-1]
        df_demand.fillna(0, inplace=True)
        demand_matrix = [[0] * len(cities) for _ in range(len(cities))]
        for i in range(len(cities)):
            for j in range(len(cities)):
                if i == j:
                    continue
                city1 = cities[i]
                city2 = cities[j]
                demand_matrix[i][j] = df_demand.loc[city1.code, city2.code]

        self.cities = cities
        self.planes = planes
        self.demand_matrix = demand_matrix


if __name__ == '__main__':
    # 枢纽建造成本
    hub_cost = dict()
    for hub_code in [10, 21, 23]:  # 一线城市
        hub_cost[hub_code] = 20000
    for hub_code in [27, 28, 29, 371]:  # 二线城市
        hub_cost[hub_code] = 15000
    for hub_code in [24, 510, 536, 571, 591, 731, 755, 852, 886, 991]:  # 三线城市
        hub_cost[hub_code] = 10000
    speeds = {"Outsourcing": 800, "B737": 750, "B757": 870, "A300": 870}
    max_num = {"Outsourcing": 10000000, "B737": 20, "B757": 20, "A300": 20}
    instance = Instance("../data/data.xlsx", speeds, max_num, hub_cost)
    print(sum([sum(lst) for lst in instance.demand_matrix]))
