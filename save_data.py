import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

import tools.dataframe_tools as dftool

# 设置绘图样式
plt.style.use(['science','no-latex'])


def get_result(type_con):
    start = 900
    end = 7200
    data_result = pd.DataFrame(columns=["beishu", "speed_all", "timeloss_all", "traveltime_all", "flow_all",
                                        "speed_p", "timeloss_p", "traveltime_p", "flow_p",
                                        "speed_t", "timeloss_t", "traveltime_t", "flow_t", ])

    types = ["passenger", "coach", "truck", "trailer"]
    vs = [120, 100, 90, 80]  # 限速
    index = 0
    l = 8500
    for bei in np.linspace(1.0, 2.0, 11):
        # path_result = "data/result/" + str(numline) + "/" + "3_" +str(int(bei * 10)) + "_"
        path_result = "data/result/" + str(numline) + "/" + str(int(bei * 10)) + "_"
        path = path_result + type_con + ".csv"
        data = dftool.df_load_csv(path)
        data = data.loc[(data["time_y"] >= start) & (data["time_y"] <= end)]
        for i in range(len(types)):
            data.loc[data["vclass_x"] == types[i], "vs"] = vs[i]
        data["timeloss"] = data["travel_time"] - l / data["vs"] * 3.6
        data["speed"] = l / data["travel_time"] * 3.6
        # data["pcu"] = 1
        df_p = data.loc[(data["vclass_x"] == types[0]), :]
        df_t = data.loc[(data["vclass_x"] != types[0]), :]

        data_result.loc[index, "beishu"] = bei

        data_result.loc[index, "flow_p"] = sum(df_p["pcu"])
        data_result.loc[index, "traveltime_p"] = df_p["travel_time"].mean()
        data_result.loc[index, "speed_p"] = df_p["speed"].mean()
        data_result.loc[index, "timeloss_p"] = df_p["timeloss"].mean()

        data_result.loc[index, "flow_t"] = sum(df_t["pcu"])
        data_result.loc[index, "traveltime_t"] = sum(df_t["travel_time"] * df_t["pcu"]) / data_result.loc[
            index, "flow_t"]
        data_result.loc[index, "speed_t"] = sum(df_t["speed"] * df_t["pcu"]) / data_result.loc[index, "flow_t"]
        data_result.loc[index, "timeloss_t"] = sum(df_t["timeloss"] * df_t["pcu"]) / data_result.loc[index, "flow_t"]

        index += 1

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

def save_data(numline):
    data_mpc = get_result("mpc")

    data_feedback = get_result("feedback")
    data_no = get_result("no")
    for i in range(numline):
        dftool.df_save_excel(get_result("static_" + str(i)),"static_" + str(i)+".xlsx")
    dftool.df_save_excel(data_mpc, "mpc.xlsx")
    dftool.df_save_excel(data_feedback, "feedback.xlsx")



numline = 3
save_data(numline)