# 周期获取微波数据
from ETC_data_change.weibodata import DataUlit
from tools.dataframe_tools import DaTaFrameTool
path = "../data/副本沪苏浙高速交调数据20210119-20210219(1).csv"
# path_result = "../data/weibo_result.xlsx"
path_result = "../data/weibo_period20.xlsx"
deviceID = 71270320100006
direction = 0
date = "2021-01-26"
start_time = "2021-01-26 00:00:00"
end_time = "2021-01-27 00:00:00"

weibo = DataUlit()
weibo.df_read_csv(path)
etc_data = weibo.select_data(deviceID, direction)  # 筛选合适的数据
period5_data = etc_data.get_alltype_perioddata(start_time, end_time, 20)
DaTaFrameTool.df_save_excel(period5_data, path_result)