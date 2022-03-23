#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计-1.19direction0 每个断面的速度
# user: Sisi
# Author: Ricardo
# createtime: 2022/2/22

import numpy as np
import pandas as pd
import datetime
# 还需要conda install openpyxl

# path = "data/speed.xlsx"
# path_save = "data/speed.csv"
# df_data = pd.read_excel(path,sheet_name=1,header=0)  #读取会非常慢
# df_data.to_csv(path_save, encoding="utf-8", index=False)

path_csv = "data/speed.csv"
path_result = "data/data19.xlsx"
df_data_csv = pd.read_csv(path_csv)
df_data_csv =df_data_csv.loc[(df_data_csv["direction"] == 0)].reset_index(drop=True) # 筛选方向0
df_data_csv["statTime"] = pd.to_datetime(df_data_csv["statTime"]) # 时间列转成时间格式
time_from = datetime.datetime.strptime("2021-01-19", '%Y-%m-%d')
time_to = time_from + datetime.timedelta(days=1)
df_data_csv =df_data_csv.loc[(df_data_csv["statTime"] >= time_from) & (df_data_csv["statTime"] < time_to)].reset_index(drop=True) # 筛选19日的
df_data_csv.to_excel(path_result,index=False)
