#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# createtime: 2021/12/21


import numpy as np
import pandas as pd

if __name__ == "__main__":
    path = "data/副本沪苏浙高速交调数据20210119-20210219(1).xlsx"
    # 默认[0]，即首行作为列名，设置为[0,1]，即表示将前两行作为多重索引
    data = pd.read_excel(path, header=[0])

    deviceID = 71270320100006
    direction = 1
    data = data.loc[(data['deviceID'] == deviceID) & (data['direction'] == direction)]  # 指定检测器编号与车流方向


