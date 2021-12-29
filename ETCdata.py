#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计(主线ETC数据提取)
# user: Ricardo
# Author: Ricardo
# create-time: 2021/12/23

import numpy as np
import pandas as pd
import datetime


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
        根据etc的json数据获取每一辆经过检测路段的车辆的空间速度
        :param path_etc_json: json文件路劲
             str_day: 数据日期
        :return: 修改实例的日期与车辆速度数据
        """
        self.day = str_day
        data_all = pd.read_json(path_etc_json)
        data_up = data_all.loc[data_all["gantryId"] ==self.up0 ].reset_index()
        data_down = data_all.loc[data_all["gantryId"] == self.down0].reset_index()
        del data_all
        data_speed = pd.DataFrame(columns=["v_plate","pass_id","v_type_up","v_type_down","in_time","out_time","speed"])
        number = 0
        for i in range(len(data_up)):
            pass_id = data_up.loc[i,"passId"]
            in_time = data_up.loc[i,"transTime"]
            car_plate = data_up.loc[i,"VEHICLEPLATE"]
            search_result = data_down.loc[(data_down["passId"] == pass_id) & (data_down["transTime"] > in_time) & (data_down["VEHICLEPLATE"] == car_plate)]

            if len(search_result)>0:
                data_speed.loc[number, "v_plate"] = car_plate
                data_speed.loc[number, "pass_id"] = pass_id
                data_speed.loc[number,"v_type_up"]=data_up.loc[i,"vehicleType"]
                data_speed.loc[number, "v_type_down"] = search_result["vehicleType"].iat[0]
                data_speed.loc[number, "in_time"] = in_time  # ms
                out_time = search_result["transTime"].iat[0]
                data_speed.loc[number, "out_time"] = out_time  # ms
                data_speed.loc[number, "speed"] = self.L*1000*3.6/(out_time-in_time)
                number += 1
            print(i)
        self.car_speed = data_speed

    def save_car_speed(self,path_save):
        """
        保存提取出来的车辆速度
        :param path_save:存储数据的文件夹路径
        :return:生成csv文件
        """
        path = path_save + "/"+self.day + ".csv"
        self.car_speed.to_csv(path, encoding="utf-8", index=False)



    @staticmethod
    def get_json_etc(path_etc, path_result):
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
        data.to_json(path_result)

    @classmethod
    def change_json_days(cls):
        """
            将xlsx都转成json格式存储，方便读取，
        """
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
            path_json = "data/沿江/" + str_date + "/03主线ETC门架数据-" + str_date + ".json"  # json文件保存路径
            cls.get_json_etc(path_data, path_json)  # 单独把这段代码拿出时请将cls改为类名


if __name__ == "__main__":
    year = 2021





