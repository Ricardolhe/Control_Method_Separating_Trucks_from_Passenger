import numpy as np
import tools.dataframe_tools as dt
import pandas as pd
import math
from scipy.optimize import minimize

class MPC(object):
    """MPC控制类"""
    def __init__(self,num_line):
        self.Vs = [120, 100, 90, 80]  # 各车型自由流速度，也是限速
        self.last_density = 0  # 最后一段路段密度
        self.num_line = num_line
        self.t_get_data = 30/3600  # 采样时间
        self.num_seg = 7
        self.L = 1
        self.belta = 0.1
        self.density_c = 2200/max(self.Vs)
        self.er = 0.013   # 误差系数
        self.types = ["passenger", "truck", "coach", "trailer"]
        self.colf = [i+"_f" for i in self.types]
        self.cols = [i+"_s" for i in self.types]

    def predict(self,arf,fa,tao,k,df_flow,df_seg_data):
        df_predict = df_seg_data.copy(deep=True)
        list_len = len(df_flow)
        col_f = list(range(1,list_len+1))
        col_s = list(range(list_len+1,list_len*2+1))
        col_d = list(range(list_len*2+1,list_len*3+1))
        for i in df_seg_data["seg"]:
            # 定义上段路密度
            if i == 0 :
                df_flow_up = df_flow.values
                df_speed_up = np.array(self.Vs)
            else:
                df_flow_up = df_seg_data.iloc[i-1,col_f].values
                df_speed_up = df_seg_data.iloc[i-1,col_s].values

            # 定义下游密度
            if i == self.num_seg-1:
                df_density_down = np.zeros(list_len)
            else:
                df_density_down = df_seg_data.iloc[i+1,col_d].values

            # 预测密度df_seg_data
            density_n = df_seg_data.iloc[i,col_d].values # 路段n的各车型密度
            flow_n = df_seg_data.iloc[i,col_f].values # 路段n的各车型流量
            df_predict.iloc[i,col_d] = density_n \
                + self.t_get_data/self.num_line/self.L * (df_flow_up - flow_n)

            # 预测速度
            speed_n = df_seg_data.iloc[i,col_s].values # 路段n的各车型速度
            values_1 = self.t_get_data/self.L * speed_n*( ((speed_n**2 + df_speed_up**2)/2)**0.5 - speed_n)

            density_total_n = sum(density_n)
            density_total_down = sum(df_density_down)
            values_2 = np.array(fa)/np.array(tao)*self.t_get_data/self.L*(density_total_down-density_total_n)/(density_total_n + np.array(k))

            ve_density_n = np.array([min((1+self.belta)*self.Vs[v] , self.Vs[v]*math.exp(-1/arf[v]*((density_total_n/self.density_c)**arf[v])))  for v in range(list_len)])
            values_3 = self.t_get_data/np.array(tao)*(ve_density_n-speed_n)
            df_predict.iloc[i,col_s] = speed_n+ values_1 - values_2 + values_3

            # 预测流量
            df_predict.iloc[i, col_f] = self.num_line * df_predict.iloc[i,col_s].values * df_predict.iloc[i,col_d].values
        df_predict[df_predict<0] =0
        return df_predict

    # @staticmethod
    # def fun_error(mpc_class,seg_data, flow_in):
    #     def v(x):
    #         l = 4
    #         arf = list(x[0:l])
    #         fa = list(x[l:l*2])
    #         tao = list(x[l*2:l * 3])
    #         k = list(x[l*3:l * l])
    #         seg_true = seg_data.loc[seg_data["n_t"] > 0]
    #         seg_predict = seg_true.copy()  # 不加copy会触发链式索引
    #         len_t = len(flow_in)
    #         for i in range(len_t - 1):
    #             df_flow = flow_in.loc[i]  # 初始段进入流量
    #             df_seg_data = seg_data.loc[seg_data["n_t"] == i, "seg":]
    #             seg_predict.loc[seg_data["n_t"] == i + 1, "seg":] = mpc_class.predict(arf, fa, tao, k, df_flow,
    #                                                                              df_seg_data).values
    #
    #         result = sum(((seg_predict[mpc_class.colf] - seg_true[mpc_class.colf]) ** 2).sum()) * mpc_class.er \
    #                  + sum(((seg_predict[mpc_class.cols] - seg_true[mpc_class.cols]) ** 2).sum())
    #         result = result / (len_t - 1) / mpc_class.num_seg
    #         print("time=1")
    #         return result
    #     return v

    def fun_c(self,xx,seg_data, flow_in):
        l = 4
        x = xx.copy()
        x = (x.reshape(1,l**2))[0].tolist()
        arf = x[0:l]
        fa = x[l:l * 2]
        tao = x[l * 2:l * 3]
        k = x[l * 3:l * l]
        seg_true = seg_data.loc[seg_data["n_t"] > 0]
        seg_predict = seg_true.copy()  # 不加copy会触发链式索引
        len_t = len(flow_in)
        for i in range(len_t - 1):
            if(i==196):
                print(1)
            df_flow = flow_in.loc[i]  # 初始段进入流量
            df_seg_data = seg_data.loc[seg_data["n_t"] == i, "seg":]
            seg_predict.loc[seg_data["n_t"] == i + 1, "seg":] = self.predict(arf, fa, tao, k, df_flow,
                                                                                  df_seg_data).values

        result = sum(((seg_predict[self.colf] - seg_true[self.colf]) ** 2).sum()) * self.er \
                 + sum(((seg_predict[self.cols] - seg_true[self.cols]) ** 2).sum())
        result = result / (len_t - 1) / self.num_seg
        return result

    def calibration(self, seg_data, flow_in):
        """
        预测模型参数校正(退火算法)
        :param seg_data: 各路段实际数据
        :param flow_in: 初始路段流量
        :return:
        """
        D = len(self.types)*4  # 变量维数
        Xs = np.array((4,)*4 + (60,)*4 + (60,)*4 + (60,)*4).reshape(D,1)  # 上限
        Xx = np.array((1,)*4 + (10,)*4 + (10,)*4 + (10,)*4).reshape(D,1)   # 下限

        # ====冷却表参数====
        L = 50  # 马可夫链长度 #在温度为t情况下的迭代次数
        K = 0.96  # 衰减参数
        S = 0.5  # 步长因子
        T = 100  # 初始温度
        # T_0 = 100
        YZ = 1e-7  # 容差
        P = 0  # Metropolis过程中总接受点
        # ====随机选点初值设定====
        PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
        PreBestX = PreX  # t-1代的全局最优X
        PreBestY = self.fun_c(PreBestX,seg_data,flow_in)

        PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
        BestX = PreX  # t时刻的全局最优X
        BestY = self.fun_c(BestX,seg_data,flow_in)

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
                NextX = PreX + (np.random.uniform(low=-S ,high=S,size=(D, 1)) * (Xs - Xx))
                # ===边界条件处理
                for ii in range(D):  # 遍历每一个维度
                    while NextX[ii] > Xs[ii] or NextX[ii] < Xx[ii]:
                        NextX[ii] = PreX[ii] + (np.random.uniform(low=-S ,high=S,size=1) * (Xs[ii] - Xx[ii]))
                NextY = self.fun_c(NextX, seg_data, flow_in)

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
        return BestX,BestY


if __name__ == "__main__":
    seg_data1 = dt.df_load_csv("data/seg_data.csv")
    flow_in1 = dt.df_load_csv("data/flow_in.csv")
    mpc = MPC(3)
    X,Y=mpc.calibration(seg_data1,flow_in1)