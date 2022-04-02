#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2022/3/22
import time
import pandas as pd
import json

def df_save_excel(df_data, save_path):
    """
    df格式保存为excel
    :param df_data: df列表
    :param save_path: excel地址
    """
    writer = pd.ExcelWriter(save_path)
    df_data.to_excel(writer,index=False)
    writer.save()


def df_save_csv(df_data, path_save):
    """
    保存csv文件
    :param df_data: df列表
    :param path_save:存储数据的文件夹路径
    :return:生成csv文件
    """
    df_data.to_csv(path_save, encoding="utf-8", index=False)


def df_load_excel(path_load):
    """
    读取excel文件
    :param path_load:存储数据的文件夹路径
    :return:生成数据表
    """
    return pd.read_excel(path_load, header=[0])


def df_load_csv(path_load):
    """
    读取csv文件
    :param path_load:存储数据的文件夹路径
    :return:生成数据表
    """
    return pd.read_csv(path_load,header=[0])


def df_save_json(filename,data):
    with open(filename, 'w') as file_obj:
        json.dump(data,file_obj)


def df_load_json(filename):
    with open(filename) as file_obj:
        names = json.load(file_obj)
    return names

