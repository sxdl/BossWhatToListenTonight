"""
app.py
author: sxdl
date: 2023/5/6
description: 
"""
from flask import Flask, render_template, request, redirect, url_for
from module.statistics import statistics

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index_get():
    return render_template('index.html')


@app.route('/', methods=['POST'])
def index_post():
    uid = request.form.get('uid')
    # 对 uid 进行处理
    if uid is None:
        return "Invalid Input"
    print(f"uid is {uid}")
    return redirect(url_for('home_get', uid=uid))


@app.route('/home.html/<uid>', methods=['GET'])
def home_get(uid):
    user_avatar, user_nickname = statistics.get_user_profile(uid)
    return render_template('home.html', avatarUrl=user_avatar, nickname=user_nickname, uid=uid)


@app.route('/dashboard.html/<uid>')
def dashboard_get(uid):
    rank_fav_art = statistics.rank_fav_ar(uid, limit=3)
    print(f"dashboard: {rank_fav_art}")
    return render_template('dashboard.html', artists=rank_fav_art)

