"""
fileio.py
author: Zicheng Zeng
date: 2023/5/11
description: input output operation of files
"""
import json
import pickle


def load_list(path):
    """
    从文件中读取列表
    :param path:
    :return: list
    """
    with open(path, "r") as f:
        data = f.read().splitlines()
    return data


def save_list(path, data):
    """
    保存list到文件
    :param path:
    :param data:
    :return:
    """
    with open(path, 'w') as f:
        for line in data:
            f.write(f"{str(line)}\n")


def load_json(path):
    """
    从路径中加载json文件
    :param path:
    :return: json dict
    """
    with open(path, "r") as f:
        data = json.load(f)
    return data


def dump_json(data, path):
    with open(path, 'w+') as f:
        json.dump(data, f, ensure_ascii=False)


def load_pickle(path):
    with open(path, "rb") as f:
        data = pickle.load(f)
    return data


def dump_pickle(data, path):
    with open(path, 'wb') as f:
        pickle.dump(data, f)
