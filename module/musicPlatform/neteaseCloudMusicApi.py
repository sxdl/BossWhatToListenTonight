"""
neteaseCloudMusicApi.py
author: Zicheng Zeng
date: 2023/4/21
description: 网易云api调用  https://github.com/Binaryify/NeteaseCloudMusicApi
"""
import time
from subprocess import PIPE, STDOUT
from module.common.const import NETEASE_CLOUD_MUSIC_API_PATH, NETEASE_CLOUD_MUSIC_SERVER_RUNNING_KEYWORD, SONG_INFO_STORAGE_DIR
from module.common.function import shell_command, timestamp, api_get, save_img, base642bytes, setItem
from threading import Thread
from module.common import fileio


class NeteaseCloudMusicProxy:
    def __init__(self):
        self.isServerOn = False

    def startup(self, cwd='..'):
        """
        启动网易云api代理
        :return:
        """
        command = "node " + NETEASE_CLOUD_MUSIC_API_PATH + "/app.js"
        shell_process = shell_command(command, cwd=cwd, stdout=PIPE, stderr=STDOUT)
        listener = Thread(target=self.shell_listener, args=(shell_process,), daemon=False)  # 监听node shell
        listener.start()
        # process, exitcode = shell_commend(command)
        # print(process, exitcode)
        while True:  # 服务启动前阻塞线程
            if not self.isServerOn:
                print('server on')
                break

    def login_qr(self):
        """
        通过二维码登录网易云账号
        :return:
        """
        print('login_qr:')
        response = api_get('/login/qr/key?timestamp=' + str(timestamp()))  # 获取二维码key
        key = response.json()['data']['unikey']
        response = api_get(f'/login/qr/create?key={key}&qrimg=true&timestamp={str(timestamp())}')  # 生成二维码
        qr_base64 = response.json()['data']['qrimg']
        save_img('', 'qrcode', 'png', base642bytes(qr_base64.split(',')[1]))
        # todo 展示二维码
        while True:  # 轮询获取二维码扫码状态
            response = api_get(f'/login/qr/check?key={key}&timestamp={str(timestamp())}').json()
            code = response['code']
            if code == '800':  # 800 为二维码过期,801 为等待扫码,802 为待确认,803 为授权登录
                print('二维码过期，请重新获取')
                break
            elif code == '803':
                print('授权登录成功')
                cookie = response['cookie']
                setItem('cookie', cookie)  # todo 保存cookie
                break
            time.sleep(0.5)

    def shell_listener(self, process):
        """
        监听shell output，如果有符合条件的输出，执行相应的操作
        :param process:
        :return:
        """
        with process.stdout:
            for line in iter(process.stdout.readline, b''):
                print(line.decode().strip())
                decode_line = line.decode().strip()
                if NETEASE_CLOUD_MUSIC_SERVER_RUNNING_KEYWORD in decode_line:
                    self.isServerOn = True
        exitcode = process.wait()
        return exitcode

    def get_user_detail(self, uid):
        """
        获取用户信息
        :param uid:用户uid
        :return:
        """
        return api_get(f'/user/detail?uid={uid}').json()

    def get_user_playlist(self, uid):
        """
        获取用户歌单
        :param uid:
        :return:
        """
        return api_get(f'/user/playlist?uid={uid}').json()['playlist']  # todo 考虑翻页问题 有没有more

    def get_playlist_id(self, playlists):
        """
        从歌单列表中获得歌单id
        :param playlists:
        :return:歌单id列表
        """
        playlist_ids = []
        for playlist in playlists:
            playlist_ids.append(playlist['id'])
        return playlist_ids

    def get_playlist_all_track(self, playlist_id):
        """
        根据歌单id获取歌单所有歌曲的id
        :param playlist_id:
        :return:歌曲id集合
        """
        song_id = set()
        track_count = api_get(f'/playlist/detail?id={playlist_id}').json()
        track_count = int(track_count['playlist']['trackCount'])
        for i in range(0, track_count, 1000):
            tracks = api_get(f'/playlist/track/all?id={playlist_id}&limit=1000&offset={i}').json()
            for song in tracks['songs']:
                song_id.update({song['id']})
        return song_id

    def get_subscribe_playlist_songs_id(self, uid):
        """
        获取用户收藏的所有歌单下的歌曲id
        :param uid:
        :return: 歌曲id集合
        """
        song_id = set()
        playlist_ids = self.get_playlist_id(self.get_user_playlist(uid))
        for playlist_id in playlist_ids:
            song_id.update(self.get_playlist_all_track(playlist_id))
        return song_id

    def get_user_record(self, uid, mode):
        """
        获取用户听歌次数排行（历史/一周）前100
        :param uid:用户uid
        :param mode:mode=1时只返回 weekData, mode=0 时返回 allData
        :return:
        """
        return api_get(f'/user/record?uid={uid}&type={mode}').json()['allData']

    def get_song_detail(self, sid: list):
        """
        根据音乐id获取歌曲详情
        :param sid:
        :return:
        """
        # print(str(sid)[1:-1].replace(" ", ""))
        details = []
        id_count = len(sid)
        for i in range(0, id_count, 1000):
            t = ",".join([str(x) for x in sid[i:min(i+1000, id_count)]])
            s = api_get(f'/song/detail?ids={t}').json()
            details.extend(s.get('songs'))
        return details

    def get_song_wiki(self, song_id):
        """
        获取音乐百科（回忆坐标/音乐百科{曲风, 推荐标签, 语种}/相似歌曲/相关歌单）
        :param song_id:
        :return:曲风、推荐标签、语种、BPM
        """
        key_list = ['melody_style', 'songBizTag', 'language', 'bpm']
        while True:
            song_wiki = api_get(f'/song/wiki/summary?id={song_id}').json()
            if song_wiki['code'] == 200:
                break
            elif song_wiki['code'] == 502:
                print("code 502! retrying...")
                time.sleep(3)
                continue
            else:
                raise Exception("Unknown Err!")
        wiki = []
        for i in range(len(song_wiki['data']['blocks'])):
            if song_wiki['data']['blocks'][i]['uiElement']['mainTitle']['title'] == '音乐百科' \
                    or song_wiki['data']['blocks'][i]['uiElement']['mainTitle']['title'] == '歌曲百科':
                wiki = song_wiki['data']['blocks'][i]['creatives']
                break

        melody_style = []  # 曲风
        try:
            for item in wiki[0]['resources']:
                melody_style.append(item['uiElement']['mainTitle']['title'])
        except TypeError:
            pass
        except IndexError:
            pass

        songBizTag = []  # 推荐标签
        try:
            for item in wiki[1]['resources']:
                songBizTag.append(item['uiElement']['mainTitle']['title'])
        except IndexError:
            pass

        language = []  # 语种
        try:
            for item in wiki[2]['uiElement']['textLinks']:
                language.append(item['text'])
        except TypeError:
            pass
        except IndexError:
            pass

        try:
            bpm = wiki[3]['uiElement']['textLinks'][0]['text']  # BPM
        except TypeError:
            bpm = None
        except IndexError:
            bpm = None

        return dict(zip(key_list, [melody_style, songBizTag, language, bpm]))

    def get_song_comments(self, song_id):
        """
        获取歌曲下方评论
        :param song_id:
        :return:
        """
        while True:
            comments = []
            try:
                test = api_get(f'/comment/music?id={song_id}').json()
                total_comments = test.get('total')
                before = int(test.get('comments')[0]['time']) + 1
                for i in range(0, total_comments, 20):
                    s = api_get(f'/comment/music?id={song_id}&limit=20&before={before}').json()
                    c = s.get('comments')
                    for cc in c:
                        user_id = cc['user']['userId']
                        comm = cc['content']
                        # comm = comm.encode('gb18030') # str(comm.encode('gb18030'))[2:-1]
                        comments.append(dict(zip(['userId', 'content'], [user_id, comm])))
                    before = c[-1]['time']
                    time.sleep(0.1)
                return comments
            except Exception as e:
                print(e)
                raise Exception("Unknown error")

    def get_json_value(self, song_id, key):
        """
        从本地加载歌曲信息，并根据key返回相应的数据
        :param song_id:
        :param key: {'ar': artist,'wiki': song_wiki,'comments': song_comments}
        :return:
        """
        song_path = f"{SONG_INFO_STORAGE_DIR}{song_id}.json"
        song_info = fileio.load_json(song_path)
        return song_info.get(key)
