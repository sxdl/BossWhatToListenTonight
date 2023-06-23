"""
neteaseCloudMusicApi.py
author: Zicheng Zeng
date: 2023/4/21
description:
"""
import time
import subprocess
from requests import get
from .const import MAX_COMMENT_NUM


class NeteaseCloudMusicProxy:
    @staticmethod
    def run():
        command = r"node app/musicPlatform/NeteaseCloudMusicApi/app.js"
        subprocess.Popen(command, shell=True, close_fds=False)

    def api_get(self, api_url: str, root_url: str = "http://localhost:3000"):
        """
        发送调用api接口请求
        :param root_url:
        :param api_url:
        :return: response
        """
        while True:
            r = get(url=root_url + api_url)
            s = r.json()
            if s['code'] == 200:
                return r
            elif s['code'] == 404:
                return None
            else:
                print(f"Request Fails: {s['code']}")
                print("retrying...")
                time.sleep(2)

    def get_user_detail(self, uid):
        """
        获取用户信息
        :param uid:用户uid
        :return:
        """
        reply = self.api_get(f'/user/detail?uid={uid}')
        if reply:
            return reply.json()
        else:
            return None

    def get_user_playlist(self, uid):
        """
        获取用户歌单
        :param uid:
        :return:
        """
        return self.api_get(f'/user/playlist?uid={uid}').json()['playlist']  # todo 考虑翻页问题 有没有more

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
        track_count = self.api_get(f'/playlist/detail?id={playlist_id}').json()
        track_count = int(track_count['playlist']['trackCount'])
        for i in range(0, track_count, 1000):
            tracks = self.api_get(f'/playlist/track/all?id={playlist_id}&limit=1000&offset={i}').json()
            for song in tracks['songs']:
                song_id.update({song['id']})
        return song_id

    def get_subscribe_playlist_songs_id(self, uid, fav_only=False):
        """
        获取用户收藏的所有歌单下的歌曲id
        :param fav_only:
        :param uid:
        :return: 歌曲id集合
        """
        song_id = set()
        playlist_ids = self.get_playlist_id(self.get_user_playlist(uid))
        if fav_only:
            song_id.update(self.get_playlist_all_track(playlist_ids[0]))
        else:
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
        if mode == 0:
            return self.api_get(f'/user/record?uid={uid}&type={mode}').json()['allData']
        elif mode == 1:
            return self.api_get(f'/user/record?uid={uid}&type={mode}').json()['weekData']

    def get_song_detail(self, sid: list):
        """
        根据音乐id获取歌曲详情（如果歌手无id，id为0）
        :param sid:
        :return:
        """
        # print(str(sid)[1:-1].replace(" ", ""))
        details = []
        id_count = len(sid)
        for i in range(0, id_count, 1000):
            t = ",".join([str(x) for x in sid[i:min(i+1000, id_count)]])
            s = self.api_get(f'/song/detail?ids={t}').json()
            details.extend(s.get('songs'))
        return details


    def get_artist_detail(self, aid):
        """
        根据歌手id获取歌手详情，返回（id, name, 头像url）
        :param aid: 歌手id
        :return: (id, name, 头像url)
        """
        details = self.api_get(f'/artist/detail?id={aid}').json()
        artist_details = details['data']['artist']
        return artist_details['id'], artist_details['name'], artist_details['avatar']


    def get_song_wiki(self, song_id):
        """
        获取音乐百科（回忆坐标/音乐百科{曲风, 推荐标签, 语种}/相似歌曲/相关歌单）
        :param song_id:
        :return:曲风、推荐标签、语种、BPM
        """
        key_list = ['melody_style', 'songBizTag', 'language', 'bpm']
        while True:
            song_wiki = self.api_get(f'/song/wiki/summary?id={song_id}').json()
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
        bpm = None
        try:
            for item in wiki[2]['uiElement']['textLinks']:
                try:
                    bpm = int(item['text'])
                except:
                    # language.append(item['text'])
                    language.extend(item['text'].split('、'))  # "日语、英语"
                    bpm = None
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
                test = self.api_get(f'/comment/music?id={song_id}').json()
                total_comments = min(test.get('total'), MAX_COMMENT_NUM)
                if not test.get('comments'):
                    return comments
                before = int(test.get('comments')[0]['time']) + 1
                for i in range(0, total_comments, 20):
                    s = self.api_get(f'/comment/music?id={song_id}&limit=20&before={before}').json()
                    c = s.get('comments')
                    for cc in c:
                        user_id = cc['user']['userId']
                        comm = cc['content']
                        timestr = cc['time']
                        # comm = comm.encode('gb18030') # str(comm.encode('gb18030'))[2:-1]
                        comments.append(dict(zip(['userId', 'content', 'time'], [user_id, comm, timestr])))
                    before = c[-1]['time']
                    time.sleep(0.1)
                return comments
            except Exception as e:
                print(e)
                raise Exception("Unknown error")

    def get_related_playlist(self, playlist_id):
        """
        传入歌单id获取相关歌单
        :param playlist_id:
        :return: {'name', 'id', 'coverImgUrl', 'creator': {'userId', 'nickname'}}
        """
        replay_json = self.api_get(f'/related/playlist?id={playlist_id}').json()
        related_playlists = replay_json['playlists']
        return related_playlists

    def get_user_liked_playlist_id(self, uid):
        """
        传入用户uid获取用户喜欢的音乐歌单id
        :param uid:
        :return:
        """
        return self.get_user_playlist(uid)[0]['id']
