from ETCdata import ETCDataUlit
import numpy as np
import pandas as pd
import datetime

year = 2021
month = 1
day = 19
nums = 32  # 32天
t0 = datetime.date(year, month, day)
etc_data = ETCDataUlit()
for i in range(0, nums):
    str_date = str(t0 + datetime.timedelta(days=i)).replace("-", "")  # 转化为XXXXXXXX八位日期格式
    print(str_date)
    path_csv = "data/数据/ETC/allcar/" + str_date + ".csv"  # json文件保存路径

    etc_data.get_car_speed(path_csv, str_date)

    path_each_car = "data/数据/ETC/eachcar/" + str_date + ".csv"
    etc_data.save_car_speed(path_each_car)
    # 保存为xlsx格式的数据
    path_each_car_xlsx = "data/数据/ETC/eachcarExcel/" + str_date + ".xlsx"
    etc_data.save_car_speed_xlsx(path_each_car_xlsx)