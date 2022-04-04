

from ETC_data_change.controlstructure import Controls

control = Controls(3)
control.mpc_controls(["T", "S", "P"])
# control.feedback_controls(["T", "S", "S"])  # 反馈控制
# control.static_controls(["T", "S", "P"]) # 静态控制与无控制
# control.time_controls(["T", "S", "P"],{3000:["T", "S", "S"],6000:["S", "S", "P"]}) # 定时控制


