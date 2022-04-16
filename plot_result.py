
#### 扩样系数与指标图
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])

numline = 3
########
data_mpc = dftool.df_load_excel("mpc.xlsx")
data_feedback = dftool.df_load_excel("feedback.xlsx")
data_static = []
for i in range(numline):
    data_static.append(dftool.df_load_excel("static_" + str(i) + ".xlsx"))
x = range(len(data_mpc))
fig,ax = plt.subplots(4, 3, figsize=(40,40))
labels = ["TTC","flow","speed","timeloss"]
labelc = ["all","p","t"]
list_label=["mpc","SSP","TSP","TSS","feedback"]

# list_label=["mpc","SSPP","TSPP","TTSP","TTSS","feedback"]
# list_label=["mpc","SSPPP","TSPPP","TTSPP","TTTSP","TTTSS","feedback"]
for i in range(4):
    ax[i, 0].set_ylabel(labels[i])
    for j in range(3):

        label = labels[i]+"_" +labelc[j]
        ax[i,j].plot(x,data_mpc[label],marker='o',markersize=3)
        for  da in data_static:
            ax[i,j].plot(x,da[label])
        ax[i,j].plot(x,data_feedback[label],linestyle='dashdot')
        ax[i,j].set_xticks(np.linspace(0, 10, 11))
        ax[i,j].set_xticklabels(np.linspace(10, 20, 11)/10)

ax[3, 0].set_xlabel("All classes")
ax[3, 1].set_xlabel("Passenger class")
ax[3, 2].set_xlabel("Truck class")
ax[0, 0].legend(list_label)
ax[0, 1].legend(list_label)
ax[0, 2].legend(list_label)

fig.align_labels()


plt.subplot_tool()
plt.show()