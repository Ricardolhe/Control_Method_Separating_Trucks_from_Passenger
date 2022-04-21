# 画方案随流量变化图



import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])


def get_result(data):
    step =600
    end =7200
    d_t = 300
    data_result = pd.DataFrame(columns=["from", "to","flow_all", "flow_p", "flow_t"])
    types =["passenger", "truck", "coach", "trailer"]
    vs = [120, 100, 90, 80]  # 限速
    index = 0
    l = 8500
    index =0
    for i in range(len(types)):
        data.loc[data["vclass_x"] == types[i], "vs"] = vs[i]
    data["timeloss"] = data["travel_time"] - l / data["vs"] * 3.6
    data["speed"] = l / data["travel_time"] * 3.6
    while step + d_t <= end:
        from_t = step
        to_t = step + d_t
        data_result.loc[index,"from"] = from_t
        data_result.loc[index,"to"] = to_t
        df_p = data.loc[(data["time_x"]>=from_t) & (data["time_x"]<to_t) & (data["vclass_x"]==types[0]),:]
        df_t = data.loc[(data["time_x"]>=from_t) & (data["time_x"]<to_t) & (data["vclass_x"]!=types[0]),:]
        data_result.loc[index, "flow_p"] = sum(df_p["pcu"])


        data_result.loc[index, "flow_t"] = sum(df_t["pcu"])
        step = to_t
        index +=1
    data_result["flow_all"] = data_result["flow_p"] + data_result["flow_t"]

    return data_result.copy()


def get_result_plan(data):
    dic ={
        "T":0,
        "S":2,
        "P":1
    }
    for k,v in dic.items():
        data[data==k] = v

    col = data.columns[::-1]
    data = data[col]
    return data.copy()


numline = 4

path_result = "data/result/"+str(numline)+"_17/"

#  流量数据
path_mpc = path_result + "mpc_in" + ".csv"
path_feedback = path_result + "feedback_in" + ".csv"

data_mpc = dftool.df_load_csv(path_mpc)
data_feedback = dftool.df_load_csv(path_feedback)

#  方案数据
path_mpc_plan = path_result + "mpc_plan" + ".csv"
path_feedback_plan = path_result + "feedback_plan" + ".csv"

plan_mpc = dftool.df_load_csv(path_mpc_plan)
plan_feedback = dftool.df_load_csv(path_feedback_plan)


### 数据处理
data_mpc = get_result(data_mpc)
data_feedback = get_result(data_feedback)

plan_mpc = get_result_plan(plan_mpc).iloc[0:len(data_mpc)-1,:]
plan_feedback = get_result_plan(plan_feedback).iloc[0:len(data_feedback)-1,:]


list_label=["Mpc","Feedback"]
list_plan = [plan_mpc,plan_feedback]
list_data = [data_mpc,data_feedback]
fig,ax = plt.subplots(2, 1, figsize=(40,40))

j =1


x = list_data[j]["to"]
ax[0].plot(x,list_data[j]["flow_all"])
ax[0].plot(x, list_data[j]["flow_p"],linestyle='dashdot')
ax[0].plot(x, list_data[j]["flow_t"], linestyle='dashed')
ax[0].set_xticks(np.arange(900,7500,300),np.arange(900,7500,300),fontsize=15)

ax[0].tick_params( labelsize= 15)
ax[0].set_ylim(top=1200)
# ax[0, j].set_yticks(np.arange(0, 1300, 200))
ax[0].legend(["All classes","Passenger class","Truck class"],fontsize=15)
# ax[0, j].set_yticks(np.arange(0, 1400, 200))
ax[0].grid()  # 网格线
ax[0].set_xlim(left=900, right=7200)

data_plot = list_plan[j].astype('float').values.T
tem_ax = ax[1].imshow(data_plot,cmap="viridis_r")
ax[1].set_yticks(np.arange(0, 4, 1),["line_1","line_2","line_3","line_4"],fontsize=15)
# ax[1, j].set_xlim(left=0,right=21)
# ax[1, j].grid(color='w', linestyle='-', linewidth=2)  # 网格线
ax[1].set_xticks(np.arange(0, 21, 1), np.arange(1, 22, 1),fontsize=15)

# fig.colorbar(tem_ax, ax=ax[1, j], orientation='horizontal', shrink=0.90)


ax[0].set_ylabel("flow (pcu)",fontsize=20)
ax[1].set_ylabel("contral plan",fontsize=20)
fig.align_labels()

plt.subplot_tool()
plt.show()