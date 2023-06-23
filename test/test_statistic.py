"""
test_statistic.py
author: Zicheng Zeng
date: 2023/6/22
description: 
"""
from app.main import statistic
import os

os.chdir("..")

statistic.recommend_from_track("1526176774", "")
