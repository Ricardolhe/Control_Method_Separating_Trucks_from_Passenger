#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# createtime: 2021/12/21


import numpy as np
import pandas as pd


class DataUlit(object):
    """
    微波检测器数据处理的类
    """

    def __init__(self, path, deviceID, direction):
        # 默认[0]，即首行作为列名，设置为[0,1]，即表示将前两行作为多重索引
        data = pd.read_excel(path, header=[0])
        self.data = data.loc[(data['deviceID'] == deviceID) & (data['direction'] == direction)]  # 指定检测器编号与车流方向

    def get_period_data(self):
        """
        按照时间间隔求解该时间间隔平均空间平均速度
        """
        df_time = self.data["statTime"].drop_duplicates()  # 去重
        arr_speed = np.zeros(df_time.size)
        for t in df_time:
            df_t_data = self.data.loc[self.data["statTime"] == t, "vehicleFlux":]



if __name__ == "__main__":
    path = "data/副本沪苏浙高速交调数据20210119-20210219(1).xlsx"
    deviceID = 71270320100006
    direction = 1
    weibo = DataUlit(path, deviceID, direction)
    weibo.get_period_data()
