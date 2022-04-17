

from ETC_data_change.controlstructure import Controls
from ETC_data_change.pantdesgin import PlanPT

numline = 4
seed_i= 3
control = Controls(numline,["sumo-gui", "-c", "data/map/maptest"+str(numline)+"/road.sumocfg","--seed",str(seed_i)])  #创建控制中心对象
planpt = PlanPT(control.control_road)   # 创建客货分道方案对象
path_result = "data/result/"+str(numline)+"/"


# # 记录模型预测控制结果
result= control.mpc_controls(["S"]*numline)
result.to_csv(path_result + "mpc" + ".csv",index =False)
#
# # 记录无控制结果
result = control.static_controls()# 无控制
result.to_csv(path_result + "no" + ".csv",index =False)

# 记录静态控制结果
l_plan = len(planpt.plans)
for i in range(l_plan):
    result = control.static_controls(planpt.plans[i])
    result.to_csv(path_result + "static_" + str(i) + ".csv", index=False)

# 记录反馈控制结果
result = control.feedback_controls(["S"]*numline)  # 反馈控制
result.to_csv(path_result + "feedback" + ".csv",index =False)








# # control.time_controls(planpt.plans[1],{3000:planpt.plans[2],6000:planpt.plans[0]}) # 定时控制


