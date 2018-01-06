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


def get_album_details(song_title, song_album, album_url):
    logging.info("找到专辑《%s》，进入 %s 抓取" % (song_album, album_url))
    html = NetworkService.get_year_html(album_url)
    soup_album = BeautifulSoup(html, 'html.parser')
    soup_album_main_info = soup_album.find_all("div", id="album_info")[0]
    album_year_string = soup_album_main_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
    album_year = album_year_string.replace('年', '-').replace('月', '-').replace('日', '')
    logging.info("专辑发行时间为%s" % album_year)

    soup_disc = soup_album.find_all("strong", class_ = "trackname")
    disc_total = len(soup_disc)
    for disc in soup_disc:
        soup_track = disc.find_all("td", class_ = "song_name")
        #if soup_track.find_all("td")

    return album_year, {1, disc_total,1,1}


def locate_line(tag, file_name):
    song_artist = tag.artist
    song_artist = song_artist.replace(chr(0), '')
    album_artist = tag.album_artist
    song_title = tag.title
    song_album = tag.album
    album_url = ""
    if (song_artist != "") & (song_title != ""):
        search_content = "%s %s"% (album_artist, song_title)
    else:
        search_content = file_name
    try:
        r = NetworkService.get_song_info_html(search_content)
        soup = BeautifulSoup(r, 'html.parser')
        song_section_soup = soup.find_all('table', class_='track_list')
        song_name_soup_list = song_section_soup[0].find_all('tr')[1:]
        found = False

        for i, item in enumerate(song_name_soup_list):
            count = 0
            soup_title = item.find_all('td', class_="song_name")[0].find_all('a')
            if soup_title[0]['title'] == "该艺人演唱的其他版本":
                song_title_from_web = soup_title[1]['title']
            else:
                song_title_from_web = soup_title[0]['title']

            soup_artist = item.find_all('td', class_='song_artist')[0].find_all('a')
            if len(soup_artist) > 1 & (album_artist != song_artist):
                album_artist_from_web = soup_artist[0]['title']
                song_artist_from_web = ""
                for artist in soup_artist[1:]:
                    song_artist_from_web = "%s%s" % (song_artist_from_web, artist.text)
                artist_group_from_web = '%s (%s)' % (album_artist_from_web, song_artist_from_web)

                artist_group = '%s (%s)' % (album_artist, song_artist)
            else:
                artist_group_from_web = soup_artist[0]['title']
                artist_group = song_artist

            song_album_from_web = item.find_all('td', class_='song_album')[0].find_all('a')[0].text\
                .replace("《", "").replace("》", "")

            if song_title_from_web.lower() == song_title.lower():
                count += 1
            if artist_group_from_web.lower() == artist_group.lower():
                count += 1
            if song_album_from_web.lower() == song_album.lower():
                count += 1
            if count >= 2:
                if count == 2:
                    logger.warning("标签未完全匹配，歌曲消息可能有误。")
                    tag.publisher = "CHECK"
                else:
                    logger.info("Title、Artist和Album标签完全匹配，定位准确。")

                if song_artist == "":
                    tag.album_artist = album_artist_from_web
                    tag.artist = song_artist_from_web
                if song_title == "":
                    tag.title = song_title_from_web
                if song_album == "":
                    tag.album = song_album_from_web

                album_url = item.find_all('td', class_='song_album')[0].find_all('a')[0]['href']
                found = True
                break
            else:
                continue
        if not found:
            # raise Exception
            logger.warning("未找到歌曲")
    except Exception as e:
        logger.warning("警告:%s" % e)
    finally:
        return album_url


def update_album_info(tag, album_url):
    try:
        if album_url != "":
            disc_and_track = {}
            year_str, disc_and_track = get_album_details(tag.title, tag.album, album_url)
            song_year = datetime.strptime(year_str, "%Y-%m-%d")
            date = eyed3.core.Date(song_year.year, song_year.month, song_year.day)
            tag.recording_date = date
            if tag.recording_date.month is None:
                raise Exception
            else:
                logger.info("写入日期(%s)成功。" % tag.recording_date)
                return True
        else:
            raise Exception
    except Exception as e:
        logger.warning("写入日期错误:%s" % e)
        return False


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
            recording_date = tag.recording_date
            if recording_date is not None:
                logging.info("发布日期(%s)完整，跳过。" % recording_date)
                continue
            else:
                album_url = locate_line(tag, file_name)
                success = update_album_info(tag, album_url)
        except IOError:
            logger.warning("打开文件失败！")
        finally:
            if success:
                tag.save(version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')
                shutil.move(os.path.join("mp3/", file_name), os.path.join("mp3/Done/", file_name))
                logger.info("标签写入完毕，文件移动至子目录下。")

            logger.info("当前文件'%s'处理完毕。" % file_name)
            logging.info('----------------------------------------------------'
                         '-----------------------------------------------')
            sleep(2)


if "__main__" == __name__:
    logging.info('-------------------------------------------'
                 '程序开始执行-------------------------------------------')
    update_audio_tag()
    logging.info('-------------------------------------------'
                 '程序执行结束-------------------------------------------')
