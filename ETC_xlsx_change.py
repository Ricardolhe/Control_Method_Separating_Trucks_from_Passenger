#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计(主线ETC的Xlsx文件转为csv保存)
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/29

from ETCdata import ETCDataUlit
import numpy as np
import pandas as pd
import datetime

year = 2021
month = 1
day = 19
nums = 32  # 32天
t0 = datetime.date(year, month, day)
for i in range(0, nums):
    # for i in range(0,nums):
    # 2021-01-19 ---- 2021-02-19
    str_date = str(t0 + datetime.timedelta(days=i)).replace("-", "")  # 转化为XXXXXXXX八位日期格式
    # datetime.timedelta(days=1)
    print(str_date)
    path_data = "data/沿江/" + str_date + "/03主线ETC门架数据-" + str_date + ".xlsx"  # xlsx文件放置路径
    path_all_car = "data/数据/ETC/allcar/" + str_date + ".csv"  # csv文件保存路径
    ETCDataUlit.get_csv_etc(path_data, path_all_car)  # 单独把这段代码拿出时请将cls改为类名