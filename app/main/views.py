"""
views.py
author: Zicheng Zeng
date: 2023/6/19
description: 
"""
import time

from flask import render_template, request, redirect, url_for, session
from . import main, statistic
from threading import Thread
from collections import OrderedDict
from .const import ProvinceCode


@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == "POST":
        # print(f'get uid{request.form.get("uid")}')
        uid = request.form.get("uid")
        session['uid'] = uid
        return redirect(url_for('main.spider'))
    # print('get request')
    return render_template('index.html')


@main.route('/spider')
def spider():
    uid = session.get('uid')
    fav_song = statistic.get_user_fav_song(uid, reload=request.args.get('reload', False))
    if request.args.get('download', False):
        statistic.spider_song_info(uid)
        return redirect(url_for('main.dashboard'))

    user_avatar, user_nickname, level = statistic.get_user_profile(uid)
    profile = {'avatar': user_avatar, 'nickname': user_nickname, 'level': level, 'uid': uid}
    session['profile'] = profile

    return render_template('spider.html', profile=profile, num=len(fav_song), uid=uid)
    # return render_template('base-page.html', profile=profile)


@main.route('/home')
def home():
    """
    abandoned
    :return:
    """
    uid = session['uid']
    # user_avatar, user_nickname = statistic.get_user_profile(uid)
    is_reload = request.args.get('reload', False)
    fav_song = statistic.get_user_fav_song(uid, is_reload)
    return render_template('home.html', uid=uid, profile=session['profile'])


@main.route('/dashboard')
def dashboard():
    uid = session['uid']
    rank_fav_art = statistic.rank_fav_ar(uid, limit=10)
    rank_fav_songs = statistic.rank_fav_song(uid, limit=10)
    statistic.gen_tag_count(uid)
    statistic.gen_user_chart(uid)
    tag_count = statistic.load_tag_count(uid)
    tag_cloud_path = f"/static/user/{uid}/"

    statistic.gen_bpm_chart(uid)
    return render_template('dashboard.html',
                           uid=uid, profile=session['profile'],
                           artists=rank_fav_art,
                           song_list=rank_fav_songs,
                           tag_count=tag_count,
                           tag_cloud_path=tag_cloud_path)


@main.route('/about-song')
def about_song():
    sid = request.args.get('id')
    song_data = statistic.load_song_info(sid)
    if not song_data['comments']:
        statistic.spider_song_info(sid, mode=1, comments=True)
    statistic.gen_comment_wordcount(sid)
    # print(song_data)
    song_info = statistic.get_song_detail(sid)

    # 分析评论区用户人群特征
    # 性别，年龄，评论时间段
    statistic.gen_song_chart(sid)
    area = statistic.load_song_info(sid)['analysis']['area']
    sorted_area = sorted(area.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)[:5]
    inverse_code = dict(zip(ProvinceCode.values(), ProvinceCode.keys()))
    return render_template('about-song.html', profile=session['profile'], song=song_data,
                           songinfo=song_info, sid=sid,
                           area=sorted_area, code=inverse_code)


@main.route('/recommend')
def recommend():
    uid = session['uid']
    playlist_id = request.args.get('id')
    if playlist_id:
        recommend_songs = OrderedDict(statistic.recommend_from_track(uid, playlist_id)[:10])
        recommend_song_ids = list(recommend_songs.keys())
        scores = list(recommend_songs.values())
        recommend_song_details = statistic.get_songs_detail(recommend_song_ids)
        songs = zip(recommend_song_details, scores)
        return render_template('recommend.html', profile=session['profile'], songs=songs)
    recommend_playlists = statistic.recommend_by_liked(uid)
    return render_template('recommend.html', profile=session['profile'], playlists=recommend_playlists)
