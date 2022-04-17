# 画各路段瞬时速度、密度的热力图

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])



numline = 4

path_result = "data/result/"+str(numline)+"_17/"

path_mpc = path_result + "mpc" + "_time.csv"
path_feedback = path_result + "feedback" + "_time.csv"


data_mpc = dftool.df_load_csv(path_mpc)
data_feedback = dftool.df_load_csv(path_feedback)

list_static = []
for i in range(numline):
    list_static.append(dftool.df_load_csv(path_result + "static_time" + str(i) + ".csv"))

### 数据处理
data_list =[[data_mpc,data_feedback],list_static[0:2],list_static[2:]]

list_label=[["Mpc","Feedback"],["SSPP","TSPP"],["TTSP","TTSS"]]
list_letter = [["a","b"],["c","d"],["e","f"]]
list_name = ["predict","transition","control"]
list_n = [4,1,4]
label_index = ["speed","density"][1]  # 指标选择
label_type= ["all","p","t"][0]   # 类型选择
col =[]
col_label_y = []
for i in range(len(list_name)):
    # 获取col
    for j in range(list_n[i]):
        col.append(list_name[i]+"_" + label_index +"_" +label_type +"_" +str(j))
        col_label_y.append(list_name[i]+"_" + str(j))

fig,ax = plt.subplots(3, 2, figsize=(40,15))

for i in range(3):
    for j in range(2):
        ### 画图
        data_plot = data_list[i][j].loc[:,col]

        ### 热力图
        data_plot=data_plot.astype('float').values.T
        # tem_ax = ax[i,j].imshow(data_plot,vmin=0, vmax=110,cmap="YlGnBu_r")
        tem_ax = ax[i, j].imshow(data_plot, vmin=0,vmax=120,cmap="YlGnBu") # 密度的
        ax[i,j].set_yticks(np.arange(0,9,1),col_label_y)
        ax[i,j].set_xticks(np.arange(0,28,2),np.arange(900,9300,600))

        ax[i,j].set_title("("+list_letter[i][j]+")"+list_label[i][j],y=-0.25)
        fig.colorbar(tem_ax,ax =ax[i,j],shrink=0.75)


# ax[3, 0].set_xlabel("All classes")
# ax[3, 1].set_xlabel("Passenger class")
# ax[3, 2].set_xlabel("Truck class")
fig.align_labels()


plt.subplot_tool()
plt.show()