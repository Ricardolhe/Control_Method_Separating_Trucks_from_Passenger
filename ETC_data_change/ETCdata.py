#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计(主线ETC数据提取)
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/23

import numpy as np
import pandas as pd
import datetime
import time


class ETCDataUlit(object):
    """
    主线ETC数据处理的类
    """

    def __init__(self):
        self.up0 = "G005032001000810010"  # 上游桩号
        self.down0 = "G005032001000810020"  # 下游桩号
        self.L = 6500  # 龙门架之间的距离
        self.car_speed = pd.DataFrame()
        self.day = ""

        # self.data_up = data_all.loc[data_all["gantryId"] ==up0 ].reset_index()
        # self.data_down = data_all.loc[data_all["gantryId"] ==down0 ].reset_index()

    def get_car_speed(self,path_etc_json,str_day):
        """
        根据etc的csv数据获取每一辆经过检测路段的车辆的空间速度
        :param path_etc_json: json文件路劲
             str_day: 数据日期
        :return: 修改实例的日期与车辆速度数据
        """
        self.day = str_day
        data_all = pd.read_csv(path_etc_json,low_memory=False)

        data_up = data_all.loc[data_all["gantryId"] ==self.up0 ].reset_index()
        data_down = data_all.loc[data_all["gantryId"] == self.down0].reset_index()
        data_up["transTime"] = pd.to_datetime(data_up["transTime"])  # 更改格式为时间
        data_down["transTime"] = pd.to_datetime(data_down["transTime"])

        del data_all
        data_speed = pd.DataFrame(columns=["v_plate","pass_id","v_type_up","v_type_down","in_time","out_time","speed"])
        number = 0
        for i in range(len(data_up)):
            pass_id = data_up.loc[i,"passId"]
            in_time = data_up.loc[i,"transTime"]
            car_plate = data_up.loc[i,"VEHICLEPLATE"]
            search_result = data_down.loc[(data_down["passId"] == pass_id) & (data_down["transTime"]> in_time) & (data_down["VEHICLEPLATE"] == car_plate)]

            if len(search_result)>0:
                data_speed.loc[number, "v_plate"] = car_plate
                data_speed.loc[number, "pass_id"] = pass_id
                data_speed.loc[number,"v_type_up"]=data_up.loc[i,"vehicleType"]
                data_speed.loc[number, "v_type_down"] = search_result["vehicleType"].iat[0]
                data_speed.loc[number, "in_time"] = in_time  # ms
                out_time = search_result["transTime"].iat[0]
                data_speed.loc[number, "out_time"] = out_time  # ms
                data_speed.loc[number, "speed"] = self.L*3.6/((out_time-in_time).total_seconds())
                number += 1
            if i % 2000 == 0:
                print(i)
        self.car_speed = data_speed

    def get_car_period(self, path_save, period=5):
        """
        按照给定时间间隔聚合
        :param path_save: 保存数据的路径
            period：时间间隔，默认5min
        :return: 生成路径文件
        """
        data_period = pd.DataFrame(
            columns=["start_time", "end_time", "v_num", "v_mean_speed"])
        time_from = datetime.datetime.strptime(self.str_change_time(self.day), '%Y-%m-%d')
        time_to = time_from + datetime.timedelta(minutes=period)
        time_end = time_from + datetime.timedelta(days=1)
        number = 0  # 下标
        while(time_from < time_end):
            data_period.loc[number,"start_time"] = time_from
            data_period.loc[number, "end_time"] = time_to
            search_result = self.car_speed.loc[(self.car_speed["in_time"] >= time_from) & (self.car_speed["in_time"] < time_to)]
            car_number = len(search_result)
            data_period.loc[number, "v_num"] = car_number
            if(car_number >0):
                data_period.loc[number, "v_mean_speed"] = (search_result["speed"].sum())/car_number
            else:
                data_period.loc[number, "v_mean_speed"] = 0
            number += 1
            time_from = time_to
            time_to = time_from + datetime.timedelta(minutes=period)
            if(time_end < time_to):
                time_to = time_end

        data_period.to_excel(path_save, index=False)  # 保存xlsx文件

    def save_car_speed(self,path_save):
        """
        保存提取出来的车辆速度
        :param path_save:存储数据的文件夹路径
        :return:生成csv文件
        """
        self.car_speed.to_csv(path_save, encoding="utf-8", index=False)

    def save_car_speed_xlsx(self,path_save):
        """
        保存提取出来的车辆速度
        :param path_save:存储数据的文件夹路径
        :return:生成xlsx文件
        """
        self.car_speed.to_excel(path_save,index=False)

    def set_car_speed(self,car_speed):
        self.car_speed = car_speed

    def set_day(self, day):
        self.day = day

    @staticmethod
    def timestamp_to_time(timestamp):
        """
        将时间戳转成标准时间
        :param timestamp：时间戳，如1462451334000 ，ms
        :return: 标准时间格式 "2016-05-05 20:28:54"
        """
        # 转换成localtime
        time_local = time.localtime(timestamp/1000)
        # 转换成新的时间格式(2016-05-05 20:28:54)
        dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
        return dt

    @staticmethod
    def str_change_time(time_str):
        """
        日期字符串转换格式
        :param time_str: "20211019"
        :return: "2021-10-19"
        """
        dt = time_str[:4] + "-" + time_str[4:6] + "-" + time_str[6:]
        return dt

    @staticmethod
    def get_csv_etc(path_etc, path_result):
        """
        将每天的ETC数据转化成json数据，便于快速读取
        """
        flist = (pd.ExcelFile(path_etc)).sheet_names
        data = pd.DataFrame()
        for i in range(len(flist)):
            if i==0:
                data = pd.read_excel(path_etc,sheet_name=0,header=0,usecols=[0,1,2,3,5])
            else:
                d = pd.read_excel(path_etc, sheet_name=i, header=0, usecols=[0, 1, 2, 3, 5])
                d.columns = data.columns
                data = pd.concat([data, d], axis=0, ignore_index=True)
        data.to_csv(path_result,index=False)


if __name__ == "__main__":
    year = 2021
    month = 1
    day = 19
    nums = 32  # 32天
    t0 = datetime.date(year, month, day)
    etc_data = ETCDataUlit()
    for i in range(0, nums):

        str_date = str(t0 + datetime.timedelta(days=i)).replace("-", "")  # 转化为XXXXXXXX八位日期格式
        print(str_date)
        path_each_car = "data/数据/ETC/eachcar/" + str_date + ".csv"

        data_each_car = pd.read_csv(path_each_car)
        data_each_car["in_time"] = pd.to_datetime(data_each_car["in_time"])
        data_each_car["out_time"] = pd.to_datetime(data_each_car["out_time"])
        etc_data.set_day(str_date)
        etc_data.set_car_speed(data_each_car)

        path_period_cars = "data/数据/ETC/periodcar/" + str_date + ".xlsx"
        etc_data.get_car_period(path_period_cars)
        # # 保存为xlsx格式的数据
        # path_each_car_xlsx = "data/数据/ETC/eachcarExcel/" + str_date + ".xlsx"
        # etc_data.save_car_speed_xlsx(path_each_car_xlsx)











