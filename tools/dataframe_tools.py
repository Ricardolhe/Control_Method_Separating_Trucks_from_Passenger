#!/usr/bin/python3
# -*- coding:utf-8 -*-
# project: 毕业设计
# user: Ricardo
# Author: Ricardo
# create-time: 2022/3/22
import time
import pandas as pd


class DaTaFrameTool(object):
    """
    DaTaFrame格式相关的类
    """

    @staticmethod
    def df_save_excel(df_data, save_path):
        """
        df格式保存为excel
        :param df_data: df列表
        :param save_path: excel地址
        """
        writer = pd.ExcelWriter(save_path)
        df_data.to_excel(writer,index=False)
        writer.save()

    @staticmethod
    def df_save_csv(df_data, path_save):
        """
        保存csv文件
        :param df_data: df列表
        :param path_save:存储数据的文件夹路径
        :return:生成csv文件
        """
        df_data.to_csv(path_save, encoding="utf-8", index=False)
