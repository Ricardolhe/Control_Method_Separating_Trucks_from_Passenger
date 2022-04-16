# 周期获取微波数据
from ETC_data_change.weibodata import DataUlit,PeriodDataUlit
import pandas as pd
import tools.dataframe_tools as dt

if __name__ == "__main__":
    path = "data/副本沪苏浙高速交调数据20210119-20210219(1).csv"
    path_result_3 = "data/map/maptest3/road.rou.xml"
    path_result_4 = "data/map/maptest4/road.rou.xml"
    path_result_5 = "data/map/maptest5/road.rou.xml"
    deviceID = 71270320100006
    direction = 0
    date = "2021-01-26"
    start_time = "2021-01-26 12:00:00"
    end_time = "2021-01-26 14:00:00"

    weibo = DataUlit()
    weibo.df_read_csv(path)
    etc_data = weibo.select_data(deviceID, direction)  # 筛选合适的数据
    etc_data_20 = etc_data.get_alltype_perioddata(start_time, end_time, 20)  # 20min聚合
    df_PtoT = pd.DataFrame(columns=["start_time", "end_time", "PtoT"])  # 各个时段客货比关系
    df_PtoT["PtoT"] = [1, 1/4, 4, 1/3, 3, 1]  # 各个时段客货比关系
    # df_PtoT["PtoT"] = [1/6]*6  # 各个时段客货比关系
    df_PtoT.loc[:,["start_time", "end_time"]] = etc_data_20.loc[:,["start_time", "end_time"]]
    etc_data_20 = PeriodDataUlit(etc_data_20)
    etc_data_20.extend_all_flow(1.6, False)
    df_PtoT = etc_data_20.get_P_to_T(df_PtoT)
    etc_data_20.extend_PandT_flow(df_PtoT,False)  # 三车道交通量
    # etc_data_20=etc_data_20.get_percent_eachtime()
    etc_data_20 = etc_data_20.get_num_eachtime()
    PeriodDataUlit.change_to_sumo_flow_num(etc_data_20, path_result_3, start_time, 3)
    PeriodDataUlit.change_to_sumo_flow_num(etc_data_20, path_result_4, start_time, 4)
    PeriodDataUlit.change_to_sumo_flow_num(etc_data_20, path_result_5, start_time, 5)