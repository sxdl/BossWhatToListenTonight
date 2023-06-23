"""
errors.py
author: Zicheng Zeng
date: 2023/6/19
description: 
"""
from flask import render_template
from . import main


@main.app_errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404
