class Plane:

    def __init__(self, type_id, name, capacity, prices, speed, max_num):
        self.id = type_id
        self.name = name
        self.speed = speed
        self.capacity = capacity
        self.prices = prices
        self.cost_matrix = None
        self.time_matrix = None
        self.max_num = max_num  # 如果不对数目进行限制，使用一个较大的数

    def calculate_cost_matrix_and_time_matrix(self, distance_matrix):
        n_cities = len(distance_matrix)
        self.cost_matrix = [[0] * n_cities for _ in range(n_cities)]
        self.time_matrix = [[0] * n_cities for _ in range(n_cities)]
        for i in range(n_cities):
            for j in range(i + 1, n_cities):
                self.time_matrix[i][j] = self.time_matrix[j][i] = distance_matrix[i][j] / self.speed
                # 分段定价（注意定价是按照天的，由于飞机要往返，单日飞行时间应×2）
                if 2 * self.time_matrix[i][j] <= 4: # 单日飞行时间不超过4小时
                    cost_per_hour = self.prices[0]
                elif 2 * self.time_matrix[i][j] <= 6:   # 单日飞行时间不超过6小时
                    cost_per_hour = self.prices[1]
                else:
                    cost_per_hour = self.prices[2]
                self.cost_matrix[i][j] = self.cost_matrix[i][j] = self.time_matrix[i][j] * cost_per_hour
