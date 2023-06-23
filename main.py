"""
main.py
author: Zicheng Zeng
date: 2023/6/18
description: 
"""
import os
import sys
import time

import app


app = app.create_app(sys.argv[1])  # python main.py debug
app.run()


