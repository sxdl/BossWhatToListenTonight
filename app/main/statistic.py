"""
statistic.py
author: Zicheng Zeng
date: 2023/6/20
description: 
"""
import os
from . import ncp
from . import fileio
from wordcloud import WordCloud
from scipy.interpolate import interp1d
import time


def is_user_data_exist(uid):
    file_dir = f"local/user/{uid}"
    return os.path.exists(file_dir)


def get_user_profile(uid):
    """
    获取用户头像 Url 和 昵称
    :param uid:
    :return:
    """
    user_info = ncp.get_user_detail(uid)
    # print(user_info.get('profile').get('avatarUrl'))
    return user_info.get('profile').get('avatarUrl'), user_info.get('profile').get('nickname'), user_info.get('level')


def get_user_fav_song(uid, reload=False):
    """
    从本地获取用户收藏歌曲id列表，如果本地没有，则爬取用户收藏歌曲数据并保存
    :param uid:
    :param reload:
    :return: list
    """
    file_dir = f"local/user/{uid}"
    if not os.path.exists(file_dir):
        print("make dir")
        os.mkdir(file_dir)
    file_path = f"{file_dir}/fav_song.txt"
    # check if data has been collected
    if not reload:
        if os.path.exists(file_path):
            return fileio.load_list(file_path)
    # if not, download
    song_ids = list(ncp.get_subscribe_playlist_songs_id(uid, fav_only=False))
    fileio.save_list(file_path, song_ids)
    return song_ids


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
    song_path = f"local/songs/{song_id}.pickle"
    # 判断音乐信息是否已经存在
    if not os.path.exists(song_path):
        print(f"not download yet, download {song_id}")
        spider_song_info(song_id, mode=1)
    song_data = fileio.load_pickle(song_path)
    return song_data


def save_song_info(song_id, song_info):
    """
    保存pickle格式的音乐信息
    :param song_id:
    :param song_info:
    :return:
    """
    song_path = f"local/songs/{song_id}.pickle"
    fileio.dump_pickle(song_info, song_path)


def get_song_ar(song_data):
    return song_data.get('ar')


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


def spider_song_info(iid, mode=0, comments=False):
    """
    爬取歌曲的 作曲、曲风标签和评论信息
    :param comments: 是否爬取评论
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
        song_path = f"local/songs/{song_id}.pickle"
        # 下载前判断是否已经下载，跳过
        if os.path.exists(song_path) and not comments:
            print(f"already download, pass {song_id}")
            continue

        song_name = ncp.get_song_detail([song_id])[0].get('name')

        artist = artist_dict.get(song_id)  # artist
        artist = [dict([('id', x.get('id')), ('name', x.get('name'))]) for x in artist]  # 删除artist冗余信息
        song_wiki = ncp.get_song_wiki(song_id)  # wiki (曲风、推荐标签、语种、BPM)
        song_comments = None
        if comments:
            song_comments = ncp.get_song_comments(song_id)  # comments

        song_info = {
            'name': song_name,
            'ar': artist,
            'wiki': song_wiki,
            'comments': song_comments
        }

        fileio.dump_pickle(song_info, song_path)


def load_tag_count(uid):
    file_path = f"local/user/{uid}/tag_count.pickle"
    if not os.path.exists(file_path):
        gen_tag_count(uid)
    return fileio.load_pickle(file_path)


def gen_tag_count(uid):
    """
    生成用户标签频次统计并保存
    :param uid:
    :return:
    """
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

    # 保存tag词频dict到用户本地文件夹中
    tag_count = {
        'melody_style': melody_style,
        'songBizTag': songBizTag,
        'language': language,
        'bpm': bpm
    }
    fileio.dump_pickle(tag_count, f"local/user/{uid}/tag_count.pickle")


def gen_bpm_chart(uid):
    """
    生成bpm统计图，修改js文件
    :param uid:
    :return:
    """
    tag_count = load_tag_count(uid)
    bpm = tag_count['bpm']
    # bpm插值
    x = list(map(int, bpm.keys()))
    y = list(bpm.values())
    f_bpm = interp1d(x, y, 'cubic')

    sorted_bpm_x = []
    sorted_bpm_y = []
    for i in range(min(x), max(x)+1):
        sorted_bpm_x.append(f'"{i}"')
        sorted_bpm_y.append(str(f_bpm(i)))

    label_str = ','.join(sorted_bpm_x)
    data_str = ','.join(sorted_bpm_y)

    with open(r"app/static/js/chart-template.js", 'r', encoding='utf-8') as fi:
        file_content = fi.readlines()
        file_content[7] = file_content[7].replace('[]', f"[{label_str}]")
        file_content[10] = file_content[10].replace('[]', f"[{data_str}]")
        with open(r"app/static/js/chart.js", 'w', encoding='utf-8') as fo:
            fo.writelines(file_content)


def gen_song_chart(sid):
    """
    分析评论区用户人群特征（性别，年龄，评论时间段），修改js文件
    :param sid:
    :return:
    """
    song_info = load_song_info(sid)
    if not song_info.get('analysis'):
        comments = song_info['comments']
        # 'userId', 'content', 'time'
        gender = {}
        age = {}
        area = {}
        timeperiod = {}
        for comment in comments:
            uid = comment['userId']
            user_detail = ncp.get_user_detail(uid)
            if not user_detail:
                continue
            if user_detail['profile']['privacyItemUnlimit']['gender']:  # 0保密，1男，2女
                gender[user_detail['profile']['gender']] = gender.get(user_detail['profile']['gender'], 0) + 1
            if user_detail['profile']['privacyItemUnlimit']['villageAge']:
                village_age = user_detail['createDays'] // 365
                age[village_age] = age.get(village_age, 0) + 1
            if user_detail['profile']['privacyItemUnlimit']['area']:
                area[user_detail['profile']['province']] = area.get(user_detail['profile']['province'], 0) + 1

            timestamp = comment['time']
            time_local = time.localtime(timestamp/1000)
            hour = time_local.tm_hour
            timeperiod[hour] = timeperiod.get(hour, 0) + 1

        gender_label = "['unknown', 'male', 'female']"
        gender_value = f"[{gender[0]}, {gender[1]}, {gender[2]}]"

        sorted_age_label = []
        sorted_age_value = []
        sorted_age = sorted(age)
        for k in sorted_age:
            sorted_age_label.append(f"'{k}'")
            sorted_age_value.append(f"{age[k]}")
        age_label = ','.join(sorted_age_label)
        age_value = ','.join(sorted_age_value)

        time_label = "['0:00', '1:00', '2:00', '3:00', '4:00', '5:00', '6:00', " \
                     "'7:00', '8:00', '9:00', '10:00', '11:00', '12:00', " \
                     "'13:00', '14:00', '15:00', '16:00', '17:00', '18:00', " \
                     "'19:00', '20:00', '21:00', '22:00', '23:00']"
        time_value = []
        for i in range(24):
            time_value.append(f"{timeperiod.get(i, 0)}")
        time_value = ','.join(time_value)

        if area.get(1000000):
            area.pop(1000000)
        if area.get(0):
            area.pop(0)

        # 保存处理后的数据
        analysis = {
            'age_label': age_label,
            'age_value': age_value,
            'time_label': time_label,
            'time_value': time_value,
            'gender_label': gender_label,
            'gender_value': gender_value,
            'area': area
        }
        song_info['analysis'] = analysis
        save_song_info(sid, song_info)

    else:
        age_label = song_info['analysis']['age_label']
        age_value = song_info['analysis']['age_value']
        time_label = song_info['analysis']['time_label']
        time_value = song_info['analysis']['time_value']
        gender_label = song_info['analysis']['gender_label']
        gender_value = song_info['analysis']['gender_value']

    with open(r"app/static/js/chart-template.js", 'r', encoding='utf-8') as fi:
        file_content = fi.readlines()

        # age
        file_content[32] = file_content[32].replace('[]', f"[{age_label}]")
        file_content[35] = file_content[35].replace('[]', f"[{age_value}]")

        # time
        file_content[63] = file_content[63].replace('[]', time_label)
        file_content[66] = file_content[66].replace('[]', f"[{time_value}]")

        # gender
        file_content[196] = file_content[196].replace('[]', gender_label)
        file_content[176] = file_content[176].replace('[]', gender_value)
        with open(r"app/static/js/chart-song.js", 'w', encoding='utf-8') as fo:
            fo.writelines(file_content)


def gen_user_chart(uid):
    """
    生成用户听歌偏好统计图（曲风、标签、语种、bpm）
    :param uid: 用户 uid
    :return:
    """
    tag_count = load_tag_count(uid)
    melody_style = tag_count['melody_style']
    songBizTag = tag_count['songBizTag']
    language = tag_count['language']

    # 生成词云图并保存
    file_dir = f"app/static/user/{uid}"
    if not os.path.exists(file_dir):
        print("make dir")
        os.mkdir(file_dir)

    font_path = "asset/msyh.ttc"
    melody_style_cloud = WordCloud(font_path=font_path, width=1000, height=1200,
                                   background_color="#191c24").generate_from_frequencies(melody_style)
    melody_style_cloud.to_file(f"{file_dir}/melody_style.jpg")
    songBizTag_cloud = WordCloud(font_path=font_path, width=1000, height=1200,
                                 background_color="#191c24").generate_from_frequencies(songBizTag)
    songBizTag_cloud.to_file(f"{file_dir}/songBizTag.jpg")
    language_cloud = WordCloud(font_path=font_path, width=1000, height=1200,
                               background_color="#191c24").generate_from_frequencies(language)
    language_cloud.to_file(f"{file_dir}/language.jpg")


def gen_comment_wordcount(sid):
    """
    生成评论区关键词 词云图
    :param sid:
    :return:
    """
    song_info = load_song_info(sid)['comments']
    comments = ' '.join(map(lambda x: x['content'].strip().replace('\n', ' '), song_info))
    # print(comments)

    font_path = "asset/msyh.ttc"
    file_dir = f"app/static/songs/{sid}"
    if not os.path.exists(file_dir):
        print("make dir")
        os.mkdir(file_dir)
    comments_cloud = WordCloud(font_path=font_path, width=600, height=600,
                               background_color="white").generate_from_text(comments)
    comments_cloud.to_file(f"{file_dir}/comment.jpg")


def get_song_wiki(song_data):
    return song_data.get('wiki')


def get_song_detail(sid):
    song_detail = ncp.get_song_detail([sid])[0]
    song_detail_ = {'id': sid,  'name': song_detail.get('name'), 'picUrl': song_detail.get('al').get('picUrl')}
    return song_detail_


def get_songs_detail(ids):
    songs_detail = ncp.get_song_detail(ids)
    song_detail_ = map(lambda s: {'id': s.get('id'), 'name': s.get('name'), 'picUrl': s.get('al').get('picUrl')}, songs_detail)
    return song_detail_


def recommend_from_track(uid, tid):
    """
    从指定歌单中挑选推荐音乐
    :param uid: 用户 id
    :param tid: 歌单 id
    :return:
    """
    tag_count = load_tag_count(uid)
    melody_style = tag_count['melody_style']
    songBizTag = tag_count['songBizTag']
    language = tag_count['language']
    bpm = tag_count['bpm']

    # 标签推荐权重
    style_weight = {}
    tag_weight = {}
    language_weight = {}
    bpm_weight = {}

    tag_order = [(melody_style, style_weight),
                 (songBizTag, tag_weight),
                 (language, language_weight),
                 (bpm, bpm_weight)]

    for data, weight in tag_order:
        sigma = sum(data.values())
        for key, value in data.items():
            weight[key] = value / sigma

    # bpm插值
    x = list(map(int, bpm_weight.keys()))
    y = list(bpm_weight.values())
    f_bpm = interp1d(x, y, 'cubic')

    # 从歌单中获取每个歌曲并计算推荐值，排序
    song_ids = ncp.get_playlist_all_track(tid)
    song_scores = {}

    for song_id in song_ids:
        song_info = load_song_info(song_id)
        song_wiki = get_song_wiki(song_info)
        style = song_wiki['melody_style']
        tag = song_wiki['songBizTag']
        language = song_wiki['language']
        bpm = song_wiki['bpm'] or 0
        bpm = int(bpm)
        if bpm < min(x) or bpm > max(x):
            bpm = 0

        score = sum(map(lambda s: 0.3 * style_weight.get(s, 0), style)) \
            + sum(map(lambda s: 0.3 * tag_weight.get(s, 0), tag)) \
            + sum(map(lambda s: 0.1 * language_weight.get(s, 0), language))

        if bpm != 0:
            score += 0.3 * f_bpm(bpm)

        # score = 0.3 * style_weight[style] + 0.3 * tag_weight[tag] + 0.1 * language_weight[language] + 0.3 * f_bpm(bpm)
        song_scores[song_id] = score
    # print(song_scores)
    return sorted(song_scores.items(), key=lambda kv: (kv[1], kv[0]), reverse=True)


def recommend_by_liked(uid):
    """
    传入用户uid，根据用户喜欢的音乐歌单推荐5个相关歌单
    :param uid:
    :return:
    """
    liked_playlist_id = ncp.get_user_liked_playlist_id(uid)
    recommend_tracks = ncp.get_related_playlist(liked_playlist_id)
    return recommend_tracks
