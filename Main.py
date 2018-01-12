#!user/bin/env python3
# -*- coding: gbk -*-
import logging
import re
import warnings
from datetime import datetime
from logging.config import fileConfig
from time import sleep

import eyed3
import os
from bs4 import BeautifulSoup

from Entity.SongInfo import SongInfo
from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService
from Utility import FileOperator
from Utility.Const import *
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


def get_album_details(song_title, song_album, album_url):
    logging.info("找到专辑《%s》，进入 %s 抓取" % (song_album, album_url))
    disc_total = 1
    disc = 1
    track_total = 1
    track = 1
    found = False
    album_year = ""
    try:
        html = NetworkService.get_year_html(album_url)
        soup_album = BeautifulSoup(html, 'html.parser')
        soup_album_main_info = soup_album.find_all("div", id="album_info")[0]
        album_year_string = soup_album_main_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
        album_year = album_year_string.replace('年', '-').replace('月', '-').replace('日', '')
        logging.info("专辑发行时间为%s" % album_year)

        disc_total = len(soup_album.find_all("strong", class_="trackname"))
        soup_track_list = soup_album.find_all("table", class_="track_list")[0].find_all("tr")[1:]
        for tr in soup_track_list:
            if not found:
                if len(tr.find_all("td")) > 1:
                    title = tr.find_all("td", class_="song_name")[0].find_all('a')[0].text
                    if title.lower() == song_title.lower():
                        found = True
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
        logging.info("专辑共有%d张碟，歌曲%s为第%d张碟的第%d首，该张碟共有%d首。" % (disc_total, song_title,
                                                             disc, track, track_total))
    except Exception as e:
        logging.warning("出现错误：%s" % e)
    finally:
        disc_and_track = {"disc": disc, "disc_total": disc_total, "track": track, "track_total": track_total}
        return album_year, disc_and_track


# return result, album_url, new_artist
def locate_song(soup_song_list, song_info, search_strictly=True, search_times=Const.DEFAULT_SEARCH_TIMES):
    result = Path.NOT_FOUND
    album_url = ""
    new_artist = {}
    for i, line in enumerate(soup_song_list[:search_times - 1]):
        song_info_web = {}
        flag = {}
        new_artist_str = ""
        soup_title = line.find_all('td', class_="song_name")[0].find_all('a')
        soup_album = line.find_all('td', class_='song_album')[0].find_all('a')[0]
        song_info_web["title"] = soup_title[1]['title'] if soup_title[0]['title'] == "该艺人演唱的其他版本" else soup_title[0][
            'title']
        artist_str = line.find_all('td', class_='song_artist')[0].text.replace("\t", "").replace("\n", " ").replace(
            "\r", "").strip()
        artist_for_new = line.find_all('td', class_='song_artist')[0].find_all('a')

        pattern = re.compile("(.*)\((.*)\)(.*)")
        match = pattern.match(artist_str)
        if match:
            song_info_web["album_artist"] = match.group(1).strip()
            song_info_web["song_artist"] = match.group(2).strip().replace(";", " ")
            for key in artist_for_new[1:]:
                new_artist_str = new_artist_str + key.text + "; "
            if new_artist_str.endswith("; "):
                new_artist_str = new_artist_str[:-2]
        else:
            song_info_web["album_artist"] = ""
            song_info_web["song_artist"] = artist_str
        song_info_web["album"] = soup_album.text.replace("《", "").replace("》", "")

        for key in Const.KEY_TAGS:
            if key in song_info:
                if song_info_web[key].lower() == song_info[key].lower():
                    flag[key] = 1

        count = int(i + 1)
        if search_strictly:
            if len(flag) < len(song_info):
                continue
            if len(flag) == len(song_info):
                logger.info("------第%s次匹配成功（Title、Artist和Album标签完全匹配，定位准确）" % count)
                result = Const.DONE
        else:
            if len(flag) < len(song_info) - 1:
                continue
            if len(flag) == len(song_info) - 1:
                logger.info("------第%s次匹配成功！（标签未完全匹配，请关注）" % count)
                result = Const.CHECK
                if ("title" in flag) & ("album" in flag):
                    if song_info_web["album_artist"].lower() == song_info["song_artist"].lower():
                        new_artist['new_song_artist'] = new_artist_str
                        new_artist['new_album_artist'] = song_info_web["album_artist"]
                        logger.info("------抓取到新的专辑歌手信息，同时更新。")

        album_url = soup_album['href']
        break

    return result, album_url, new_artist


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
def get_album_url(song_info, search_content):
    soup_song_list = locate_song_list(search_content)
    if soup_song_list is None:
        return Const.NOT_FOUND, ""

    song_info = {"title": tag.title, "song_artist": tag.artist.replace(chr(0), ' ')}
    if has_album_artist:
        song_info["album_artist"] = tag.album_artist.replace(chr(0), ' ')
    if tag.album is not None:
        song_info["album"] = tag.album
    logger.info("----严格模式启用。")
    result, album_url, new_artist = locate_song(soup_song_list, song_info)
    if result == 'NOT_FOUND':
        logger.info("----严格模式未找到歌曲，尝试模糊查询。")
        result, album_url, new_artist = locate_song(soup_song_list, song_info, False)
    if result == 'NOT_FOUND':
        logger.info("----模糊查询未找到歌曲。")
    return album_url, new_artist


def update_song_info(tag, new_artist):
    result = False
    if len(new_artist) > 0:
        try:
            tag.artist = new_artist["new_song_artist"]
            tag.album_artist = new_artist["new_album_artist"]
        except Exception as e:
            logger.warning("写入新歌手失败：%s" % e)
        else:
            logger.info("写入新歌手成功！")
            result = True
    return result


def update_album_info(tag, album_url):
    result = 'NOT_FOUND'
    try:
        if album_url != "":
            year_str, disc_and_track = get_album_details(tag.title, tag.album, album_url)
            song_year = datetime.strptime(year_str, "%Y-%m-%d")
            date = eyed3.core.Date(song_year.year, song_year.month, song_year.day)
            tag.recording_date = date
            if tag.recording_date.month is None:
                raise Exception
            else:
                logger.info("写入日期(%s)成功。" % tag.recording_date)
                result = 'DONE'

            tag.track_num = (disc_and_track["track"], disc_and_track["track_total"])
            tag.disc_num = (disc_and_track["disc"], disc_and_track["disc_total"])
            logger.info("写入音轨序号成功。")
        else:
            raise Exception
    except Exception as e:
        logger.warning("写入专辑信息错误:%s" % e)
    finally:
        return result


# ----------------------------------------------------------------------------------#


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
            pass_this = False  # check_tag_complete(tag)
            if pass_this:
                logging.info("歌曲标签完整，跳过。")
                continue
            else:
                if song_info.song_artist is None:
                    search_content = file_name
                else:
                    search_content = "%s %s" % (song_info.song_artist, song_info.song_title)
                if song_info.has_album_artist():
                    if song_info.same_sa_and_aa():
                        logging.info("--专辑歌手存在，优先查找。")
                        search_content = "%s %s" % (song_info.album_artist, song_info.title)
                        search_result = get_album_url(song_info, search_content)
                        if search_result == SearchResultCode.NOT_FOUND:
                            logging.info("--查找专辑歌手无匹配，查找歌曲歌手。")
                            search_content = "%s %s" % (song_info.artist, song_info.title)
                            search_result = get_album_url(song_info, search_content)
                    else:
                        logging.info("--专辑歌手与歌曲歌手相同，查找歌曲歌手。")
                        search_result = get_album_url(song_info, search_content)
                else:
                    logging.info("--专辑歌手不存在，查找歌曲歌手。")
                    search_result = get_album_url(song_info, search_content)

                if search_result == SearchResultCode.NOT_FOUND:
                    logger.warning("未找到曲目:%s" % search_content)
                elif song_info.update_song_info():
                    result = update_album_info(tag, song_info) & update_song_info(tag, song_info)
                else:
                    result = update_album_info(tag, song_info)

        except CustomException.OpenFileError:
            logger.error("打开文件失败！")
            result_path = StatusCode.FAILED
        except Exception as e:
            logger.error(e)
        finally:
            result_path = Path.MOVE_PATH.get(status_code)
            if search_result == StatusCode.SUCCESS:
                try:
                    tag.save()
                except Exception as e:
                    logger.warning("文件保存失败: %s" % e)
                finally:
                    FileOperator.move_file(file_name, Path.FILE_PATH, result_path)
            if search_result == StatusCode.FAILED:
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
