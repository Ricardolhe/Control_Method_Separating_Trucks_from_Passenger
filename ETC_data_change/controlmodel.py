import numpy as np
import pandas as pd
import math
from main import PredictRoad


class MPC(object):
    """MPC控制类"""

    def __init__(self, Road):
        self.col_d_out = Road.col_density_out
        self.col_f_in = Road.col_flow_in
        self.col_list_f = Road.col_list_flow
        self.col_list_s = Road.col_list_speed
        self.col_list_d = Road.col_list_density
        self.Vs = Road.Vs  # 各车型自由流速度，也是限速
        self.num_line = Road.num_line
        self.t_get_data = 30 / 3600  # 采样时间
        self.num_seg = Road.n
        self.L = Road.L / 1000  # km
        self.belta = 0.1
        self.density_c = 2200 / max(self.Vs)
        self.er = 0.013  # 误差系数
        self.types = Road.types
        self.col_seg_f = Road.col_seg_flow
        self.col_seg_s = Road.col_seg_speed

    def predict(self, arf, fa, tao, k, df_seg_data):
        df_predict = df_seg_data.copy(deep=True)
        l_types = len(self.types)
        l_t = len(df_seg_data)
        arf = np.array(arf)
        fa = np.array(fa)
        tao = np.array(tao)
        k = np.array(k)
        speed_in = np.tile(np.array(self.Vs), (l_t, 1))
        for i in range(self.num_seg):
            # 定义上段路密度与速度
            if i == 0:
                df_flow_up = df_seg_data[self.col_f_in].values
                df_speed_up = speed_in
            else:
                df_flow_up = df_seg_data[self.col_list_f[i - 1]].values
                df_speed_up = df_seg_data[self.col_list_s[i - 1]].values

            # 定义下游密度
            if i == self.num_seg - 1:
                df_density_down = df_seg_data[self.col_d_out].values
            else:
                df_density_down = df_seg_data[self.col_list_d[i + 1]].values

            # 预测密度df_seg_data
            density_n = df_seg_data[self.col_list_d[i]].values  # 路段n的各车型密度
            flow_n = df_seg_data[self.col_list_f[i]].values  # 路段n的各车型流量
            df_predict[self.col_list_d[i]] = density_n \
                                             + self.t_get_data / self.num_line / self.L * (df_flow_up - flow_n)

            # 预测速度
            speed_n = df_seg_data[self.col_list_s[i]].values  # 路段n的各车型速度
            values_1 = self.t_get_data / self.L * speed_n * (((speed_n ** 2 + df_speed_up ** 2) / 2) ** 0.5 - speed_n)

            density_total_n = np.tile(density_n.sum(axis=1), (l_types, 1)).T
            density_total_down = np.tile(df_density_down.sum(axis=1), (l_types, 1)).T
            values_2 = fa / tao * self.t_get_data / self.L * (density_total_down - density_total_n) / (
                    density_total_n + k)
            ve_density_n_1 = (1 + self.belta) * speed_in  # speed_in为限速
            ve_density_n_2 = np.array(self.Vs) * math.e ** (-1 / arf * ((density_total_n / self.density_c) ** arf))
            ve_density_n = np.minimum(ve_density_n_1, ve_density_n_2)
            values_3 = self.t_get_data / tao * (ve_density_n - speed_n)
            df_predict[self.col_list_s[i]] = speed_n + values_1 - values_2 + values_3

            # 预测流量
            df_predict[self.col_list_f[i]] = self.num_line * df_predict[self.col_list_d[i]].values \
                                          * df_predict[self.col_list_s[i]].values
        df_predict[df_predict < 0] = 0
        return df_predict

    def fun_c(self, xx, seg_data):
        l = 4
        x = xx.copy()
        x = (x.reshape(1, l ** 2))[0].tolist()
        arf = x[0:l]
        fa = x[l:l * 2]
        tao = x[l * 2:l * 3]
        k = x[l * 3:l * l]
        seg_predict = self.predict(arf, fa, tao, k, seg_data.copy())

        seg_true = seg_data.loc[1:].copy().reset_index(drop=True)
        result = sum(((seg_predict[self.col_seg_f] - seg_true[self.col_seg_f]) ** 2).sum())* self.er \
                 + sum(((seg_predict[self.col_seg_s] - seg_true[self.col_seg_s]) ** 2).sum())
        result = result / (len(seg_predict) - 1) / self.num_seg
        return result

    def calibration(self, seg_data):
        """
        预测模型参数校正(退火算法)
        :param seg_data: 各路段实际数据
        :return:
        """
        D = len(self.types) * 4  # 变量维数
        Xs = np.array((4,) * 4 + (60,) * 4 + (60,) * 4 + (60,) * 4).reshape(D, 1)  # 上限
        Xx = np.array((1,) * 4 + (10,) * 4 + (10,) * 4 + (10,) * 4).reshape(D, 1)  # 下限

        # ====冷却表参数====
        L = 100  # 马可夫链长度 #在温度为t情况下的迭代次数
        K = 0.96  # 衰减参数
        S = 0.1  # 步长因子
        T = 100  # 初始温度
        # T_0 = 100
        YZ = 1e-7  # 容差
        P = 0  # Metropolis过程中总接受点
        # ====随机选点初值设定====
        PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
        PreBestX = PreX  # t-1代的全局最优X
        PreBestY = self.fun_c(PreBestX, seg_data)

        PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
        BestX = PreX  # t时刻的全局最优X
        BestY = self.fun_c(BestX, seg_data)

        # ====每迭代一次退火一次(降温), 直到满足迭代条件为止===
        deta = np.abs(BestY - PreBestY)  # 前后能量差
        PreY = BestY

        trace = []  # 记录
        while (deta > YZ) and (T > 0.1):  # 如果能量差大于允许能量差 或者温度大于阈值
            T = K * T  # 降温
            print(T)

            # ===在当前温度T下迭代次数====
            for i in range(L):  #
                # ====在此点附近随机选下一点=====
                NextX = PreX + (np.random.uniform(low=-S, high=S, size=(D, 1)) * (Xs - Xx))
                # ===边界条件处理
                for ii in range(D):  # 遍历每一个维度
                    while NextX[ii] > Xs[ii] or NextX[ii] < Xx[ii]:
                        NextX[ii] = PreX[ii] + (np.random.uniform(low=-S, high=S, size=1) * (Xs[ii] - Xx[ii]))
                NextY = self.fun_c(NextX, seg_data)

                # ===是否全局最优解 ===
                if BestY > NextY:
                    # 保留上一个最优解与函数值
                    PreBestX = BestX
                    PreBestY = BestY
                    # 此为新的最优解与函数值
                    BestX = NextX
                    BestY = NextY

                # ====Metropolis过程====
                if PreY - NextY > 0:  # 后一个比前一个好
                    # 接受新解
                    PreX = NextX
                    PreY = NextY
                    P = P + 1
                else:
                    changer = -1 * (NextY - PreY) / T
                    p1 = np.exp(changer)
                    # 接受较差的解
                    if p1 > np.random.random():
                        PreX = NextX
                        PreY = NextY
                        P = P + 1
                trace.append(BestY)
            deta = np.abs(BestY - PreBestY)  # 修改前后能量差
        return BestX, BestY