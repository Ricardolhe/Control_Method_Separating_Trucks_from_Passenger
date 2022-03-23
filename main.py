#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计—SUMO的traci接口连接
# user: Ricardo
# Author: Ricardo
# createtime: 2022/2/14


import traci
import os, sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("please declare environment variable 'SUMO_HOME'")


class Controls(object):
    """
    不同控制方法的类
    """
    def __init__(self,):
        self.sumoCmd = ["sumo-gui", "-c", "data/map/maptest6/road.sumocfg"]
        self.T = 3600
        self.delt_t = 600  # 控制周期

    def no_controls(self):
        """
        客货不分道控制方法
        """
        traci.start(self.sumoCmd)
        step = 0
        while step < self.T:
            traci.simulationStep()
            step += 1
        traci.close()

    def static_controls(self):
        """
        静态客货分道
        """
        traci.start(self.sumoCmd)
        step = 0
        traci.lane.setAllowed("E1_0", ["truck"])
        traci.lane.setAllowed("E1_1", ["passenger"])
        traci.lane.setAllowed("E1_2", ["passenger"])
        while step < self.T:
            traci.simulationStep()
            step += 1
            # if step == 200:
            #     traci.lane.setAllowed("E1_1", ["truck"])
        traci.close()

    def feedback_controls(self):
        """
        反馈式动态客货分道
        """
        traci.start(self.sumoCmd)
        step = 0
        edge_name = "E1"
        vehicles_begin = traci.edge.getLastStepVehicleIDs(edge_name)  # 初始车辆列表
        # traci.lane.setAllowed("E1_0", ["truck"])
        # traci.lane.setAllowed("E1_1", ["passenger"])
        # traci.lane.setAllowed("E1_2", ["passenger"])

        while step < self.T:
            traci.simulationStep()
            step += 1

            # if step == 200:
            #     traci.lane.setAllowed("E1_1", ["truck"])
        traci.close()


if __name__ == "__main__":
    control = Controls()
    control.static_controls()
