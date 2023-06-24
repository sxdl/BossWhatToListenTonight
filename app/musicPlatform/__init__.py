"""
__init__.py
author: Zicheng Zeng
date: 2023/6/19
description: 
"""
from .neteaseCloudMusicApi import NeteaseCloudMusicProxy


def create_app():
    ncp = NeteaseCloudMusicProxy()
    return ncp
