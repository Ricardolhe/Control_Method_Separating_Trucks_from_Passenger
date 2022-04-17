import numpy as np
import pandas as pd

from ETC_data_change.controlstructuregetdata import Controls
from ETC_data_change.pantdesgin import PlanPT

numline = 4
seed_i= 3
control = Controls(numline,["sumo", "-c", "data/map/maptest"+str(numline)+"/road.sumocfg","--seed",str(seed_i)])  #创建控制中心对象
planpt = PlanPT(control.control_road)   # 创建客货分道方案对象
path_result = "data/result/"+str(numline)+"_17/"


# 记录模型预测控制结果
result,plan_list,result_time= control.mpc_controls(["S"]*numline)
result.to_csv(path_result + "mpc_in" + ".csv",index =False)  # 记录
result_time.to_csv(path_result + "mpc_time" + ".csv",index =False)
plan_list = pd.DataFrame(np.array(plan_list[2:])).to_csv(path_result + "mpc_plan" + ".csv",index =False)
#
# #

#
# 记录反馈控制结果
result,plan_list,result_time = control.feedback_controls(["S"]*numline)  # 反馈控制
result.to_csv(path_result + "feedback_in" + ".csv",index =False)
result_time.to_csv(path_result + "feedback_time" + ".csv",index =False)
plan_list = pd.DataFrame(np.array(plan_list[2:])).to_csv(path_result + "feedback_plan" + ".csv",index =False)
#

# 记录静态控制结果
l_plan = len(planpt.plans)
for i in range(l_plan):
    result,result_time = control.static_controls(planpt.plans[i])
    result.to_csv(path_result + "static_in" + str(i) + ".csv", index=False)
    result_time.to_csv(path_result + "static_time" + str(i) + ".csv", index=False)

