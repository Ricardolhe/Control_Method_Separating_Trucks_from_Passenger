

from ETC_data_change.controlstructure import Controls
from ETC_data_change.pantdesgin import PlanPT

numline = 4
control = Controls(numline,["sumo-gui", "-c", "data/map/maptest"+str(numline)+"/road.sumocfg"])  #创建控制中心对象
planpt = PlanPT(control.control_road)   # 创建客货分道方案对象

# result = planpt.pick_best_plan_feedback([1000,10contral00,500,100])
control.mpc_controls(planpt.plans[0])
# control.feedback_controls(planpt.plans[0])  # 反馈控制
# control.static_controls() # 无控制
# control.static_controls(planpt.plans[0]) # 静态控制与无控制

# control.time_controls(planpt.plans[1],{3000:planpt.plans[2],6000:planpt.plans[0]}) # 定时控制


