#!user/bin/env python3
# -*- coding: gbk -*-
import os
import shutil
import logging
from logging.config import fileConfig
import warnings
import eyed3
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep
from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService

##########################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
fileConfig('logging_config.ini')
logger = logging.getLogger()
##########################################################################
FILE_PATH = 'mp3/'
DONE_PATH = 'mp3/Done/'


def check_tag_complete(tag):
    pass_this = False
    recording_date = tag.recording_date
    if recording_date is not None:
        logging.info("发布日期(%s)完整，跳过。" % recording_date)
        pass_this = True

    return pass_this


def get_album_details(song_title, song_album, album_url):
    logging.info("找到专辑《%s》，进入 %s 抓取" % (song_album, album_url))
    album_year = "1950-12-31"
    disc_total = 1
    disc = 1
    track_total = 1
    track = 1
    found = False
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


def locate_line(tag, file_name, search_song_artist=False, update_album=False):
    song_artist = tag.artist.replace(chr(0), ' ')
    album_artist = tag.album_artist
    song_title = tag.title
    song_album = tag.album
    album_url = ""
    found = False
    if search_song_artist:
        search_content = "%s %s" % (song_artist, song_title)
        artist_compare = song_artist
    else:
        if (album_artist is not None) & (song_title is not None):
            search_content = "%s %s" % (album_artist, song_title)
        else:
            search_content = file_name
        artist_compare = album_artist

    try:
        r = NetworkService.get_song_info_html(search_content)
        soup = BeautifulSoup(r, 'html.parser')
        song_section_soup = soup.find_all('table', class_='track_list')
        if len(song_section_soup) > 0:
            song_name_soup_list = song_section_soup[0].find_all('tr')[1:]

            for item in song_name_soup_list[:9]:
                song_artist_from_web = ""
                album_artist_from_web = ""
                artist_group_from_web = ""
                soup_title = item.find_all('td', class_="song_name")[0].find_all('a')
                if soup_title[0]['title'] == "该艺人演唱的其他版本":
                    song_title_from_web = soup_title[1]['title']
                else:
                    song_title_from_web = soup_title[0]['title']

                soup_artist = item.find_all('td', class_='song_artist')[0].find_all('a')
                if len(soup_artist) > 1 & (album_artist != song_artist):
                    album_artist_from_web = soup_artist[0]['title']
                    for artist in soup_artist[1:]:
                        song_artist_from_web = "%s %s" % (song_artist_from_web, artist.text)
                    if song_artist_from_web[0] == " ":
                        song_artist_from_web = song_artist_from_web[1:]
                    song_artist_from_web = song_artist_from_web.replace(";", " ")
                    artist_group = '%s ( %s )' % (album_artist, song_artist)
                else:
                    artist_group_from_web = soup_artist[0].text.strip().replace(";", " ")
                    artist_group = song_artist

                song_album_from_web = item.find_all('td', class_='song_album')[0].find_all('a')[0].text \
                    .replace("《", "").replace("》", "")

                flag = {}
                publisher = ""
                if song_title_from_web.lower() == song_title.lower():
                    flag["title"] = 1
                if artist_group_from_web.lower() == artist_group.lower():
                    flag["artist_album_artist"] = 1
                if song_artist_from_web.lower() == song_artist.lower():
                    flag["artist"] = 1
                if song_album_from_web.lower() == song_album.lower():
                    flag["album"] = 1

                if len(flag) < 3:
                    continue
                if len(flag) == 4:
                    logger.info("Title、Artist和Album标签完全匹配，定位准确。")
                elif len(flag) >= 3:
                    if "title" not in flag:
                        logger.warning("Title未完全匹配，请手动处理。")
                        publisher += "Title "
                    if ("artist_album_artist" not in flag) & ("artist" not in flag):
                        logger.warning("Artist未完全匹配，请手动处理。")
                        publisher += "Artist Album_artist"
                    if ("artist_album_artist" not in flag) & ("artist" in flag):
                        if "album" in flag:
                            logger.warning("Artist未完全匹配，但Album_artist匹配，自动更新。")
                            logger.info("写入Album_artist：%s。" % album_artist_from_web)
                            tag.album_artist = album_artist_from_web
                            publisher += "NewArtist "
                        else:
                            logger.warning("Artist未完全匹配，请手动处理。")
                            publisher += "Artist "
                    if "album" not in flag:
                        if update_album:
                            logger.warning("Album未完全匹配，自动更新。")
                            tag.album = song_album_from_web
                            logger.info("旧Album：%s；新Album：%s。" % (song_album, song_album_from_web))
                            publisher += "NewAlbum "
                        else:
                            logger.warning("Album未完全匹配，请手动处理。")
                            publisher += "Album "

                    tag.publisher = publisher
                    # if song_artist == "":
                    #     tag.album_artist = album_artist_from_web
                    #     tag.artist = song_artist_from_web
                    # if song_title == "":
                    #     tag.title = song_title_from_web
                    # if song_album == "":
                    #     tag.album = song_album_from_web

                album_url = item.find_all('td', class_='song_album')[0].find_all('a')[0]['href']
                found = True
                break

            if not found:
                # raise Exception
                logger.warning("未找到歌曲")
    except Exception as e:
        logger.warning("警告:%s" % e)
    finally:
        return album_url


def update_album_info(tag, album_url):
    result = False
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
                result = True

            tag.track_num = (disc_and_track["track"], disc_and_track["track_total"])
            tag.disc_num = (disc_and_track["disc"], disc_and_track["disc_total"])
            logger.info("写入音轨序号成功。")
        else:
            raise Exception
    except Exception as e:
        logger.warning("写入专辑信息错误:%s" % e)
    finally:
        return result


def update_audio_tag():
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(FILE_PATH)):
        success = False
        logging.info("文件名称：'%s'。" % file_name)
        file_path = os.path.join(FILE_PATH, file_name)
        try:
            audio_file = eyed3.load(file_path)
            if audio_file is None:
                raise IOError

            tag = audio_file.tag
            pass_this = check_tag_complete(tag)
            if pass_this:
                logging.info("歌曲标签完整，跳过。")
                continue
            else:
                if tag.album_artist is not None:
                    album_url = locate_line(tag, file_name)
                    if album_url == "":
                        album_url = locate_line(tag, file_name, True)
                else:
                    album_url = locate_line(tag, file_name, True)
                success = update_album_info(tag, album_url)
        except IOError:
            logger.warning("打开文件失败！")
        finally:
            if success:
                tag.save()
                # version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')
                shutil.move(os.path.join(FILE_PATH, file_name), os.path.join(DONE_PATH, file_name))
                logger.info("标签写入完毕，文件移动至子目录下。")

            logger.info("当前文件'%s'处理完毕。" % file_name)
            logging.info('----------------------------------------------------'
                         '-----------------------------------------------')
            sleep(2)


if "__main__" == __name__:
    if not os.path.exists(DONE_PATH):
        os.makedirs(DONE_PATH)

    logging.info('-------------------------------------------'
                 '程序开始执行-------------------------------------------')
    update_audio_tag()
    logging.info('-------------------------------------------'
                 '程序执行结束-------------------------------------------')
