"""
__init__.py
author: Zicheng Zeng
date: 2023/6/19
description: 
"""
from flask import Blueprint
from .. import musicPlatform

# 开启网易云api代理
ncp = musicPlatform.create_app()
ncp.run()

main = Blueprint('main', __name__)

from . import views, errors
