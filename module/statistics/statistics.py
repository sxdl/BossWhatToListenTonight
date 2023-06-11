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
from wordcloud import WordCloud

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
    从本地获取用户收藏歌曲id列表，如果本地没有，则爬取用户收藏歌曲数据并保存
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


def spider_song_info(iid, mode=0):
    """
    爬取歌曲的 作曲、曲风标签和评论信息
    :param mode: mode=0 传入 用户id；mode=1 传入 歌曲id
    :param iid: 用户uid：用户收藏的所有歌曲的歌曲信息 | 歌曲sid：单个歌曲的歌曲信息
    :return:
    """
    if mode == 0:
        song_ids = get_user_fav_song(iid)
    elif mode == 1:
        song_ids = [iid]
    else:
        raise ValueError("Invalid mode value!")

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


def rank_fav_ar(uid, limit=10):
    """
    收藏歌曲歌手排行，需要剔除无 id歌手（id=0）
    :param limit: 返回最大歌手数量
    :param uid:
    :return:(id, name, 头像url, 出现次数)
    """
    fav_songs = get_user_fav_song(uid)
    ar_dict = dict()
    for song in fav_songs:
        song_info = load_song_info(song)
        ar_id_list = get_song_ar(song_info)
        for ar_id in ar_id_list:
            ar_dict[ar_id.get('id')] = ar_dict.get(ar_id.get('id'), 0) + 1
    if ar_dict.get(0):  # 剔除无 id歌手(id=0)
        ar_dict.pop(0)
    sorted_art = sorted(ar_dict.items(), key=lambda x: (x[1], x[0]), reverse=True)
    if len(sorted_art) > limit:
        sorted_art = sorted_art[:limit]
    sorted_art_detail = [(ncp.get_artist_detail(x[0]), x[1]) for x in sorted_art]
    return sorted_art_detail


def load_song_info(song_id):
    """
    导入pickle格式的音乐信息
    :param song_id:
    :return:
    """
    song_path = f"{SONG_INFO_STORAGE_DIR}{song_id}.pickle"
    # 判断音乐信息是否已经存在
    if not os.path.exists(song_path):
        print(f"not download yet, download {song_id}")
        spider_song_info(song_id, mode=1)
    song_data = fileio.load_pickle(song_path)
    return song_data


def rank_fav_song(uid, limit=10):
    """
    list[{'playCount', 'score', 'song': {'name', 'id', 'al': {'picUrl'}}}]
    :param uid:
    :param limit:
    :return:
    """
    fav_songs = ncp.get_user_record(uid, mode=0)
    if len(fav_songs) > limit:
        fav_songs = fav_songs[:limit]
    return fav_songs


def gen_tag_count(uid):
    """
    生成用户标签频次统计并保存
    :param uid:
    :return:
    """
    tag_count = dict()
    melody_style = dict()
    songBizTag = dict()
    language = dict()
    bpm = dict()
    # 根据uid获取用户收藏音乐列表
    fav_songs = get_user_fav_song(uid)
    # 获取列表中每首音乐的wiki信息
    # 将每个wiki词条分别存储在字典中计数
    for song in fav_songs:
        song_data = load_song_info(song)
        song_wiki = get_song_wiki(song_data)
        for itm in song_wiki['melody_style']:
            melody_style[itm] = melody_style.get(itm, 0) + 1
        for itm in song_wiki['songBizTag']:
            songBizTag[itm] = songBizTag.get(itm, 0) + 1
        for itm in song_wiki['language']:
            language[itm] = language.get(itm, 0) + 1
        if song_wiki['bpm']:
            bpm[song_wiki['bpm']] = bpm.get(song_wiki['bpm'], 0) + 1
    # tag_count['melody_style'] = sorted(melody_style.items(), key=lambda x: (x[1], x[0]), reverse=True)
    # tag_count['melody_style'] = [{x: y} for x, y in tag_count['melody_style']]
    #
    # tag_count['songBizTag'] = sorted(songBizTag.items(), key=lambda x: (x[1], x[0]), reverse=True)
    # tag_count['songBizTag'] = [{x: y} for x, y in tag_count['songBizTag']]
    #
    # tag_count['language'] = sorted(language.items(), key=lambda x: (x[1], x[0]), reverse=True)
    # tag_count['language'] = [{x: y} for x, y in tag_count['language']]
    #
    # tag_count['bpm'] = sorted(bpm.items(), key=lambda x: (x[1], x[0]), reverse=True)
    # tag_count['bpm'] = [{x: y} for x, y in tag_count['bpm']]

    # 生成词云图并保存
    melody_style_cloud = WordCloud(font_path='../../asset/msyh.ttc', width=1000, height=700,
                                   background_color="white").generate_from_frequencies(melody_style)
    melody_style_cloud.to_file(f"{USER_FAV_SONG_DIR}{uid}/melody_style.jpg")
    songBizTag_cloud = WordCloud(font_path='../../asset/msyh.ttc', width=1000, height=700,
                                   background_color="white").generate_from_frequencies(songBizTag)
    songBizTag_cloud.to_file(f"{USER_FAV_SONG_DIR}{uid}/songBizTag.jpg")
    language_cloud = WordCloud(font_path='../../asset/msyh.ttc', width=1000, height=700,
                                   background_color="white").generate_from_frequencies(language)
    language_cloud.to_file(f"{USER_FAV_SONG_DIR}{uid}/language.jpg")
    # 保存tag词频dict到用户本地文件夹中
    fileio.dump_pickle(tag_count, f"{USER_FAV_SONG_DIR}{uid}/tag_count.pickle")


def load_tag_count(uid):
    return fileio.load_pickle(f"{USER_FAV_SONG_DIR}{uid}/tag_count.pickle")


def get_song_ar(song_data):
    return song_data.get('ar')


def get_song_wiki(song_data):
    return song_data.get('wiki')


def get_song_comments(song_data):
    """
    评论编码：gb18030
    """
    return song_data.get('comments')
