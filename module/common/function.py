"""
function.py
author: Zicheng Zeng
date: 2023/4/21
description: common function used by multiple modules
"""
from subprocess import Popen, PIPE, STDOUT
from requests import get
from module.common.const import NETEASE_CLOUD_MUSIC_API_URL, USER_LOCAL_STORAGE_PATH
from time import time
from base64 import b64decode
import json
import time


def shell_command(command: str, cwd=None, stdout=None, stderr=None):
    """
    执行shell命令并实时显示返回结果
    :param stderr:
    :param stdout:
    :param cwd: shell执行目录
    :param command: shell命令
    :return:
    """
    print(cwd, command)
    process = Popen(command, shell=True, cwd=cwd, stdout=stdout, stderr=stderr)  # stdout=PIPE, stderr=STDOUT,
    return process


def read_shell_output(process):
    """
    读取shell返回值(abused)
    :return:
    """
    with process.stdout:
        for line in iter(process.stdout.readline, b''):
            print(line.decode().strip())
    exitcode = process.wait()
    return exitcode


def api_get(api_url: str, root_url: str = NETEASE_CLOUD_MUSIC_API_URL):
    """
    发送调用api接口请求
    :param root_url:
    :param api_url:
    :return: response
    """
    while True:
        r = get(url=root_url + api_url)
        s = r.json()
        if s['code'] == 200:
            return r
        else:
            print(f"Request Fails: {s['code']}")
            print("retrying...")
            time.sleep(2)


def timestamp():
    """
    获取13位时间戳
    :return: 13位整型时间戳
    """
    return int(time() * 1000)


def base642bytes(data):
    """
    将base64格式转换成bytes
    :param data: base64格式数据
    :return: bytes
    """
    return b64decode(data)


def save_img(root_path, filename, code, data):
    """
    将字节数据保存到指定路径，指定格式的图片
    :param root_path: 保存的图片所在目录
    :param filename: 图片文件名
    :param code: 图片编码格式（'jpg','png',...)
    :param data: bytes 图片数据
    :return:
    """
    with open(f'{root_path}/{filename}.{code}', 'wb') as p:
        p.write(data)


def setItem(key, value):
    with open(USER_LOCAL_STORAGE_PATH, 'w+') as f:
        data = json.loads(f.read())
        data[key] = value
        f.seek(0)
        f.write(data)


def dump_json(data, path):
    with open(path, 'w+') as f:
        json.dump(data, f, ensure_ascii=False)

