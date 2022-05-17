#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计—控制结构
# user: Ricardo
# Author: Ricardo
# create time: 2022/4/3
import copy
import math
import pandas as pd
import traci
import os, sys
import numpy as np
import tools.dataframe_tools as dt
from ETC_data_change.controlmodel import MPC
from ETC_data_change.pantdesgin import PlanPT

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


class Seg(object):
    """
    sumo的seg，包含seg的各类操作
    """

    def __init__(self, name):
        self.name = name
        P = ["passenger"]
        T = ["coach", "truck", "trailer"]
        S = P + T
        self.dic = {
            "P": P,
            "S": S,
            "T": T
        }

    def change_seg_value(self, plan):
        """
        更改seg客货方案
        :param plan: 客货分道方案，由最外道到最内道的列表[“T”,”S“,”P“]
        P代表客车专用道，S代表客货共用车道，T代表货车专用道
        :return:
        """
        for i in range(len(plan)):
            lane_name = self.name + "_" + str(i)
            traci.lane.setAllowed(lane_name, self.dic[plan[i]])

    def get_seg_ave_speed(self):
        return traci.edge.getLastStepMeanSpeed(self.name)


class E1Detector(object):
    """
    E1检测器类
    """

    def __init__(self, name):
        self.name = name
        self.pass_Vehicles = set()
        self.pass_Vehicles_types = []

    def addPassedVehicleIDs(self):
        # 记录路过的车辆
        new_vehicles = set(traci.inductionloop.getLastStepVehicleIDs(self.name))
        copy_pass_Vehicles = self.pass_Vehicles & new_vehicles  # 重复的
        passed_Vehicles = new_vehicles - copy_pass_Vehicles  # 通过的车流
        self.pass_Vehicles = self.pass_Vehicles | new_vehicles
        self.pass_Vehicles_types = self.pass_Vehicles_types + list(map(traci.vehicle.getVehicleClass, passed_Vehicles))

    def clearPassedVehicles(self):
        self.pass_Vehicles = set()
        self.pass_Vehicles_types = []


class Road(object):
    """
    路段类
    """

    def __init__(self, name, n, L, num_line):
        """
        初始化
        :param name: 路段名称
        :param n: 路段seg个数
        :param L: seg长度,m
        """
        self.name = name
        self.num_line = num_line
        self.n = n
        self.L = L
        self.types = ["passenger", "coach", "truck", "trailer"]
        self.w = [1.0, 1.5, 2.0, 3.0]
        self.Vs = [120, 100, 90, 80]
        self.back = 5  # 备用时间
        self.segs = []
        for i in range(n):
            seg_name = self.name + "_" + str(i)
            self.segs.append(Seg(seg_name))
        self.col_seg_flow, self.col_seg_speed, self.col_seg_density = [], [], []

        self.col_flow_in, self.col_density_out = [], []
        self.col_list_flow, self.col_list_speed, self.col_list_density = [], [], []
        # 定义要存储的列数据
        for type_i in self.types:
            self.col_flow_in.append("f_in_" + type_i)
            self.col_density_out.append("d_out_" + type_i)

        for i in range(self.n):
            self.col_list_flow.append(["f_" + str(i) + "_" + type_i for type_i in self.types])
            self.col_seg_flow = self.col_seg_flow + self.col_list_flow[-1]

            self.col_list_speed.append(["s_" + str(i) + "_" + type_i for type_i in self.types])
            self.col_seg_speed = self.col_seg_speed + self.col_list_speed[-1]

            self.col_list_density.append(["d_" + str(i) + "_" + type_i for type_i in self.types])
            self.col_seg_density = self.col_seg_density + self.col_list_density[-1]
        self.col_seg = self.col_seg_flow + self.col_seg_speed + self.col_seg_density

    def get_seg_speed_density(self, seg_i):
        """
        返回指定路段当前各类车型的车流密度(pcu)与平均速度
        :param seg_i: 路段编号
        :return: 返回
        """
        seg = self.segs[seg_i]
        vehs_id = traci.edge.getLastStepVehicleIDs(seg.name)
        df_vehs = pd.DataFrame({"class": list(map(traci.vehicle.getVehicleClass, vehs_id)),
                                "speed": list(map(traci.vehicle.getSpeed, vehs_id))})  # m/s
        speed = []
        density = []
        for i in range(len(self.types)):
            df_vtype = df_vehs.loc[df_vehs["class"] == self.types[i]]
            if len(df_vtype["speed"]) == 0:
                speed.append(self.Vs[i])
            else:
                speed.append(df_vtype["speed"].mean() * 3.6)  # 转为km/h
            density.append(len(df_vtype) * self.w[i] / self.num_line / (self.L / 1000))  # pcu/km/line
        return speed, density

    def get_allseg_speed_density(self):
        """
        得到某一采样时刻各个seg的密度 pcu/ln/km 速度 km/h
        :return:
        """
        l = len(self.types)
        seg_speed = pd.DataFrame(columns=self.col_seg_speed, index=["0"])
        seg_density = pd.DataFrame(columns=self.col_seg_density, index=["0"])
        for i in range(self.n):
            seg_speed.iloc[0, l * i:l * i + l], seg_density.iloc[0, l * i:l * i + l] = self.get_seg_speed_density(i)
        return seg_speed, seg_density

    def get_step_new(self, step, i):
        speed, density = self.get_seg_speed_density(i)
        speed = sum(np.array(speed) * np.array(density)) / sum(np.array(density))
        step_new = step + math.ceil(self.L / speed) + self.back
        return step_new


class ControlRoad(Road):
    """
    控制路段类，继承路段类
    """

    def __init__(self, name, n, L, num_line):
        """
        初始化
        :param name: 路段名称
        :param n: 路段seg个数
        :param L: seg长度
        """
        Road.__init__(self, name, n, L, num_line)
        self.control_step_i = {}  # 路段需要变更属性的seg与对应的step
        self.control_step_plan = {}  # 路段需要变更属性的step与对应的计划
        self.in_E1Detectors = []
        self.out_E1Detectors = []

        for i in range(self.num_line):
            e1Detector_name_in = "e1Detector_" + "in" + "_" + str(i)
            e1Detector_name_out = "e1Detector_" + "out" + "_" + str(i)
            self.in_E1Detectors.append(E1Detector(e1Detector_name_in))
            self.out_E1Detectors.append(E1Detector(e1Detector_name_out))

    def get_E1Detectors_vehID(self):
        """
        更新指定断面上的E1检测器的经过车辆id数据
        """
        in_veh = []
        in_veh_types = []
        out_veh = []
        out_veh_types = []
        for i in range(self.num_line):
            in_Detectors = self.in_E1Detectors[i]
            new_vehicles = list(traci.inductionloop.getLastStepVehicleIDs(in_Detectors.name))
            in_veh = in_veh + new_vehicles
            in_veh_types = in_veh_types + list(map(traci.vehicle.getVehicleClass, new_vehicles))

            out_Detectors = self.out_E1Detectors[i]
            new_vehicles = list(traci.inductionloop.getLastStepVehicleIDs(out_Detectors.name))
            try:

                out_veh_types = out_veh_types + list(map(traci.vehicle.getVehicleClass, new_vehicles))
                out_veh = out_veh + new_vehicles
            except (traci.exceptions.TraCIException):

                print("车辆已经出去了，无视")

        return in_veh, in_veh_types, out_veh, out_veh_types

    def change_seg_value(self, i, plan):
        """
        改变具体seg的客货属性
        :param i: seg编号
        :param plan: 客货计划
        :return:
        """
        self.segs[i].change_seg_value(plan)

    def change_all_seg_value(self, plan):
        for seg in self.segs:
            seg.change_seg_value(plan)

    def change_road_value(self, step):
        """
        分段更改road客货方案
        :param step: 当前时间
        :return:
        """
        i = self.control_step_i[step]
        plan = self.control_step_plan[step]
        seg = self.segs[i]
        seg.change_seg_value(plan)
        speed, density = self.get_seg_speed_density(i)
        speed = sum(np.array(speed) * np.array(density)) / sum(np.array(density))
        # speed = seg.get_seg_ave_speed()  # 获得清尾seg的平均速度 m/s
        if i + 1 < self.n:
            step_new = step + math.ceil(self.L / speed) + self.back
            self.control_step_i[step_new] = i + 1
            self.control_step_plan[step_new] = plan
        self.del_change_i_seg(step)

    def add_change_i_seg(self, step, i, plan):
        self.control_step_i[step] = i
        self.control_step_plan[step] = plan

    def del_change_i_seg(self, step):
        del self.control_step_i[step]
        del self.control_step_plan[step]


class PredictRoad(Road):
    """
    预测路段类，继承路段类
    """

    def __init__(self, name, n, L, num_line):
        """
        初始化
        :param name: 路段名称
        :param n: 路段seg个数
        :param L: seg长度
        """
        Road.__init__(self, name, n, L, num_line)
        self.E1Detectors = []
        self.set_E1Detectors()

    def set_E1Detectors(self):
        for i in range(self.n + 1):
            e1Detectors = []
            for j in range(self.num_line):
                e1Detector_name = "e1Detector_" + self.name + "_" + str(i) + "_" + str(j)
                e1Detectors.append(E1Detector(e1Detector_name))
            self.E1Detectors.append(e1Detectors)

    def update_E1Detectors_vehID(self, i):
        """
        更新指定断面上的E1检测器的经过车辆id数据
        """
        for Detector in self.E1Detectors[i]:
            Detector.addPassedVehicleIDs()

    def update_all_E1Detectors_vehID(self):
        """
        更新所有断面上的E1检测器的经过车辆id数据
        """
        for i in range(self.n + 1):
            self.update_E1Detectors_vehID(i)

    def get_E1Detectors_flow(self, i):
        """
        计算指定断面上的E1检测器的经过各类车流数(转为pcu)
        """
        pass_veh = []
        for Detector in self.E1Detectors[i]:
            pass_veh = pass_veh + Detector.pass_Vehicles_types
            Detector.clearPassedVehicles()
        pass_veh = pd.Series(pass_veh, dtype='object')
        flow = []
        for i in range(len(self.types)):
            flow.append(sum(pass_veh == self.types[i]) * (self.w[i]))
        return flow

    def get_allseg_flow(self):
        """
        得到某一采样时刻各个seg的流(没有转化为)
        :return:
        """
        l = self.n
        seg_flow = pd.DataFrame(columns=self.col_seg_flow, index=["0"])
        for i in range(self.n):
            seg_flow.iloc[0, l * i:l * i + l] = self.get_E1Detectors_flow(i + 1)  # 注意检测器安在下游，需要i+1
        return seg_flow


class Controls(object):
    """
    不同控制方法的类
    """

    def __init__(self, num_line, sumoCmd):
        self.sumoCmd = sumoCmd
        self.T = 9000
        self.num_line = num_line
        self.delt_t = 300  # 控制时长，5min
        self.t_get_data = 30  # 采样间隔
        self.no_change = 900
        self.control_road = ControlRoad("contral", 4, 1000, num_line)
        self.transition_road = Road("transition", 1, 500, num_line)
        self.predict_road = PredictRoad("predict", 4, 1000, num_line)
        self.min_flow = 1210 * self.num_line  # pcu/h/line
        self.predict_time = 480  # 预测时长，8min

        self.in_veh = []
        self.in_veh_types = []
        self.in_veh_time = []
        self.out_veh = []
        self.out_veh_types = []
        self.out_veh_time = []
        self.df_data = pd.DataFrame()

        # 瞬时各路段流量速度数据
        self.time_speed_density_c = pd.DataFrame(columns=self.control_road.col_seg_speed
                                                         + self.control_road.col_seg_density + ["step"])
        self.time_speed_density_t = pd.DataFrame(columns=self.transition_road.col_seg_speed
                                                         + self.transition_road.col_seg_density+ ["step"])
        self.time_speed_density_p = pd.DataFrame(columns=self.predict_road.col_seg_speed
                                                         + self.predict_road.col_seg_density+ ["step"])
        self.plan_list = []  # 各个周期控制方案

    def clear_data(self):
        self.in_veh = []
        self.in_veh_types = []
        self.in_veh_time = []
        self.out_veh = []
        self.out_veh_types = []
        self.out_veh_time = []
        self.df_data = pd.DataFrame()

        self.time_speed_density_c = pd.DataFrame(columns=self.control_road.col_seg_speed
                                                         + self.control_road.col_seg_density + ["step"])
        self.time_speed_density_t = pd.DataFrame(columns=self.transition_road.col_seg_speed
                                                         + self.transition_road.col_seg_density+ ["step"])
        self.time_speed_density_p = pd.DataFrame(columns=self.predict_road.col_seg_speed
                                                         + self.predict_road.col_seg_density+ ["step"])
        self.plan_list = []  # 各个周期控制方案

    def save_data(self, step):
        # 记录控住段数据
        veh_data = self.control_road.get_E1Detectors_vehID()
        self.in_veh = self.in_veh + veh_data[0]
        self.in_veh_types = self.in_veh_types + veh_data[1]
        self.in_veh_time = self.in_veh_time + [step] * len(veh_data[0])
        self.out_veh = self.out_veh + veh_data[2]
        self.out_veh_types = self.out_veh_types + veh_data[3]
        self.out_veh_time = self.out_veh_time + [step] * len(veh_data[2])

    def solve_data(self):
        # 处理控住段数据
        df_in = pd.DataFrame({
            "veh": self.in_veh,
            "vclass": self.in_veh_types,
            "time": self.in_veh_time
        })

        df_out = pd.DataFrame({
            "veh": self.out_veh,
            "vclass": self.out_veh_types,
            "time": self.out_veh_time
        })
        df_in = df_in.drop_duplicates(subset=['veh'], keep='first')
        df_in = df_in.sort_values(by=['veh']).reset_index(drop=True)

        df_out = df_out.drop_duplicates(subset=['veh'], keep='last')
        df_out = df_out.sort_values(by=['veh']).reset_index(drop=True)
        df_data = pd.merge(df_in, df_out, on='veh')
        del df_data["vclass_y"]
        for i in range(len(self.control_road.types)):
            df_data.loc[df_data["vclass_x"] == self.control_road.types[i], "pcu"] = self.control_road.w[i]
        self.df_data = df_data

    def solve_road_date(self):
        """处理瞬时数据"""
        list_data = [self.time_speed_density_p,self.time_speed_density_t,self.time_speed_density_c]
        list_name = ["predict","transition","control"]
        list_road = [self.predict_road,self.transition_road,self.control_road]
        for k in range(len(list_name)):
            list_data[k]= list_data[k].astype("float")
            list_data[k][list_data[k]==0.0] = 1.0
            for i in range(list_road[k].n):
                # 密度
                col_d_p = list_name[k]+"_density_p_"+str(i)
                col_d_t = list_name[k]+"_density_t_" + str(i)
                col_d_all = list_name[k]+"_density_all_" + str(i)
                list_data[k][col_d_p] = list_data[k][list_road[k].col_list_density[i][0]]
                list_data[k][col_d_t] = list_data[k][list_road[k].col_list_density[i][1:]].sum(axis=1)
                list_data[k][col_d_all] = list_data[k][list_road[k].col_list_density[i]].sum(axis=1)
                temp = list_data[k][[col_d_p,col_d_t,col_d_all]].copy()
                temp[temp==0.0] =1.0
                list_data[k][[col_d_p, col_d_t, col_d_all]] = temp.copy()


                col_s_p = list_name[k]+"_speed_p_"+str(i)
                col_s_t = list_name[k]+"_speed_t_" + str(i)
                col_s_all = list_name[k]+"_speed_all_" + str(i)
                list_data[k][col_s_p] = list_data[k][list_road[k].col_list_speed[i][0]]
                list_data[k][col_s_t] = (list_data[k][list_road[k].col_list_speed[i][1:]].values
                                         *list_data[k][list_road[k].col_list_density[i][1:]].values).sum(axis=1)/list_data[k][col_d_t]
                list_data[k][col_s_all] = (list_data[k][list_road[k].col_list_speed[i]].values
                                         *list_data[k][list_road[k].col_list_density[i]].values).sum(axis=1)/list_data[k][col_d_all]

        df_list =[ list_data[i].loc[:,(list_name[i]+"_density_p_"+str(0)):] for i in range(len(list_name))]
        data_result = pd.concat(df_list, axis=1)
        data_result["step"] = list_data[0]["step"]
        data_result =data_result.loc[(data_result["step"]>=900)]
        return data_result.copy()


    def look_data(self):
        """
        分析数据
        :return:
        """
        df_data = self.df_data.copy()
        df_data["travel_time"] = df_data["time_y"] - df_data["time_x"]  # 得到速度
        travel_time = sum(df_data["travel_time"] * df_data["pcu"]) / sum(df_data["pcu"])
        print(travel_time)
        return df_data

    def save_ervey_roaddata(self,step,cycle_index):
        # 预测段各段瞬时数据记录
        speed, density = self.predict_road.get_allseg_speed_density()
        self.time_speed_density_p.loc[cycle_index, self.predict_road.col_seg_speed] = speed.values
        self.time_speed_density_p.loc[cycle_index, self.predict_road.col_seg_density] = density.values
        self.time_speed_density_p.loc[cycle_index, "step"] = step

        # 过渡段各段瞬时数据记录
        speed, density = self.transition_road.get_allseg_speed_density()
        self.time_speed_density_t.loc[cycle_index, self.transition_road.col_seg_speed] = speed.values
        self.time_speed_density_t.loc[cycle_index, self.transition_road.col_seg_density] = density.values
        self.time_speed_density_t.loc[cycle_index, "step"] = step

        # 控制段各段瞬时数据记录
        speed, density = self.control_road.get_allseg_speed_density()
        self.time_speed_density_c.loc[cycle_index, self.control_road.col_seg_speed] = speed.values
        self.time_speed_density_c.loc[cycle_index, self.control_road.col_seg_density] = density.values
        self.time_speed_density_c.loc[cycle_index, "step"] = step

    def controls_calibration(self, first_plan=""):
        """
        用于获取监测数据，用于参数标定源数据的获取
        """
        l_types = len(self.predict_road.types)
        traci.start(self.sumoCmd)
        no_t = 1800  # 只取中间4200的数据
        col_flow_in = self.predict_road.col_flow_in
        col_density_out = self.predict_road.col_density_out
        col = col_flow_in + self.predict_road.col_seg + col_density_out
        seg_data = pd.DataFrame(columns=col, index=range(math.ceil((self.T - no_t * 2) / self.t_get_data)))

        n_t = 0

        # 设置初始方案
        if first_plan != "":
            self.control_road.change_all_seg_value(first_plan)
        for step in range(no_t):  # 预热
            traci.simulationStep()

        speed, density = self.predict_road.get_allseg_speed_density()
        seg_data.loc[n_t, self.predict_road.col_seg_speed] = speed.values
        seg_data.loc[n_t, self.predict_road.col_seg_density] = density.values
        seg_data.loc[n_t, col_density_out] = self.transition_road.get_seg_speed_density(0)[1]

        for step in range(1, self.T - 2 * no_t + 1):
            traci.simulationStep()

            # 所有E1检测器更新数据
            self.predict_road.update_all_E1Detectors_vehID()

            if step % self.t_get_data == 0:
                flow = self.predict_road.get_allseg_flow()
                seg_data.loc[n_t, self.predict_road.col_seg_flow] = flow.values
                seg_data.loc[n_t, col_flow_in] = self.predict_road.get_E1Detectors_flow(0)
                n_t += 1
                speed, density = self.predict_road.get_allseg_speed_density()
                seg_data.loc[n_t, self.predict_road.col_seg_speed] = speed.values
                seg_data.loc[n_t, self.predict_road.col_seg_density] = density.values
                seg_data.loc[n_t, col_density_out] = self.transition_road.get_seg_speed_density(0)[1]
        seg_data.drop(len(seg_data) - 1, inplace=True)

        for step in range(no_t):  # 1500s收尾
            traci.simulationStep()

        traci.close()

        # 转为小时交通量
        seg_data[col_flow_in + self.predict_road.col_seg_flow] \
            = seg_data[col_flow_in + self.predict_road.col_seg_flow] * 3600 / self.t_get_data
        return seg_data

    def static_controls(self, first_plan=None):
        """
        静态客货分道
        """
        traci.start(self.sumoCmd)
        step = 0
        # 设置初始方案
        cycle_index = 0
        while step < self.no_change:
            traci.simulationStep()
            step += 1
            if step % self.delt_t == 0:
                self.save_ervey_roaddata(step, cycle_index)
                cycle_index +=1
            # 更新控制段数据
            self.save_data(step)

        if first_plan is not None:
            self.control_road.change_all_seg_value(first_plan)
        while step < self.T:
            traci.simulationStep()
            step += 1
            if step % self.delt_t == 0:
                self.save_ervey_roaddata(step, cycle_index)
                cycle_index += 1

            # 更新控制段数据
            self.save_data(step)
        traci.close()
        # 处理数据
        self.solve_data()
        data_time = self.solve_road_date()
        # 分析数据
        data = self.look_data()
        self.clear_data()
        return data,data_time

    def time_controls(self, first_plan, dic_plan):
        """
        定时客货分道
        :param first_plan: 初始方案
        :param dic_plan: 计划列表{1000:["T", "S", "S"],2000:["S", "S", "P"]}
        """
        traci.start(self.sumoCmd)
        step = 0
        self.control_road.change_all_seg_value(first_plan)
        # 加载客货分道定时方案
        for k, v in dic_plan.items():
            self.control_road.add_change_i_seg(k, 0, v)
        while step < self.T:
            traci.simulationStep()
            step += 1
            # 判断是否需要更新控制路段的seg属性
            if step in self.control_road.control_step_i.keys():
                self.control_road.change_road_value(step)

            # 更新控制段数据
            self.save_data(step)
        traci.close()
        # 处理数据
        self.solve_data()
        # 分析数据
        data = self.look_data()
        self.clear_data()
        return data

    def feedback_controls(self, now_plan):
        """
        反馈式客货分道
        :param now_plan: 当前方案
        """
        traci.start(self.sumoCmd)
        step = 0
        self.control_road.change_all_seg_value(now_plan)
        plan_pt = PlanPT(self.control_road)
        # 加载客货分道定时方案
        index = -1
        cycle_index = 0
        while step < self.T:
            traci.simulationStep()
            step += 1

            # 指定E1检测器更新数据
            self.predict_road.update_E1Detectors_vehID(index)

            # 判断是否需要切换方案
            if step % self.delt_t == 0:

                self.save_ervey_roaddata(step, cycle_index)
                v_flow = self.predict_road.get_E1Detectors_flow(index)
                v_flow = [flow * 3600 / self.delt_t for flow in v_flow]  # 转化为小时交通量
                # 判断是否达到流量阈值
                if sum(v_flow) > self.min_flow and step >= self.no_change:
                    plan = plan_pt.pick_best_plan_feedback(v_flow)
                    if plan != now_plan:
                        step_new = self.transition_road.get_step_new(step, 0)
                        self.control_road.add_change_i_seg(step_new, 0, plan)  # 添加切换计划
                        now_plan = plan
                self.plan_list.append(now_plan)  # 记录当前周期方案
                cycle_index = cycle_index+1

            # 判断是否有哪段seg需要切换（适用于分段切换的策略）
            if step in self.control_road.control_step_i.keys():
                self.control_road.change_road_value(step)

            # 更新控制段数据
            self.save_data(step)
        traci.close()
        # 处理数据
        self.solve_data()
        data_time = self.solve_road_date()
        # 分析数据
        data = self.look_data()
        plan_list = copy.deepcopy(self.plan_list)  # 客货分道方案列表
        self.clear_data()
        return data,plan_list,data_time

    def mpc_controls(self, now_plan):
        """
        mpc客货分道
        :param now_plan: 当前方案
        """
        traci.start(self.sumoCmd)
        n_step = 1
        step = 0
        # 加载客货分道初始方案
        self.control_road.change_all_seg_value(now_plan)
        model = MPC(self.predict_road, self.control_road)  # 控制模型引入
        col_flow_in = self.predict_road.col_flow_in
        col_density_out = self.predict_road.col_density_out
        col = col_flow_in + self.predict_road.col_seg + col_density_out
        seg_data = pd.DataFrame(columns=col, index=[0])
        flow_in = []  # 每个采样周期记录进入初始路段流量

        while step < self.T:
            traci.simulationStep()
            step += 1

            # E1检测器更新数据，记录初始路段进入流量
            self.predict_road.update_all_E1Detectors_vehID()

            # 每个采样周期记录初始路段进入流量
            if step % self.t_get_data == 0:
                flow_temp = self.predict_road.get_E1Detectors_flow(0)
                flow_in.append([flow * 3600 / self.t_get_data for flow in flow_temp])
                flow = self.predict_road.get_allseg_flow()
                # for seg_i in range(1,self.predict_road.n+1):
                #     # 每个路段下游的E1检测器更新数据
                #     self.predict_road.update_E1Detectors_vehID(seg_i)

            # 判断是否需要切换方案
            if step % self.delt_t == 0:
                # 获取当前交通状态，密度速度
                speed, density = self.predict_road.get_allseg_speed_density()
                seg_data.loc[0, self.predict_road.col_seg_speed] = speed.values
                seg_data.loc[0, self.predict_road.col_seg_density] = density.values
                seg_data.loc[0, col_density_out] = self.transition_road.get_seg_speed_density(0)[1]

                # 记录该周期瞬时数据
                cycle_index = n_step - 1
                self.save_ervey_roaddata(step,cycle_index)

            if step == (n_step * self.delt_t + self.t_get_data):
                # 获取当前交通状态，流量，速度
                n_step += 1
                # flow = self.predict_road.get_allseg_flow()  # 获取所有seg流量
                seg_data.loc[0, self.predict_road.col_seg_flow] = flow.values
                seg_data.loc[0, col_flow_in] = flow_in[-1]
                # 转为小时交通量
                seg_data.loc[0, self.predict_road.col_seg_flow] \
                    = seg_data.loc[0, self.predict_road.col_seg_flow] * 3600 / self.t_get_data

                plan, sum_flow = model.get_plan(seg_data, np.array(flow_in), self.t_get_data, self.predict_time)
                # 判断是否达到流量阈值
                if sum_flow > self.min_flow and step > self.no_change:
                    if plan != now_plan:
                        step_new = self.transition_road.get_step_new(step, 0)
                        self.control_road.add_change_i_seg(step_new, 0, plan)  # 添加切换计划

                        now_plan = plan
                flow_in = []

                self.plan_list.append(now_plan)  # 记录当前周期方案

            # 判断是否有哪段seg需要切换（适用于分段切换的策略）
            if step in self.control_road.control_step_i.keys():
                self.control_road.change_road_value(step)
            # 更新控制段数据
            self.save_data(step)
        traci.close()
        # 处理数据
        self.solve_data()
        data_time = self.solve_road_date()
        # 分析数据
        data = self.look_data()
        plan_list = copy.deepcopy(self.plan_list)  # 客货分道方案列表
        self.clear_data()
        return data,plan_list,data_time
