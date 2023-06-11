"""
const.py
author: Zicheng Zeng
date: 2023/4/21
description: 存放常量
"""

NETEASE_CLOUD_MUSIC_API_URL = "http://localhost:3000"
NETEASE_CLOUD_MUSIC_API_PATH = r"./thirdparty/NeteaseCloudMusicApi"
NETEASE_CLOUD_MUSIC_SERVER_RUNNING_KEYWORD = "server running"

USER_LOCAL_STORAGE_PATH = "./local/userLocalStorage.json"
PERSONAL_UID = '1526176774'

FLASK_RUN_COMMAND = r"flask run --debug"
FLASK_CWD = "./module/application"

SONG_INFO_STORAGE_DIR = "../../local/songs/"  # "./local/songs/"  #

USER_FAV_SONG_DIR = "../../local/user/"   # 用户收藏歌曲id保存目录   # "./local/user/"  #
FAV_SONG_FILE = "fav_song.txt"  # 用户收藏歌曲id文件名

MAX_COMMENT_NUM = 100  # 单只歌曲爬取评论的最大数量
