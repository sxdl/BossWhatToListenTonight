"""
statistics.py
author: Zicheng Zeng
date: 2023/5/10
description: 
"""
import os.path

from module.musicPlatform.neteaseCloudMusicApi import NeteaseCloudMusicProxy
from module.common import function, fileio
import json
from module.common.const import SONG_INFO_STORAGE_DIR, USER_FAV_SONG_DIR, FAV_SONG_FILE

ncp = NeteaseCloudMusicProxy()
ncp.startup()


def get_user_profile(uid):
    """
    获取用户头像 Url 和 昵称
    :param uid:
    :return:
    """
    user_info = ncp.get_user_detail(uid)
    print(user_info.get('profile').get('avatarUrl'))
    return user_info.get('profile').get('avatarUrl'), user_info.get('profile').get('nickname')


def get_user_fav_song(uid, reload=False):
    """
    从本地获取用户收藏歌曲id列表，如果本地没有，则爬取数据并保存
    :param uid:
    :param reload:
    :return: list
    """
    file_dir = f"{USER_FAV_SONG_DIR}{uid}"
    if not os.path.exists(file_dir):
        print("make dir")
        os.mkdir(file_dir)
    file_path = f"{file_dir}/{FAV_SONG_FILE}"
    # check if data has been collected
    if not reload:
        if os.path.exists(file_path):
            return fileio.load_list(file_path)
    # if not, download
    song_ids = list(ncp.get_subscribe_playlist_songs_id(uid))
    fileio.save_list(file_path, song_ids)
    return song_ids


def spider_song_info(uid):
    """
    爬取歌曲的 作曲、曲风标签和评论信息
    :param uid:
    :return:
    """
    song_ids = get_user_fav_song(uid)

    # artist
    song_details = ncp.get_song_detail(song_ids)
    song_artists = [x.get('ar') for x in song_details]
    artist_dict = dict(zip(song_ids, song_artists))

    for song_id in song_ids:
        song_path = f"{SONG_INFO_STORAGE_DIR}{song_id}.pickle"
        # 下载前判断是否已经下载，跳过
        if os.path.exists(song_path):
            print(f"already download, pass {song_id}")
            continue

        artist = artist_dict.get(song_id)  # artist
        artist = [dict([('id', x.get('id')), ('name', x.get('name'))]) for x in artist]  # 删除artist冗余信息
        song_wiki = ncp.get_song_wiki(song_id)  # wiki (曲风、推荐标签、语种、BPM)
        song_comments = ncp.get_song_comments(song_id)  # comments

        song_info = {
            'ar': artist,
            'wiki': song_wiki,
            'comments': song_comments
        }

        fileio.dump_pickle(song_info, song_path)


def load_song_info(song_id):
    song_path = f"{SONG_INFO_STORAGE_DIR}{song_id}.pickle"
    song_data = fileio.load_pickle(song_path)
    return song_data


def get_song_ar(song_data):
    return song_data.get('ar')


def get_song_wiki(song_data):
    return song_data.get('wiki')


def get_song_comments(song_data):
    """
    评论编码：gb18030
    :param song_data:
    :return:
    """
    return song_data.get('comments')
