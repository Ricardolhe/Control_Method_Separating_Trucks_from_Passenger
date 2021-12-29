#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/21

import numpy as np
import pandas as pd


class DataUlit(object):
    """
    微波检测器数据处理的类
    """

    def __init__(self,path1):
        # 默认[0]，即首行作为列名，设置为[0,1]，即表示将前两行作为多重索引
        self.data = pd.read_excel(path1, header=[0])

    def get_period_data(self, deviceID1, direction1, path_result1):
        """
        按照时间间隔求解该时间间隔平均空间平均速度
        """
        data = self.data.loc[(self.data['deviceID'] == deviceID1) & (self.data['direction'] == direction1)]
        # 指定检测器编号与车流方向
        df_time = data["statTime"].drop_duplicates()  # 去重
        df_nums_speed = pd.DataFrame(index=df_time, columns=["nums", "s_speed"], data=np.zeros((df_time.size, 2)))
        # 存储每5min车辆数与近似空间平均速度
        for t in df_time:
            df_t_data = data.loc[data["statTime"] == t, "vehicleFlux":]
            v_sum = df_t_data["vehicleFlux"].sum() # 车辆数
            df_nums_speed.loc[t,"nums"] = v_sum
            time_speed = (df_t_data["vehicleFlux"]*df_t_data["speed"]).sum()/v_sum  # 时间平均车速，pandas两列相乘
            std_time_speed = (((df_t_data['smallVehicleSpeed']-time_speed)**2 *df_t_data['smallVehicleFlux']).sum()+
                              ((df_t_data['mediumVehicleSpeed']-time_speed)**2 *df_t_data['mediumVehicleFlux']).sum() +
                              ((df_t_data['largeVehicleSpeed']-time_speed)**2 *df_t_data['largeVehicleFlux']).sum() +
                              ((df_t_data['sLargeVehicleSpeed'] - time_speed) ** 2 * df_t_data['sLargeVehicleFlux']).sum())/v_sum
            space_speed = time_speed - std_time_speed/time_speed
            df_nums_speed.loc[t, "s_speed"] = space_speed
            print(t)
        writer = pd.ExcelWriter(path_result1)
        df_nums_speed.to_excel(writer)
        writer.save()


if __name__ == "__main__":
    path = "data/副本沪苏浙高速交调数据20210119-20210219(1).xlsx"
    path_result = "data/weibo_result.xlsx"
    deviceID = 71270320100006
    direction = 0
    weibo = DataUlit(path)
    weibo.get_period_data(deviceID, direction, path_result)