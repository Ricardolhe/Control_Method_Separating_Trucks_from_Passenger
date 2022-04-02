import numpy as np
# import matplotlib.pyplot as plt
# import matplotlib as mpl
# import matplotlib;

# matplotlib.use('TkAgg')
# mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
# mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

# =================初始化参数===============
D = 10  # 变量维数
Xs = 20  # 上限
Xx = -20  # 下限
# ====冷却表参数====
L = 200  # 马可夫链长度 #在温度为t情况下的迭代次数
K = 0.99  # 衰减参数
S = 0.01  # 步长因子
T_0 = 100
T = 100  # 初始温度
YZ = 1e-7  # 容差
P = 0  # Metropolis过程中总接受点
# ====随机选点初值设定====
PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
PreBestX = PreX  # t-1代的全局最优X
PreX = np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx
BestX = PreX  # t时刻的全局最优X


# ==============目标函数=============
def func1(x):
    return np.sum([i ** 2 for i in x])


# ====每迭代一次退火一次(降温), 直到满足迭代条件为止===
deta = np.abs(func1(BestX) - func1(PreBestX))  # 前后能量差

trace = []  # 记录
while (deta > YZ) and (T > 0.1):  # 如果能量差大于允许能量差 或者温度大于阈值
    T = K * T  # 降温
    print(T)

    # ===在当前温度T下迭代次数====
    for i in range(L):  #
        # ====在此点附近随机选下一点=====
        NextX = PreX + S * (np.random.uniform(size=(D, 1)) * (Xs - Xx) + Xx)
        # ===边界条件处理
        for ii in range(D):  # 遍历每一个维度
            while NextX[ii] > Xs or NextX[ii] < Xx:
                NextX[ii] = PreX[ii] + S * (np.random.random() * (Xs - Xx) + Xx)

        # ===是否全局最优解 ===
        if (func1(BestX) > func1(NextX)):
            # 保留上一个最优解
            PreBestX = BestX
            # 此为新的最优解
            BestX = NextX

        # ====Metropolis过程====
        if (func1(PreX) - func1(NextX) > 0):  # 后一个比前一个好
            # 接受新解
            PreX = NextX
            P = P + 1
        else:
            changer = -1 * (func1(NextX) - func1(PreX)) / T
            p1 = np.exp(changer)
            # 接受较差的解
            if p1 > np.random.random():
                PreX = NextX
                P = P + 1
        trace.append(func1(BestX))
    deta = np.abs(func1(BestX) - func1(PreBestX))  # 修改前后能量差

print('最小值点\n', BestX)
print('最小值\n', func1(BestX))
plt.plot(trace, label='迭代曲线')
plt.xlabel('迭代次数')
plt.ylabel('目标函数值')
plt.show()
