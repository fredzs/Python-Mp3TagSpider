# Filename: const.py
# 定义一个常量类实现常量的功能


class Path(object):
    FILE_PATH = 'mp3/'
    MOVE_PATH = {'DONE': 'mp3/Done/', 'CHECK': 'mp3/Check/', 'NOT_FOUND': 'mp3/', 'FAILED': 'mp3/Failed'}

    KEY_TAGS = {"title", "album_artist", "song_artist", "album"}


class SearchResultCode(object):
    DONE = 'DONE'
    CHECK = 'CHECK'
    NOT_FOUND = 'NOT_FOUND'


class StatusCode:
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
