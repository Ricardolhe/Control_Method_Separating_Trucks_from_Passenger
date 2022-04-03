#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计(参数校正)
# user: Ricardo
# Author: Ricardo
# create-time: 2021/4/3

import tools.dataframe_tools as dt
import numpy as np
import pandas as pd

from ETC_data_change.controlmodel import MPC
from main import Controls, PredictRoad

# 获取校正数据
control = Controls(3)
seg_data1 = control.controls_calibration()

# dt.df_save_csv(seg_data1, "data/seg_data.csv")
# seg_data1 = dt.df_load_csv("data/seg_data.csv")

# 参数校正
mpc = MPC(PredictRoad("predict", 4, 1000, 3))
BestX, BestY = mpc.calibration(seg_data1)
print(BestX)
print(BestY)
