#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/21

import numpy as np
import pandas as pd
import datetime
import time
from tools.time_tools import TimeTool
from tools.dataframe_tools import DaTaFrameTool


class DataUlit(object):
    """
    微波检测器数据处理的类
    """

    def __init__(self, path1, type="csv"):
        # 默认[0]，即首行作为列名，设置为[0,1]，即表示将前两行作为多重索引
        if type == "xlxs":
            self.data = pd.read_excel(path1, header=[0])
        elif type == "csv":
            self.data = pd.read_csv(path1)
        # self.deviceID = 71270320100006
        # self.direction = 0

    def select_data(self, deviceID1=-1, direction1=-1, date1=""):
        """
        筛选数据
        :param deviceID1: 检测器编号
        :param direction1: 方向
        :param date1: 日期，格式类似"2021-10-19"
        :return: none
        """
        data = self.data.copy(deep=True)
        if deviceID1 != -1:
            data = data.loc[data['deviceID'] == deviceID1].reset_index(drop=True)
        if direction1 != -1:
            data = data.loc[data['direction'] == direction1].reset_index(drop=True)
        if date1 != "":
            data = data.loc[data['statTime'].str.contains(date1)].reset_index(drop=True)
        return data

    @staticmethod
    def get_period_data(data):
        """
        按照时间间隔求解该时间间隔平均空间平均速度
        """
        # 指定检测器编号与车流方向
        df_time = data["statTime"].drop_duplicates()  # 去重
        df_nums_speed = pd.DataFrame(index=df_time, columns=["nums", "s_speed"], data=np.zeros((df_time.size, 2)))
        # 存储每5min车辆数与近似空间平均速度
        for t in df_time:
            df_t_data = data.loc[data["statTime"] == t, "vehicleFlux":]
            v_sum = df_t_data["vehicleFlux"].sum()  # 车辆数
            df_nums_speed.loc[t, "nums"] = v_sum
            time_speed = (df_t_data["vehicleFlux"] * df_t_data["speed"]).sum() / v_sum  # 时间平均车速，pandas两列相乘
            std_time_speed = (((df_t_data['smallVehicleSpeed'] - time_speed) ** 2 * df_t_data[
                'smallVehicleFlux']).sum() +
                              ((df_t_data['mediumVehicleSpeed'] - time_speed) ** 2 * df_t_data[
                                  'mediumVehicleFlux']).sum() +
                              ((df_t_data['largeVehicleSpeed'] - time_speed) ** 2 * df_t_data[
                                  'largeVehicleFlux']).sum() +
                              ((df_t_data['sLargeVehicleSpeed'] - time_speed) ** 2 * df_t_data[
                                  'sLargeVehicleFlux']).sum()) / v_sum
            space_speed = time_speed - std_time_speed / time_speed
            df_nums_speed.loc[t, "s_speed"] = space_speed
            print(t)
        return df_nums_speed

    @staticmethod
    def get_eachtype_data(data,type_name):
        """
        获取指定类型车辆的车辆数、平均速度
        :param data: 原始数据
        :param type_name:类型名称，
               vehicle，smallVehicle，mediumVehicle，largeVehicle，sLargeVehicle
        :return: 车辆数、平均速度
        """
        flux_name = type_name + "Flux"
        if type_name == "vehicle":
            speed_name = "speed"
        else:
            speed_name = type_name + "Speed"

        # 统计车辆总数
        v_sum = data[flux_name].sum()

        # 统计车辆平均速度
        if v_sum == 0:
            v_speed = 0
        else:
            v_speed = (data[flux_name] * data[speed_name]).sum() / v_sum

        return v_sum, v_speed

    @staticmethod
    def get_alltype_perioddata(data, time_from, time_end, period=5):
        """
        按照时间间隔获取4种车型的数量
        :param time_end: 结束时间，标准时间格式 "2016-05-05 20:28:54"
        :param time_from: 开始时间，标准时间格式 "2016-05-05 20:28:00"
        :param period:统计间隔，必须是5的倍数start_time
        :param data:原始数据
        :return:
        """

        data["statTime"] = pd.to_datetime(data["statTime"])  # 更改时间格式
        time_from = datetime.datetime.strptime(time_from, "%Y-%m-%d %H:%M:%S")
        time_to = time_from + datetime.timedelta(minutes=period)
        time_end = datetime.datetime.strptime(time_end, "%Y-%m-%d %H:%M:%S")

        type_list = ["vehicle", "smallVehicle", "mediumVehicle", "largeVehicle", "sLargeVehicle"]
        num_list = ["all_v_num","s_v_num","m_v_num", "l_v_num", "sl_v_num"]
        speed_list = ["all_v_mean_speed","s_v_mean_speed","m_v_mean_speed","l_v_mean_speed","sl_v_mean_speed"]
        len_type = len(type_list)
        data_period = pd.DataFrame(columns=["start_time", "end_time"] + num_list + speed_list)
        number = 0  # 下标
        while time_from < time_end:
            data_period.loc[number,"start_time"] = time_from
            data_period.loc[number, "end_time"] = time_to
            search_result = data.loc[(data["statTime"] >= time_from) & (data["statTime"] < time_to)]
            if len(search_result) == 0:
                data_period.iloc[number,2:]=0  # 全赋值为0
            else:
                for i in range(len_type):
                    data_period.loc[number, num_list[i]],data_period.loc[number, speed_list[i]] \
                        = DataUlit.get_eachtype_data(search_result,type_list[i])
            number += 1
            time_from = time_to
            time_to = time_from + datetime.timedelta(minutes=period)
            if(time_end < time_to):
                time_to = time_end
        return data_period




if __name__ == "__main__":
    path = "../data/副本沪苏浙高速交调数据20210119-20210219(1).csv"
    # path_result = "../data/weibo_result.xlsx"
    path_result = "../data/weibo_period5.xlsx"
    deviceID = 71270320100006
    direction = 0
    date = "2021-01-20"
    start_time = "2021-01-20 00:00:00"
    end_time = "2021-01-21 00:00:00"

    weibo = DataUlit(path, "csv")
    etc_data = weibo.select_data(deviceID, direction, date)  # 筛选合适的数据
    period5_data = weibo.get_alltype_perioddata(etc_data, start_time, end_time, 5)
    DaTaFrameTool.df_save_excel(period5_data,path_result)


    # weibo.get_period_data(deviceID, direction) # 获取
