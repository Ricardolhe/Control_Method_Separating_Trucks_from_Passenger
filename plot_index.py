# 画指标优化比例


import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])

def get_date(data):
    data["bili"] = [1] * 6 + [-1] * 6
    for i in data.columns[2:7]:
        data.loc[:,i] = (data.loc[:,i]-data.loc[:,"Mpc"])/data.loc[:,i]*100 * data.loc[:,"bili"]

    del data["bili"]
    data.index = data.iloc[:,0]
    del data[data.columns[0]]
    del data["Mpc"]
    data = pd.DataFrame(data.values.T, index=data.columns, columns=data.index)

    label_class = ["all", "p", "t"]
    w = [1, 1, 1, 1]
    # 计算整体指标
    for i in label_class:
        data["Total_"+i] = (w[0]*data["TTC_"+i] + w[1]*data["Flow_"+i] +w[2]*data["Speed_"+i]+w[3]*data["Timeloss_"+i])/sum(w)


    return data

numline = 4

path_result = "data/result/"+str(numline)+"_17/"

path_data = path_result + "结果.xlsx"

data = dftool.df_load_excel(path_data)

data = get_date(data)

# plot bar
label_i = 4
label_index = ["TTC","Flow","Speed","Timeloss","Total"][label_i]
label_class = ["all","p","t"]
list_label=["Feedback","SSP","TSP","TSS"]
label_plot = [label_index + "_" + i for i in label_class]




fig,ax=plt.subplots(figsize=(20,20))
data_plot = data.loc[:,label_plot]
data_plot.plot(kind='bar', stacked=False,ax=ax)
ax.legend([label_index + "_" + i for i in ["All classes","Passenger class","Truck class"]])
plt.xticks(rotation=0)
ax.set_ylabel("Effects of optimization(%)")
ax.set_title("Percentage improvement of MPC compared with other methods",fontdict={'size': 20})
plt.axhline(0, color='grey', linewidth=0.8)

for x,y in zip(range(0,5),data_plot[label_plot[0]]):
    plt.text(x-0.17,y+0.05,'%.2f' %y +"%", ha='center',va='bottom')
for x,y in zip(range(0,5),data_plot[label_plot[1]]):
    plt.text(x,y+0.05,'%.2f' %y +"%", ha='center')
for x,y in zip(range(0,5),data_plot[label_plot[2]]):
    plt.text(x+0.17,y+0.05,'%.2f' %y +"%", ha='center')

plt.show()
print(1)