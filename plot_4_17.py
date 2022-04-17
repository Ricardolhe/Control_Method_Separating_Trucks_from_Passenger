
# 画热力图

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])


def get_result(data):
    step =900
    end =7200
    d_t = 300
    data_result = pd.DataFrame(columns=["from", "to","speed_all", "timeloss_all", "traveltime_all", "flow_all",
                                        "speed_p", "timeloss_p", "traveltime_p", "flow_p",
                                        "speed_t", "timeloss_t", "traveltime_t", "flow_t", ])
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
        df_p = data.loc[(data["time_y"]>=from_t) & (data["time_y"]<to_t) & (data["vclass_x"]==types[0]),:]
        df_t = data.loc[(data["time_y"]>=from_t) & (data["time_y"]<to_t) & (data["vclass_x"]!=types[0]),:]
        data_result.loc[index, "flow_p"] = sum(df_p["pcu"])
        data_result.loc[index, "traveltime_p"] = df_p["travel_time"].mean()
        data_result.loc[index, "speed_p"] = df_p["speed"].mean()
        data_result.loc[index, "timeloss_p"] = df_p["timeloss"].mean()

        data_result.loc[index, "flow_t"] = sum(df_t["pcu"])
        data_result.loc[index, "traveltime_t"] = sum(df_t["travel_time"] * df_t["pcu"]) / data_result.loc[
            index, "flow_t"]
        data_result.loc[index, "speed_t"] = sum(df_t["speed"] * df_t["pcu"]) / data_result.loc[index, "flow_t"]
        data_result.loc[index, "timeloss_t"] = sum(df_t["timeloss"] * df_t["pcu"]) / data_result.loc[index, "flow_t"]
        step = to_t
        index +=1
    data_result["flow_all"] = data_result["flow_p"] + data_result["flow_t"]
    data_result["traveltime_all"] = (data_result["flow_p"] * data_result["traveltime_p"] + data_result["flow_t"] *
                                     data_result["traveltime_t"]) / data_result["flow_all"]
    data_result["timeloss_all"] = (data_result["flow_p"] * data_result["timeloss_p"] + data_result["flow_t"] *
                                   data_result["timeloss_t"]) / data_result["flow_all"]
    data_result["speed_all"] = (data_result["flow_p"] * data_result["speed_p"] + data_result["flow_t"] * data_result[
        "speed_t"]) / data_result["flow_all"]
    data_result["TTC_all"] = data_result["flow_all"]*data_result["traveltime_all"]
    data_result["TTC_p"] = data_result["flow_p"] * data_result["traveltime_p"]
    data_result["TTC_t"] = data_result["flow_t"] * data_result["traveltime_t"]
    return data_result.copy()


numline = 4

path_result = "data/result/"+str(numline)+"/" +"3" +"_16_"

path_mpc = path_result + "mpc" + ".csv"
path_feedback = path_result + "feedback" + ".csv"
path_no = path_result + "no" + ".csv"

data_mpc = dftool.df_load_csv(path_mpc)
data_feedback = dftool.df_load_csv(path_feedback)
data_no = dftool.df_load_csv(path_no)
list_static = []
for i in range(numline):
    list_static.append(dftool.df_load_csv(path_result + "static_" + str(i) + ".csv"))

### 数据处理
data_mpc = get_result(data_mpc)
data_feedback = get_result(data_feedback)
data_no = get_result(data_no)
data_static = []
for i in range(numline):
    data_static.append(get_result(list_static[i]))

list_label=["Mpc","Feedback","TTSS","TTSP","TSPP","SSPP"]
labels = ["TTC","flow","speed","timeloss"]
labelc = ["all","p","t"]
fig,ax = plt.subplots(4, 3, figsize=(40,15))

for i in range(4):
    ax[i, 0].set_ylabel(labels[i])
    for j in range(3):
        ### 画图
        # fig=plt.figure(figsize=(15, 3), dpi=200)
        label = labels[i]+"_" +labelc[j]
        data_plot=pd.concat([data_mpc[label],data_feedback[label],data_static[3][label],data_static[2][label],data_static[1][label],data_static[0][label]], axis=1)

        ### 热力图
        data_plot=data_plot.astype('float').values.T
        tem_ax = ax[i,j].imshow(data_plot)
        ax[i,j].set_yticks(np.arange(0,6,1),list_label)
        ax[i,j].set_xticks(np.arange(0,22,2),np.arange(900,7500,600))
        fig.colorbar(tem_ax,ax =ax[i,j],orientation='horizontal',shrink=0.90)

ax[3, 0].set_xlabel("All classes")
ax[3, 1].set_xlabel("Passenger class")
ax[3, 2].set_xlabel("Truck class")
fig.align_labels()


plt.subplot_tool()
plt.show()