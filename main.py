#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计—SUMO的traci接口连接
# user: Ricardo
# Author: Ricardo
# create time: 2022/2/14
import math
import pandas as pd
import traci
import os, sys
import numpy as np
import tools.dataframe_tools as dt
import json

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
        T = ["truck", "coach", "trailer"]
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
        self.types = ["passenger", "truck", "coach", "trailer"]
        self.w = [1.0, 1.5, 2.0, 3.0]
        self.segs = []
        for i in range(n):
            seg_name = self.name + "_" + str(i)
            self.segs.append(Seg(seg_name))


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
        self.back = 1  # 驾驶员反应时间
        self.control_step_i = {}  # 路段需要变更属性的seg与对应的step
        self.control_step_plan = {}  # 路段需要变更属性的step与对应的计划
        self.E1Detectors = []
        self.set_E1Detectors()

    def set_E1Detectors(self):
        for i in range(self.n + 1):
            e1Detectors = []
            for j in range(self.num_line):
                e1Detector_name = "e1Detector_" + self.name + "_" + str(i) + "_" + str(j)
                e1Detectors.append(E1Detector(e1Detector_name))
            self.E1Detectors.append(e1Detectors)

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
        speed = seg.get_seg_ave_speed()  # 获得清尾seg的平均速度 m/s
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
            speed.append(df_vtype["speed"].mean() * 3.6)  # 转为km/h
            density.append(len(df_vtype) * self.w[i] / self.num_line / (self.L / 1000))  # pcu/km/line
        return speed, density

    def get_allseg_flow(self):
        """
        得到某一采样时刻各个seg的流(没有转化为)
        :return:
        """

        seg_data = pd.DataFrame(columns=self.types)
        for i in range(self.n):
            flow = self.get_E1Detectors_flow(i + 1)
            # speed, density = self.get_seg_speed_density(i)
            seg_data.loc[i, :] = flow
        return seg_data

    def get_allseg_speed_density(self):
        """
        得到某一采样时刻各个seg的密度 pcu/ln/km 速度 km/h
        :return:
        """

        seg_speed = pd.DataFrame(columns=self.types)
        seg_density = pd.DataFrame(columns=self.types)
        for i in range(self.n):
            seg_speed.loc[i, :], seg_density.loc[i, :] = self.get_seg_speed_density(i)

        return seg_speed, seg_density


class PlanPT(object):
    """客货方案类,结合客货方案相关操作"""

    def __init__(self, num_line):
        plan_dic = {
            3: [["S", "S", "P"],
                ["T", "S", "P"],
                ["T", "S", "S"]],
            4: [["S", "S", "P", "P"],
                ["T", "S", "P", "P"],
                ["T", "T", "S", "P"],
                ["T", "T", "S", "S"]],
            5: [["S", "S", "P", "P", "P"],
                ["T", "S", "P", "P", "P"],
                ["T", "T", "S", "P", "P"],
                ["T", "T", "T", "S", "P"],
                ["T", "T", "T", "S", "S"]]
        }
        self.plans = plan_dic[num_line]
        self.a = 0.15
        self.b = 4
        self.C = 2200
        self.K0 = 1.1
        self.L = 5
        self.y = 0.8
        self.w = [1.0, 1.5, 2.0, 3.0]
        self.n = 1
        self.Vs = [120, 100, 90, 80]

    @staticmethod
    def get_lane_pt(plan):
        lane_P = 0
        lane_T = 0
        w_S = 0.5
        for i in plan:
            if i == "T":
                lane_T += 1
            elif i == "P":
                lane_P += 1
            else:
                lane_T += (1 - w_S)
                lane_P += w_S
        return lane_P, lane_T

    def get_pcu_flow(self, flow_list, n=1.0):
        """
        普通交通量转化为pcu交通量
        :param n: 倍数
        :param flow_list: 四个车型的交通量
        :return:
        """
        for i in range(len(flow_list)):
            flow_list[i] = n * self.w[i] * flow_list[i]
        return flow_list

    def BRP(self, flow_list, plan):
        """
        计算阻抗函数
        :param plan: 客货方案
        :param flow_list: 四个车型的标准交通量（提前换算为小时）
        :return: 平均阻抗
        """
        t_list = []
        for i in range(len(flow_list)):
            t_list.append(flow_list[i] * self.K0 * self.L / self.y / self.n / self.Vs[i])

        l_m, l_n = self.get_lane_pt(plan)
        result = t_list[0] * (1 + self.a * (flow_list[0] / l_m / self.C) ** self.b) + \
                 sum(t_list[1:]) * (1 + self.a * (sum(flow_list[1:]) / l_n / self.C) ** self.b)
        return result / sum(flow_list)

    def pick_best_plan_feedback(self, flow_list):
        """
        选择最好的方案
        :param flow_list: 四个车型的标准交通量（提前换算为小时）
        :return: 最好方案
        """
        best_plan = []
        best_brp = np.inf
        for plan in self.plans:
            now_brp = self.BRP(flow_list.copy(), plan)
            if now_brp < best_brp:
                best_brp = now_brp
                best_plan = plan
        return best_plan


class Controls(object):
    """
    不同控制方法的类
    """

    def __init__(self, num_line):
        self.sumoCmd = ["sumo", "-c", "data/map/maptest6/road.sumocfg"]
        self.T = 9000
        self.num_line = num_line
        self.delt_t = 600  # 控制周期
        self.t_get_data = 30  # 采样时间
        self.num_seg = 7
        self.control_road = ControlRoad("contral", self.num_seg, 1000, num_line)
        self.plan_pt = PlanPT(num_line)
        self.min_flow = 1210 * self.num_line  # pcu/h/line

    def controls_calibration(self, first_plan=""):
        """
        用于获取监测数据，用于参数标定源数据的获取
        """
        traci.start(self.sumoCmd)
        no_t = 1500  # 只取中间5000的数据
        col1,col2,col3 =[],[],[]
        for i in self.control_road.types:
            col1.append(i+"_f")
            col2.append(i+"_s")
            col3.append(i+"_d")
        col = col1 + col2 + col3
        seg_data = pd.DataFrame(columns=["n_t", "seg"] + col)
        flow_in = pd.DataFrame(columns=self.control_road.types)
        temp_data = pd.DataFrame(columns=["n_t", "seg"] + col)
        n_t = 0

        temp_data["seg"] = list(range(self.control_road.n))
        temp_data["n_t"] = n_t

        # 设置初始方案
        if first_plan != "":
            self.control_road.change_all_seg_value(first_plan)
        for step in range(no_t):  # 1500s预热
            traci.simulationStep()

        temp_data[col2], temp_data[col3] = self.control_road.get_allseg_speed_density()

        for step in range(1,self.T - 2*no_t+1):
            traci.simulationStep()

            # 所有E1检测器更新数据
            self.control_road.update_all_E1Detectors_vehID()

            if step % self.t_get_data == 0:
                temp_data[col1] = self.control_road.get_allseg_flow()
                flow_in.loc[n_t,:] = self.control_road.get_E1Detectors_flow(0)
                seg_data = pd.concat([seg_data,temp_data])
                n_t += 1
                temp_data["n_t"] = n_t
                temp_data[ col2], temp_data[col3] = self.control_road.get_allseg_speed_density()

        for step in range(no_t):  # 1500s收尾
            traci.simulationStep()

        traci.close()
        flow_in = flow_in*3600/self.t_get_data
        seg_data[col1] = seg_data[col1]*3600/self.t_get_data  # 转为小时交通量
        for i in range(len(self.control_road.types)):
            seg_data.loc[seg_data[col2[i]].isna(), col2[i]] = self.plan_pt.Vs[i]
        return  seg_data,flow_in

        # 用于校正流密速图，但sumo自身发车一个车道最多3600，所以不用了
        # seg_data = pd.DataFrame(columns=["density","flow"])
        # seg_data["flow"] = seg_flow.sum(axis=1)*3600/self.t_get_data/self.num_line
        # seg_data["density"] = seg_density.sum(axis=1)
        # del seg_flow,seg_speed,seg_density
        # seg_data = seg_data.loc[(seg_data["flow"]>0) & (seg_data["density"]>0)]
        # return seg_data
        # seg_data.plot.scatter(x='density', y='flow')
        # plt.scatter(seg_data["density"], seg_data["flow"],s=1)
        # plt.show()

    def static_controls(self, first_plan=None):
        """
        静态客货分道,当不输入参数时，为无控制
        """
        traci.start(self.sumoCmd)
        step = 0
        # 设置初始方案
        if first_plan is not None:
            self.control_road.change_all_seg_value(first_plan)
        while step < self.T:
            traci.simulationStep()
            step += 1
        traci.close()

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
        traci.close()

    def feedback_controls(self, now_plan):
        """
        反馈式客货分道
        :param now_plan: 当前方案
        """
        traci.start(self.sumoCmd)
        step = 0
        self.control_road.change_all_seg_value(now_plan)
        # 加载客货分道定时方案
        index = 0
        while step < self.T:
            traci.simulationStep()
            step += 1

            # 指定E1检测器更新数据
            self.control_road.update_E1Detectors_vehID(index)

            # 判断是否需要切换方案
            if step % self.delt_t == 0:
                v_flow = self.control_road.get_E1Detectors_flow(index)
                v_flow = [flow * 3600 / self.delt_t for flow in v_flow]  # 转化为小时交通量
                # 判断是否达到流量阈值
                if sum(v_flow) > self.min_flow:
                    plan = self.plan_pt.pick_best_plan_feedback(v_flow)
                    if plan != now_plan:
                        self.control_road.add_change_i_seg(step, 0, plan)  # 添加切换计划
                        self.control_road.change_road_value(step)  # 分段切换
                        now_plan = plan

            # 判断是否有哪段seg需要切换（适用于分段切换的策略）
            if step in self.control_road.control_step_i.keys():
                self.control_road.change_road_value(step)
        traci.close()



if __name__ == "__main__":
    control = Controls(3)

    # seg_data,flow_in = control.controls_calibration()
    # dt.df_save_csv(seg_data,"data/seg_data.csv")
    # dt.df_save_csv(flow_in,"data/flow_in.csv")
    # seg_data = dt.df_load_csv("data/seg_data.csv")
    # flow_in = dt.df_load_csv("data/flow_in.csv")

    # control.feedback_controls(["T", "S", "P"])
    # control.static_controls()
    # control.time_controls(["T", "S", "P"],{3000:["T", "S", "S"],6000:["S", "S", "P"]})
    # plan_pt = PlanPT(5)
    # v = [2000,800,800,500]
    # result = plan_pt.pick_best_plan_feedback(v)
    # print(1)
