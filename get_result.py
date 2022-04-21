# 周期获取微波数据
from ETC_data_change.weibodata import DataUlit,PeriodDataUlit
import pandas as pd
import numpy as np
import tools.dataframe_tools as dt
from ETC_data_change.controlstructure import Controls
from ETC_data_change.pantdesgin import PlanPT

def set_rou(numline,bei):
    path = "data/副本沪苏浙高速交调数据20210119-20210219(1).csv"
    path_result = "data/map/maptest"+str(numline)+"/road.rou.xml"
    deviceID = 71270320100006
    direction = 0
    date = "2021-01-26"
    start_time = "2021-01-26 12:00:00"
    end_time = "2021-01-26 14:00:00"

    weibo = DataUlit()
    weibo.df_read_csv(path)
    etc_data = weibo.select_data(deviceID, direction)  # 筛选合适的数据
    etc_data_20 = etc_data.get_alltype_perioddata(start_time, end_time, 20)  # 20min聚合
    df_PtoT = pd.DataFrame(columns=["start_time", "end_time", "PtoT"])  # 各个时段客货比关系
    df_PtoT["PtoT"] = [1, 1/4, 4, 1/3, 3, 1]  # 各个时段客货比关系
    # df_PtoT["PtoT"] = [1/6]*6  # 各个时段客货比关系
    df_PtoT.loc[:,["start_time", "end_time"]] = etc_data_20.loc[:,["start_time", "end_time"]]
    data = PeriodDataUlit(etc_data_20)
    data.extend_all_flow(bei, False)
    df_PtoT = data.get_P_to_T(df_PtoT)
    data.extend_PandT_flow(df_PtoT, False)  # 三车道交通量
    # etc_data_20=etc_data_20.get_percent_eachtime()
    data = data.get_num_eachtime()
    PeriodDataUlit.change_to_sumo_flow_num(data, path_result, start_time, numline)


if __name__ == "__main__":
    numline =3
    # 设置rou
    seed_i= 1111
    for bei in np.linspace(2.0,2.0,1):
        print(bei)
        set_rou(numline,bei)
        control = Controls(numline, ["sumo", "-c", "data/map/maptest" + str(numline) + "/road.sumocfg","--seed",str(seed_i)])  # 创建控制中心对象
        planpt = PlanPT(control.control_road)  # 创建客货分道方案对象
        path_result = "data/result/" + str(numline) + "/" +str(int(bei*10)) +"_"

        # 记录模型预测控制结果
        result= control.mpc_controls(["S"]*numline)
        result.to_csv(path_result + "mpc" + ".csv",index =False)
        #
        # # # 记录无控制结果
        # result = control.static_controls()# 无控制
        # result.to_csv(path_result + "no" + ".csv",index =False)

        # 记录静态控制结果
        l_plan = len(planpt.plans)
        for i in range(l_plan):
            result = control.static_controls(planpt.plans[i])
            result.to_csv(path_result + "static_" + str(i) + ".csv", index=False)

        # # 记录反馈控制结果
        result = control.feedback_controls(["S"]*numline)  # 反馈控制
        result.to_csv(path_result + "feedback" + ".csv",index =False)




