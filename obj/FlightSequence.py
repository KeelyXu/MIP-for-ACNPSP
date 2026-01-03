class FlightSequence:

    def __init__(self, take_off_slot_ids, total_stay_time, plane_type_and_ids):
        self.take_off_slot_ids = take_off_slot_ids   # 每个起飞航班使用的城市的可用起飞时间点id
        self.total_stay_time = total_stay_time     # 整个flight sequence耗时
        self.plane_type_and_ids = plane_type_and_ids     # 中间每条航线使用的货机及其编号

