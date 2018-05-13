#!user/bin/env python3

import logging
import re
import warnings
from logging.config import fileConfig
from time import sleep

import eyed3
import os
from bs4 import BeautifulSoup

from Entity.SongInfo import SongInfo
from Entity.AlbumInfo import AlbumInfo
from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService
from Utility.FileOperator import FileOperator
from Entity.Statistic import Statistic
from Utility.Const import *
from Utility.ListFunc import ListFunc

##########################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
fileConfig('logging_config.ini')

logging.getLogger("eyed3.mp3.headers").setLevel(logging.CRITICAL)
logging.getLogger("eyed3").setLevel(logging.CRITICAL)
logger = logging.getLogger()
##########################################################################


def print_search_progress(flag, song_info, song_info_web):
    logger.info("flag: %s" % flag.keys())
    for key in Const.COMPARE_TAGS:
        if key not in flag:
            attr = getattr(song_info, key)
            # if isinstance(attr, list) and isinstance(song_info_web[key], list):
            try:
                logger.info("%15s: `%s`" % (key, attr))
            except UnicodeEncodeError as e:
                logger.info("%15s:" % key)
            logger.info("%11s_web: `%s`" % (key, song_info_web[key]))


def check_tag_complete(tag):
    pass_this = True
    recording_date = tag.recording_date
    if recording_date is None:
        pass_this = pass_this * False
    else:
        logger.info("发布日期(%s)完整，跳过。" % recording_date)

    return pass_this


def get_album_details(album_info, song_info):
    try:
        logger.info("找到专辑《%s》，进入 %s 抓取" % (album_info.album_title, album_info.album_url))
    except UnicodeEncodeError as e:
        logger.info("找到专辑，进入 %s 抓取" % album_info.album_url)

    disc_total = 1
    disc = 1
    track_total = 1
    track = 1
    found = False
    album_year = ""
    subtitle = ""
    try:
        html = NetworkService.get_year_html(album_info.album_url)
        soup_album = BeautifulSoup(html, 'html.parser')
        soup_album_main_info = soup_album.find_all("div", id="album_info")[0]
        album_year_string = soup_album_main_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
        album_year = album_year_string.replace('年', '-').replace('月', '-').replace('日', '')
        logger.info("专辑发行时间为%s" % album_year_string)

        disc_total = len(soup_album.find_all("strong", class_="trackname"))
        soup_track_list = soup_album.find_all("table", class_="track_list")[0].find_all("tr")[1:]
        for tr in soup_track_list:
            if not found:
                if len(tr.find_all("td")) > 1:
                    title = tr.find_all("td", class_="song_name")[0].find_all('a')[0].text
                    if title.lower() == album_info.song_title.lower():
                        found = True
                        track_total = track
                        # 处理中文副标题
                        soup_show_title = tr.find_all("td", class_="song_name")[0].find_all("a", class_="show_zhcn")
                        if len(soup_show_title) > 0:
                            subtitle = soup_show_title[0].text
                    else:
                        track += 1
                else:
                    disc += 1
                    track = 1
            else:
                if len(tr.find_all("td")) > 1:
                    track_total += 1
                else:
                    break
        logger.info("专辑共有%d张碟，歌曲%s为第%d张碟的第%d首，该张碟共有%d首。" % (disc_total, album_info.song_title,
                                                            disc, track, track_total))
    except Exception as e:
        logger.warning("出现错误：%s" % e)
        raise e
    finally:
        album_info.album_date = album_year
        album_info.track_num = (track, track_total)
        album_info.disc_num = (disc, disc_total)
        song_info.new_song_title = subtitle


# return result, album_url, new_artist
def locate_song(soup_song_list, song_info, album_info, search_strictly=True, search_times=Const.DEFAULT_SEARCH_TIMES):
    search_result = SearchResultCode.NOT_FOUND
    try:
        for i, line in enumerate(soup_song_list[:search_times - 1]):
            song_info_web = {}
            flag = {}
            new_artist_list = []
            soup_title = line.find_all('td', class_="song_name")[0].find_all('a')
            song_info_web["song_title"] = get_song_title_web(soup_title)
            soup_album = line.find_all('td', class_='song_album')[0].find_all('a')[0]
            song_info_web["album_title"] = soup_album.text.replace("《", "").replace("》", "").strip()
            artist_str = line.find_all('td', class_='song_artist')[0].text.strip()
            artist_str = artist_str.replace('\r', '').replace('\t', '').replace('(\n', '(').replace('\n)', ')').replace(
                '\n', ';')

            artist_for_new = line.find_all('td', class_='song_artist')[0].find_all('a')

            # 判断是否有多个song_artist
            pattern = re.compile("(.*)\((.*)\)(.*)")
            match = pattern.match(artist_str)
            if match:
                song_info_web["album_artist"] = list(match.group(1).strip().split(";"))
                song_info_web["song_artist"] = list(match.group(2).strip().split(";"))
                for key1 in artist_for_new[1:]:
                    new_artist_list.append(key1.text)
            if (not match) or (artist_str in SkipArtist.SKIP_ARTIST):
                song_info_web["album_artist"] = []
                song_info_web["song_artist"] = [artist_str]

            # 1.匹配搜索结果
            for key2 in Const.COMPARE_TAGS:
                if hasattr(song_info, key2):
                    attr = getattr(song_info, key2)
                    if isinstance(attr, list) and isinstance(song_info_web[key2], list):
                        if ListFunc.compare_2_lists(getattr(song_info, key2), song_info_web[key2]):
                            flag[key2] = 1
                    else:
                        if getattr(song_info, key2).lower() == song_info_web[key2].lower():
                            flag[key2] = 1

            # 判断是否需要更新album_artist
            if (song_info_web["album_artist"] == []) & (song_info.same_sa_and_aa()):
                flag["album_artist"] = 1
                album_info.update_artists = True

            # 2.分析搜索结果
            search_result = analyse_search_result(search_strictly, song_info_web, song_info, flag, album_info, new_artist_list, i + 1)

            if search_result == SearchResultCode.NOT_FOUND:
                continue
            else:
                # 这里有坑，反爬虫，注意url是否完整。
                album_info.album_url = "{}{}".format("http:", soup_album['href'])
                break
    except Exception as e:
        logger.warning("标签匹配发生错误：%s" % e)
        raise e
    finally:
        return search_result


def analyse_search_result(search_strictly, song_info_web, song_info, flag, album_info, new_artist_list, count):
    """分析搜索结果，判断最终状态"""
    search_result = SearchResultCode.NOT_FOUND
    if search_strictly:
        len_song_info_web = len(song_info_web) if len(song_info_web["album_artist"]) > 0 else len(song_info_web) - 1
        if len_song_info_web == len(flag) == song_info.valid_tag_amount():
            logger.info("------第%s次匹配成功（Title、Artist和Album标签完全匹配，定位准确）" % count)
            search_result = SearchResultCode.DONE
        elif len_song_info_web > len(flag) == song_info.valid_tag_amount():
            if ("song_title" in flag) & ("album_title" in flag):
                if ListFunc.compare_2_lists(song_info_web["song_artist"], song_info.song_artist):
                    album_info.new_album_artist.extend(song_info_web["album_artist"])
                    album_info.update_album_artists = True
                    logger.info("------抓取到新的专辑歌手信息，同时更新。")
                    search_result = SearchResultCode.UPDATE
        elif len_song_info_web == song_info.valid_tag_amount() > len(flag):
            if ("song_title" in flag) & ("album_title" in flag) & ("album_artist" in flag):
                album_info.new_song_artist.extend(new_artist_list)
                album_info.update_song_artists = True
                logger.info("------抓取到新的歌手信息，同时更新。")
                search_result = SearchResultCode.UPDATE
        elif len_song_info_web < song_info.valid_tag_amount() == len(flag):
            if ("song_title" in flag) & ("album_title" in flag) & ("song_artist" in flag):
                album_info.new_album_artist.extend(song_info_web["album_artist"])
                album_info.update_album_artists = True
                logger.info("------抓取到新的歌手信息，同时更新。")
                search_result = SearchResultCode.UPDATE
        else:
            pass
    else:
        if len(flag) < song_info.valid_tag_amount() - 1:
            pass
        if len(flag) == song_info.valid_tag_amount() - 1:
            logger.info("------第%s次匹配成功！（标签未完全匹配，请关注）" % count)
            print_search_progress(flag, song_info, song_info_web)
            search_result = SearchResultCode.CHECK

    return search_result


def get_song_title_web(soup_title):
    if soup_title[0]['title'] == "该艺人演唱的其他版本":
        song_title_web = soup_title[1]['title'].strip()
    else:
        song_title_web = soup_title[0]['title'].strip()
        for strip_str in StripTitleStr.STRIP_STR:
            song_title_web.replace(strip_str, '')
        song_title_web = song_title_web.strip()

    return song_title_web


# return soup_song_list
def locate_song_list(search_content):
    r = NetworkService.get_song_info_html(search_content)
    soup = BeautifulSoup(r, 'html.parser')
    song_section_soup = soup.find_all('table', class_='track_list')
    if len(song_section_soup) == 0:
        return None
    soup_song_list = song_section_soup[0].find_all('tr')[1:]
    return soup_song_list


# return album_url, new_artist
def get_album_url(song_info, album_info, search_content):
    search_result = SearchResultCode.NOT_FOUND
    soup_song_list = locate_song_list(search_content)
    if soup_song_list is not None:
        logger.info("----严格模式启用。")
        search_result = locate_song(soup_song_list, song_info, album_info)
        if search_result == SearchResultCode.NOT_FOUND:
            logger.info("----严格模式未找到歌曲，尝试模糊查询。")
            search_result = locate_song(soup_song_list, song_info, album_info, False)
        if search_result == SearchResultCode.NOT_FOUND:
            logger.info("----模糊查询未找到歌曲。")
    return search_result


def update_artists(tag, album_info):
    status_code = StatusCode.FAILED
    try:
        if album_info.update_song_artists:
            logger.info("旧歌手：%s。" % tag.artist)
            logger.info("新歌手：%s。" % album_info.new_song_artist_str)
            tag.artist = album_info.new_song_artist_str
            logger.info("写入新歌手成功！")
        if album_info.update_album_artists:
            logger.info("旧专辑歌手：%s。" % tag.album_artist)
            logger.info("新专辑歌手：%s。" % album_info.new_album_artist_str)
            tag.album_artist = album_info.new_album_artist_str
            logger.info("写入新专辑歌手成功！")
        status_code = StatusCode.SUCCESS
    except Exception as e:
        logger.warning("写入新歌手失败：%s" % e)
    return status_code


def update_album_info(tag, album_info, song_info):
    status_code = StatusCode.FAILED
    try:
        if album_info.album_url != "":
            get_album_details(album_info, song_info)
            song_date = album_info.album_date
            date = eyed3.core.Date(song_date.year, song_date.month, song_date.day)
            tag.recording_date = date
            if tag.recording_date.month is None:
                raise Exception
            else:
                logger.info("写入日期(%s)成功。" % tag.recording_date)

            tag.track_num = album_info.track_num
            tag.disc_num = album_info.disc_num
            logger.info("写入音轨序号成功。")

            if song_info.new_song_title != "":
                tag.setTextFrame(b'TIT3', song_info.new_song_title)
                logger.info("写入副标题(%s)成功。"% song_info.new_song_title)
        else:
            raise Exception
    except Exception as e:
        logger.warning("写入专辑信息错误:%s" % e)
    else:
        status_code = StatusCode.SUCCESS
    finally:
        return status_code


def make_search_content(song_info, album_artist=True):
    if album_artist:
        search_content = "%s - %s - %s" % (song_info.album_artist_str(), song_info.song_artist_str(), song_info.song_title)
    else:
        if song_info.song_artist == [] and song_info.album_artist == []:
            search_content = "%s %s" % (song_info.album_title, song_info.song_title)
        elif song_info.song_artist is []:
            search_content = "%s %s" % (song_info.album_artist_str(), song_info.song_title)
        else:
            search_content = "%s %s" % (song_info.song_artist_str(), song_info.song_title)

    return search_content


def update_audio_tag():
    """循环遍历MP3目录下的.mp3文件，更新歌曲标签。"""
    statistic = Statistic()
    file_list = list(filter(lambda x: x.endswith(".mp3") | x.endswith(".MP3"), os.listdir(Path.FILE_PATH)))
    for i, file_name in enumerate(file_list):
        status_code = StatusCode.SUCCESS
        search_result = SearchResultCode.NOT_FOUND
        logger.info("(%s/%s)文件名称：'%s'。" % (str(i + 1), len(file_list), file_name))
        file_path = os.path.join(Path.FILE_PATH, file_name)
        try:
            audio_file = eyed3.load(file_path)
            if audio_file is None:
                raise CustomException.OpenFileError

            tag = audio_file.tag
            if tag.title is None:
                logger.warning("Title缺失，跳过！")
                status_code = StatusCode.FAILED
                continue
            if tag.album is None:
                logger.warning("Album_title缺失，跳过！")
                status_code = StatusCode.FAILED
                continue
            if tag.version != (1, 1, 0):
                song_info = SongInfo(tag)
                album_info = AlbumInfo(tag)
                pass_this = False  # check_tag_complete(tag)
                if pass_this:
                    logger.info("歌曲标签完整，跳过。")
                    continue
                else:
                    if song_info.has_album_artist():
                        if not song_info.same_sa_and_aa():
                            logger.info("--专辑歌手存在，优先查找。")
                            search_content = make_search_content(song_info)
                            search_result = get_album_url(song_info, album_info, search_content)
                            if search_result == SearchResultCode.NOT_FOUND:
                                logger.info("--查找专辑歌手无匹配，查找歌曲歌手。")
                                search_content = make_search_content(song_info, False)
                                search_result = get_album_url(song_info, album_info, search_content)
                        else:
                            logger.info("--专辑歌手与歌曲歌手相同，查找歌曲歌手。")
                            search_content = make_search_content(song_info, False)
                            search_result = get_album_url(song_info, album_info, search_content)
                    else:
                        logger.info("--专辑歌手不存在，查找歌曲歌手。")
                        search_content = make_search_content(song_info, False)
                        search_result = get_album_url(song_info, album_info, search_content)

                    if search_result == SearchResultCode.NOT_FOUND:
                        logger.warning("未找到曲目:%s" % search_content)
                    elif search_result == SearchResultCode.CHECK:
                        pass
                    else:
                        if update_artists(tag, album_info) == StatusCode.SUCCESS:
                            if update_album_info(tag, album_info, song_info) == StatusCode.SUCCESS:
                                status_code = StatusCode.SUCCESS
                            else:
                                status_code = StatusCode.FAILED
                        else:
                            status_code = StatusCode.FAILED
            else:
                status_code = StatusCode.WRONG_VERSION
        except CustomException.OpenFileError:
            logger.error("打开文件失败！")
            status_code = StatusCode.FAILED
        except Exception as e:
            logger.error(e)
            status_code = StatusCode.FAILED
        finally:
            if status_code == StatusCode.SUCCESS:
                result_path = Path.MOVE_PATH.get(search_result)
                try:
                    tag.save(encoding='utf-8', preserve_file_time=True)
                except Exception as e:
                    logger.warning("文件保存失败: %s" % e)
                finally:
                    FileOperator.move_file(file_name, Path.FILE_PATH, result_path)
                    statistic.set_search_result(search_result)
            else:
                if status_code == StatusCode.WRONG_VERSION:
                    result_path = Path.MOVE_PATH.get(status_code)
                    FileOperator.move_file(file_name, Path.FILE_PATH, result_path)
                    logger.error("标签更新失败，请手动处理")
                elif status_code == StatusCode.FAILED:
                    result_path = Path.MOVE_PATH.get(status_code)
                    FileOperator.move_file(file_name, Path.FILE_PATH, result_path)
                    logger.error("标签更新失败，请手动处理")
                statistic.set_search_result("FAILED")

            logger.info('----------------------------------------------------'
                        '-----------------------------------------------')
            sleep(2)
    logger.info("程序共整理文件%d个，其中：" % statistic.get_sum())
    for key in ['DONE', "UPDATE", 'CHECK', 'NOT_FOUND', 'FAILED']:
        logger.info("%s %d个" % (key, statistic.get_search_result(key)))


if "__main__" == __name__:
    logger.info('-------------------------------------------'
                '程序开始执行-------------------------------------------')
    NetworkService.str_2_cookies()
    update_audio_tag()
    logger.info('-------------------------------------------'
                '程序执行结束-------------------------------------------')
