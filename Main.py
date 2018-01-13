#!user/bin/env python3
# -*- coding: gbk -*-
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
import Utility.FileOperator
from Utility.Const import *
from Utility.ListFunc import ListFunc
##########################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
fileConfig('logging_config.ini')
logger = logging.getLogger()
##########################################################################


def check_tag_complete(tag):
    pass_this = True
    recording_date = tag.recording_date
    if recording_date is None:
        pass_this = pass_this * False
    else:
        logging.info("发布日期(%s)完整，跳过。" % recording_date)

    return pass_this


def get_album_details(album_info):
    logging.info("找到专辑《%s》，进入 %s 抓取" % (album_info.song_title, album_info.album_url))
    disc_total = 1
    disc = 1
    track_total = 1
    track = 1
    search_result = SearchResultCode.NOT_FOUND
    album_year = ""
    try:
        html = NetworkService.get_year_html(album_info.album_url)
        soup_album = BeautifulSoup(html, 'html.parser')
        soup_album_main_info = soup_album.find_all("div", id="album_info")[0]
        album_year_string = soup_album_main_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
        album_year = album_year_string.replace('年', '-').replace('月', '-').replace('日', '')
        logging.info("专辑发行时间为%s" % album_year_string)

        disc_total = len(soup_album.find_all("strong", class_="trackname"))
        soup_track_list = soup_album.find_all("table", class_="track_list")[0].find_all("tr")[1:]
        for tr in soup_track_list:
            if search_result != SearchResultCode.FOUND:
                if len(tr.find_all("td")) > 1:
                    title = tr.find_all("td", class_="song_name")[0].find_all('a')[0].text
                    if title.lower() == album_info.song_title.lower():
                        search_result = SearchResultCode.FOUND
                        track_total = track
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
        logging.info("专辑共有%d张碟，歌曲%s为第%d张碟的第%d首，该张碟共有%d首。" % (disc_total, album_info.song_title,
                                                             disc, track, track_total))
    except Exception as e:
        logging.warning("出现错误：%s" % e)
        raise e
    finally:
        album_info.album_date = album_year
        album_info.track_num = (track, track_total)
        album_info.disc_num = (disc, disc_total)
        return search_result


# return result, album_url, new_artist
def locate_song(soup_song_list, song_info, album_info, search_strictly=True, search_times=Const.DEFAULT_SEARCH_TIMES):
    search_result = SearchResultCode.NOT_FOUND
    try:
        for i, line in enumerate(soup_song_list[:search_times - 1]):
            song_info_web = {}
            flag = {}
            new_artist_list = []
            soup_title = line.find_all('td', class_="song_name")[0].find_all('a')
            soup_album = line.find_all('td', class_='song_album')[0].find_all('a')[0]
            song_info_web["song_title"] = soup_title[1]['title'] if soup_title[0]['title'] == "该艺人演唱的其他版本" else soup_title[0][
                'title']
            artist_str = line.find_all('td', class_='song_artist')[0].text.strip()
            artist_str = artist_str.replace('\r', '').replace('\t', '').replace('(\n', '(').replace('\n)', ')').replace('\n', ';')

            artist_for_new = line.find_all('td', class_='song_artist')[0].find_all('a')

            pattern = re.compile("(.*)\((.*)\)(.*)")
            match = pattern.match(artist_str)
            if match:
                song_info_web["album_artist"] = list(match.group(1).strip().split(";"))
                song_info_web["song_artist"] = list(match.group(2).strip().split(";"))
                for key1 in artist_for_new[1:]:
                    new_artist_list.append(key1.text)
            else:
                song_info_web["album_artist"] = [artist_str] if song_info.same_sa_and_aa() else []
                song_info_web["song_artist"] = [artist_str]
            song_info_web["album_title"] = soup_album.text.replace("《", "").replace("》", "")

            for key2 in Const.COMPARE_TAGS:
                if hasattr(song_info, key2):
                    attr = getattr(song_info, key2)
                    if isinstance(attr, list) and isinstance(song_info_web[key2], list):
                        if ListFunc.compare_2_lists(getattr(song_info, key2), song_info_web[key2]):
                            flag[key2] = 1
                    else:
                        if getattr(song_info, key2).lower() == song_info_web[key2].lower():
                            flag[key2] = 1

            count = int(i + 1)
            if search_strictly:
                if len(flag) < song_info.valid_tag_amount():
                    continue
                if len(flag) == song_info.valid_tag_amount():
                    logger.info("------第%s次匹配成功（Title、Artist和Album标签完全匹配，定位准确）" % count)
                    search_result = SearchResultCode.DONE
            else:
                if len(flag) < song_info.valid_tag_amount() - 1:
                    continue
                if len(flag) == song_info.valid_tag_amount() - 1:
                    logger.info("------第%s次匹配成功！（标签未完全匹配，请关注）" % count)
                    search_result = SearchResultCode.CHECK
                    if ("song_title" in flag) & ("album_title" in flag):
                        if ListFunc.compare_2_lists(song_info_web["album_artist"], song_info.song_artist):
                            album_info.new_song_artist.extend(new_artist_list)
                            album_info.new_album_artist.extend(song_info_web["album_artist"])
                            logger.info("------抓取到新的专辑歌手信息，同时更新。")
                            search_result = SearchResultCode.UPDATE

            album_info.album_url = soup_album['href']
            break
    except Exception as e:
        logger.warning("标签匹配发生错误：%s" % e)
        raise e
    finally:
        return search_result


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
        tag.artist = album_info.new_song_artist_str
        tag.album_artist = album_info.new_album_artist_str
    except Exception as e:
        logger.warning("写入新歌手失败：%s" % e)
        raise e
    else:
        logger.info("写入新歌手成功！")
        status_code = StatusCode.SUCCESS
    return status_code


def update_album_info(tag, album_info):
    search_result = SearchResultCode.NOT_FOUND
    try:
        if album_info.album_url != "":
            get_album_details(album_info)
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
        else:
            raise Exception
    except Exception as e:
        logger.warning("写入专辑信息错误:%s" % e)
        raise e
    else:
        search_result = SearchResultCode.DONE
    finally:
        return search_result


def update_audio_tag():
    """循环遍历MP3目录下的.mp3文件，更新歌曲标签。"""
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(Path.FILE_PATH)):
        status_code = StatusCode.SUCCESS
        search_result = SearchResultCode.NOT_FOUND
        logging.info("文件名称：'%s'。" % file_name)
        file_path = os.path.join(Path.FILE_PATH, file_name)
        try:
            audio_file = eyed3.load(file_path)
            if audio_file is None:
                raise CustomException.OpenFileError

            tag = audio_file.tag
            song_info = SongInfo(tag)
            album_info = AlbumInfo(tag)
            pass_this = False  # check_tag_complete(tag)
            if pass_this:
                logging.info("歌曲标签完整，跳过。")
                continue
            else:
                if song_info.song_artist is None:
                    search_content = file_name
                else:
                    search_content = "%s %s" % (song_info.song_artist_str(), song_info.song_title)
                if song_info.has_album_artist():
                    if not song_info.same_sa_and_aa():
                        logging.info("--专辑歌手存在，优先查找。")
                        search_content = "%s %s" % (song_info.album_artist_str(), song_info.song_title)
                        search_result = get_album_url(song_info, album_info, search_content)
                        if search_result == SearchResultCode.NOT_FOUND:
                            logging.info("--查找专辑歌手无匹配，查找歌曲歌手。")
                            search_content = "%s %s" % (song_info.song_artist_str(), song_info.song_title)
                            search_result = get_album_url(song_info, album_info, search_content)
                    else:
                        logging.info("--专辑歌手与歌曲歌手相同，查找歌曲歌手。")
                        # del song_info.album_artist
                        search_result = get_album_url(song_info, album_info, search_content)
                else:
                    logging.info("--专辑歌手不存在，查找歌曲歌手。")
                    search_result = get_album_url(song_info, album_info, search_content)

                if search_result == SearchResultCode.NOT_FOUND:
                    logger.warning("未找到曲目:%s" % search_content)
                else:
                    try:
                        if album_info.update_artists():
                            update_album_info(tag, album_info)
                            update_artists(tag, album_info)
                        else:
                            update_album_info(tag, album_info)
                    except Exception as e:
                        logger.error("标签写入错误：%s" % e)
                    else:
                        status_code = StatusCode.SUCCESS
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
                    tag.save()
                except Exception as e:
                    logger.warning("文件保存失败: %s" % e)
                finally:
                    Utility.FileOperator.FileOperator.move_file(file_name, Path.FILE_PATH, result_path)
            if status_code == StatusCode.FAILED:
                logger.error("标签更新失败，请手动处理")

            logging.info('----------------------------------------------------'
                         '-----------------------------------------------')
            sleep(2)


if "__main__" == __name__:
    logging.info('-------------------------------------------'
                 '程序开始执行-------------------------------------------')
    update_audio_tag()
    logging.info('-------------------------------------------'
                 '程序执行结束-------------------------------------------')
