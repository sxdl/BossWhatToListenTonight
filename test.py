"""
test.py.py
author: sxdl
date: 2023/4/21
description: script for test only
"""
import os
import time
import codecs
from module.common import const
import signal
from module.common import function
from module.application import server
from module.common.const import FLASK_CWD, FLASK_RUN_COMMAND


### 测试单个模块时取消注释 ###
# cwd = os.getcwd()
# os.chdir("./module/application/")
from module.statistics import statistics
# os.chdir(cwd)


# # server.join()
#
# ncm = NeteaseCloudMusicProxy()
# ncm.startup()
# # ncm.login_qr()
# playlist = ncm.get_song_wiki('1396905934')
# print(playlist)

def test_fav_song(uid):
    """
    test for 听歌次数排行
    :param uid:
    :return:
    """
    favsong = statistics.rank_fav_song(uid)
    time.sleep(3)


def test_fav_art(uid):
    """
    test for 歌手排行
    :param uid:
    :return:
    """
    ar_rank = statistics.rank_fav_ar(uid)
    time.sleep(3)


def test_song_info(uid):
    """
    test for 爬取歌曲音乐信息
    """
    statistics.spider_song_info(uid, mode=1)
    time.sleep(3)


def test_load_song_info(uid):
    """
    test for 从本地读取音乐信息
    """
    song_data = statistics.load_song_info(uid)
    artist = statistics.get_song_ar(song_data)
    wiki = statistics.get_song_wiki(song_data)
    comments = statistics.get_song_comments(song_data)
    print(2)


if __name__ == "__main__":
    # test_uid = 6280920254


    flask_server = server.WebServer(FLASK_RUN_COMMAND, FLASK_CWD)
    flask_server.run()

    time.sleep(3)

    # test_song_info("1854902495")
    # test_fav_song("1526176774")
    # test_fav_art("1526176774")
    # test_load_song_info("1382367245")

    time.sleep(300)
    # flask_server.stop()



