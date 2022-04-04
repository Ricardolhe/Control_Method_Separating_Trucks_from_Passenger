import numpy as np


class PlanPT(object):
    """客货方案类,结合客货方案相关操作"""

    def __init__(self, Road):
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
        self.plans = plan_dic[Road.num_line]
        self.a = 0.15
        self.b = 4
        self.C = 2200
        self.K0 = 1.1
        self.L = 5
        self.y = 0.8
        self.w = Road.w
        self.n = 1
        self.Vs = Road.Vs

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
        # return result / sum(flow_list)
        return result

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