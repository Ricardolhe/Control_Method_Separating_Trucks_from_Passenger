#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2022/3/22
import time


def timestamp_to_time(timestamp):
    """
    将时间戳转成标准时间
    :param timestamp：时间戳，如1462451334000 ，ms
    :return: 标准时间格式 "2016-05-05 20:28:54"
    """
    # 转换成localtime
    time_local = time.localtime(timestamp / 1000)
    # 转换成新的时间格式(2016-05-05 20:28:54)
    dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
    return dt


def str_change_time(time_str):
    """
    日期字符串转换格式
    :param time_str: "20211019"
    :return: "2021-10-19"
    """
    dt = time_str[:4] + "-" + time_str[4:6] + "-" + time_str[6:]
    return dt


