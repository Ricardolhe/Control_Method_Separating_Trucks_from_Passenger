#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/21

import tools.sumo_txt_tools as sttool
import numpy as np
import pandas as pd
import datetime
import time


class DataUlit(object):
    """
    微波检测器数据处理的类
    """

    def __init__(self, data=None):
        self.data = data

    def df_read_excel(self, path1):
        self.data = pd.read_excel(path1, header=[0])

    def df_read_csv(self, path1):
        self.data = pd.read_csv(path1)

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
        return DataUlit(data)

    def get_period_data(self):
        """
        按照时间间隔求解该时间间隔平均空间平均速度
        """
        data = self.data
        # 指定检测器编号与车流方向
        data["statTime"] = pd.to_datetime(data["statTime"])  # 更改时间格式
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
    def get_eachtype_data(data, type_name):
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

    def get_alltype_perioddata(self, time_from, time_end, period=5):
        """
        按照时间间隔获取4种车型的数量
        :param time_end: 结束时间，标准时间格式 "2016-05-05 20:28:54"
        :param time_from: 开始时间，标准时间格式 "2016-05-05 20:28:00"
        :param period:统计间隔，必须是5的倍数
        :return:
        """
        data = self.data
        data["statTime"] = pd.to_datetime(data["statTime"])  # 更改时间格式
        time_from = datetime.datetime.strptime(time_from, "%Y-%m-%d %H:%M:%S")
        time_to = time_from + datetime.timedelta(minutes=period)
        time_end = datetime.datetime.strptime(time_end, "%Y-%m-%d %H:%M:%S")

        type_list = ["vehicle", "smallVehicle", "mediumVehicle", "largeVehicle", "sLargeVehicle"]
        num_list = ["all_v_num", "s_v_num", "m_v_num", "l_v_num", "sl_v_num"]
        speed_list = ["all_v_mean_speed", "s_v_mean_speed", "m_v_mean_speed", "l_v_mean_speed", "sl_v_mean_speed"]
        len_type = len(type_list)
        data_period = pd.DataFrame(columns=["start_time", "end_time"] + num_list + speed_list)
        number = 0  # 下标
        while time_from < time_end:
            data_period.loc[number, "start_time"] = time_from
            data_period.loc[number, "end_time"] = time_to
            search_result = data.loc[(data["statTime"] >= time_from) & (data["statTime"] < time_to)]
            if len(search_result) == 0:
                data_period.iloc[number, 2:] = 0  # 全赋值为0
            else:
                for i in range(len_type):
                    data_period.loc[number, num_list[i]], data_period.loc[number, speed_list[i]] \
                        = self.get_eachtype_data(search_result, type_list[i])
            number += 1
            time_from = time_to
            time_to = time_from + datetime.timedelta(minutes=period)
            if time_end < time_to:
                time_to = time_end
        return data_period


class PeriodDataUlit(object):
    """
    微波检测器周期汇总数据处理的类
    """

    def __init__(self, data=None):
        self.data = data
        self.pcu =[1, 1.5, 2.0, 3.0]

    def df_read_excel(self, path1):
        data = pd.read_excel(path1, header=[0])
        data["start_time"] = pd.to_datetime(data["start_time"])
        data["end_time"] = pd.to_datetime(data["end_time"])
        self.data = data

    def df_read_csv(self, path1):
        data = pd.read_csv(path1)
        data["start_time"] = pd.to_datetime(data["start_time"])
        data["end_time"] = pd.to_datetime(data["end_time"])
        self.data = data

    def extend_all_flow(self, k, inplace=True):
        """
        对数据进行扩样
        :param k: 整体扩样系数
        :param inplace: 是否生成新类
        :return: 如果生成新类，就返回
        """
        data = self.data.copy(deep=True)
        data.loc[:, "all_v_num":"sl_v_num"] = data.loc[:, "all_v_num":"sl_v_num"] * k
        if inplace:
            return PeriodDataUlit(data)
        else:
            self.data = data

    def extend_PandT_flow(self, df_PandT, inplace=True):
        """
        根据客、货扩样系数对车辆进行扩样
        :param inplace: 是否生成新类
        :param df_PandT: 起始时间，终止时间，客车扩样系数，货车扩样系数的数据
        :return: 如果生成新类，就返回
        """
        data = self.data.copy(deep=True)
        df_PandT["start_time"] = pd.to_datetime(df_PandT["start_time"])
        df_PandT["end_time"] = pd.to_datetime(df_PandT["end_time"])
        for i in range(len(df_PandT)):
            s_time = df_PandT["start_time"][i]
            e_time = df_PandT["end_time"][i]
            p = df_PandT["P"][i]
            t = df_PandT["T"][i]
            data.loc[(data["start_time"] >= s_time) & (data["start_time"] < e_time), "s_v_num"] =\
                data.loc[(data["start_time"] >= s_time) & (data["start_time"] < e_time), "s_v_num"] * p
            data.loc[(data["start_time"] >= s_time) & (data["start_time"] < e_time), "m_v_num":"sl_v_num"] =\
                data.loc[(data["start_time"] >= s_time) & (data["start_time"] < e_time), "m_v_num":"sl_v_num"] * t
        data["all_v_num"] = data["s_v_num"] + data["m_v_num"] + data["l_v_num"] + data["sl_v_num"]
        if inplace:
            return PeriodDataUlit(data)
        else:
            self.data = data

    def get_P_to_T(self, df_PandT):
        """
        分别计算客车、货车的扩样系数
        :param df_PandT: 起始时间，终止时间，客货比（标准车）的数组
        :return: 起始时间，终止时间，客货比（标准车）的数组, 客车数，货车数，客车数（扩样后）,货车车数（扩样后），客车扩样系数，货车扩样系数的数据
        """
        df_PandT["start_time"] = pd.to_datetime(df_PandT["start_time"])
        df_PandT["end_time"] = pd.to_datetime(df_PandT["end_time"])
        data = self.data
        pcu = self.pcu
        for i in range(len(df_PandT)):
            s_time = df_PandT["start_time"][i]
            e_time = df_PandT["end_time"][i]
            df_num = data.loc[(data["start_time"] >= s_time) & (data["start_time"] < e_time),"all_v_num":"sl_v_num"].sum()
            num_p = df_num["s_v_num"]
            num_t = df_num["m_v_num"] * pcu[1] + df_num["l_v_num"] * pcu[2] + df_num["sl_v_num"] * pcu[3]
            num_all = num_p + num_t
            PtoT = df_PandT["PtoT"][i]
            df_PandT.loc[i, "num_p"] = num_p
            df_PandT.loc[i, "num_t"] = num_t
            df_PandT.loc[i, "num_p_end"] = num_all * PtoT / (1 + PtoT)
            df_PandT.loc[i, "num_t_end"] = num_all / (1 + PtoT)
            df_PandT.loc[i, "P"] = num_all * PtoT / (1 + PtoT) / num_p
            df_PandT.loc[i, "T"] = num_all / (1 + PtoT) / num_t
        return df_PandT

    def get_percent_eachtime(self):
        """
        计算每一时段各种车型占比
        :return: 各种车型占比结果
        """
        data = self.data.copy(deep=True)
        data.loc[:,"s_v_num":"sl_v_num"] = data.loc[:,"s_v_num":"sl_v_num"].div(data["all_v_num"],axis=0)
        data = data.loc[:,:"sl_v_num"]
        return data

    @staticmethod
    def change_to_sumo_flow(data, path_sumo, time_from, line=3):
        """
        用于生成sumo仿真软件的车流
        :param start_time: 开始时间，标准时间格式 "2016-05-05 20:28:00"
        :param line: 车道数
        :param path_sumo: 车流文件
        :param data: 不同时段各种车型占比结果
        :return: 生成sumo车流文件
        """
        from_seg = "contral_0"
        to_seg = "end"
        time_from = datetime.datetime.strptime(time_from, "%Y-%m-%d %H:%M:%S")
        space = "    "

        with open(path_sumo, 'w') as file_object:
            file_object.write("<routes>\n")

            for i in range(len(data)):
                typedist = "typedist" + str(i)
                flow = "flow" + str(i)
                begin = data["start_time"][i]
                end = data["end_time"][i]
                file_object.write(space + '<vTypeDistribution id="' + typedist +'">\n')
                dic_s = {
                    "id": "s-car"+str(i),
                    "color": "yellow",
                    "vClass": "passenger",
                    "maxSpeed": str(120/3.6),
                    "probability":str(data["s_v_num"][i])
                }
                file_object.write(2*space + sttool.get_vType_str(dic_s))

                dic_m = {
                    "id": "m-car"+str(i),
                    "color": "red",
                    "vClass": "coach",
                    "maxSpeed": str(100 / 3.6),
                    "probability":str(data["m_v_num"][i])
                }
                file_object.write(2*space + sttool.get_vType_str(dic_m))

                dic_l = {
                    "id": "l-car"+str(i),
                    "color": "magenta",
                    "vClass": "truck",
                    "length": "12.0",
                    "width" : "2.5",
                    "height": "4.0",
                    "maxSpeed": str(90 / 3.6),
                    "probability":str(data["l_v_num"][i])
                }
                file_object.write(2*space + sttool.get_vType_str(dic_l))

                dic_sl = {
                    "id": "sl-car"+str(i),
                    "color": "white",
                    "vClass": "trailer",
                    "maxSpeed": str(80 / 3.6),
                    "probability":str(data["sl_v_num"][i])
                }
                file_object.write(2*space + sttool.get_vType_str(dic_sl))
                file_object.write(space + '</vTypeDistribution>\n')

                dic_flow ={
                    "id": "flow" + str(i),
                    "type": typedist,
                    "from": from_seg,
                    "to": to_seg,
                    "departLane": "random",
                    "departSpeed": "max",
                    "departPos":"0",
                    "begin": str((begin - time_from).seconds),
                    "end": str((end - time_from).seconds),
                    "number": str(int(line*data["all_v_num"][i]/3))

                }
                file_object.write(space + sttool.get_flow_str(dic_flow))
            file_object.write("</routes>")


if __name__ == "__main__":
    path = "../data/副本沪苏浙高速交调数据20210119-20210219(1).csv"
    path_result = "../data/map/maptest6/road.rou.xml"
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
    df_PtoT["PtoT"] = [1, 4, 1/4, 3, 1 / 3, 1]  # 各个时段客货比关系
    df_PtoT.loc[:,["start_time", "end_time"]] = etc_data_20.loc[:,["start_time", "end_time"]]
    etc_data_20 = PeriodDataUlit(etc_data_20)
    etc_data_20.extend_all_flow(2.0, False)
    df_PtoT = etc_data_20.get_P_to_T(df_PtoT)
    etc_data_20.extend_PandT_flow(df_PtoT,False)  # 三车道交通量
    etc_data_20 = etc_data_20.get_percent_eachtime()
    PeriodDataUlit.change_to_sumo_flow(etc_data_20, path_result, start_time, 3)

