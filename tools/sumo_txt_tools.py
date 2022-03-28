#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计(sumo文本编辑)
# user: Ricardo
# Author: Ricardo
# create-time: 2022/3/27


def get_vType_str(dic):
    s = "<vType"
    for k, v in dic.items():
        s = s + ' ' + k + '="' + v + '"'
    s = s+ "/>\n"
    return s


def get_flow_str(dic):
    s = "<flow"
    for k, v in dic.items():
        s = s + ' ' + k + '="' + v + '"'
    s = s+ "/>\n"
    return s