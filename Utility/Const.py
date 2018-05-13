# Filename: const.py
# 定义一个常量类实现常量的功能


class Path:
    FILE_PATH = 'mp3/'
    MOVE_PATH = {'DONE': 'mp3/Done/', 'CHECK': 'mp3/Check/', 'NOT_FOUND': 'mp3/Not_Found', 'FAILED': 'mp3/Failed',
                 'UPDATE': 'mp3/Update', 'WRONG_VERSION': 'mp3/WrongVersion'}


class SearchResultCode:
    DONE = 'DONE'
    CHECK = 'CHECK'
    NOT_FOUND = 'NOT_FOUND'
    UPDATE = "UPDATE"


class StatusCode:
    SUCCESS = 'SUCCESS'
    FAILED = 'FAILED'
    WRONG_VERSION = 'WRONG_VERSION'


class Const:
    DEFAULT_SEARCH_TIMES = 15
    COMPARE_TAGS = {"song_title", "album_artist", "song_artist", "album_title"}


class CustomException:
    OpenFileError = ("-1", "文件打开失败！")
    SaveFileError = ("-2", "文件保存失败！")


class StripTitleStr:
    STRIP_STR = {"(Album Version)", "(Single Version)", "(Main Version)", "(Studio Version)"}


class SkipArtist:
    SKIP_ARTIST = {"f(x)"}
