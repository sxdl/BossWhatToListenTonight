"""
test.py.py
author: sxdl
date: 2023/4/21
description: script for test only
"""
import os
import time
from module.common import const
import signal
from module.common import function
from module.application import server
from module.common.const import FLASK_CWD, FLASK_RUN_COMMAND

cwd = os.getcwd()
os.chdir("./module/application/")
from module.statistics import statistics
os.chdir(cwd)

# # server.join()
#
# ncm = NeteaseCloudMusicProxy()
# ncm.startup()
# # ncm.login_qr()
# playlist = ncm.get_song_wiki('1396905934')
# print(playlist)


def test_fav_art(uid):
    # fav_songs = statistics.get_user_fav_song(uid, reload=False)
    statistics.spider_song_info(uid)
    time.sleep(3)


if __name__ == "__main__":
    # flask_server = server.WebServer(FLASK_RUN_COMMAND, FLASK_CWD)
    # flask_server.run()
    #
    time.sleep(5)

    test_fav_art("1526176774")

    time.sleep(300)
    # flask_server.stop()


