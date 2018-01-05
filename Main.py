#!user/bin/env python3
# -*- coding: gbk -*-
import os
import logging
from logging.config import fileConfig
import warnings
import eyed3
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

from numpy import unicode

from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService

########################################################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
fileConfig('logging_config.ini')
logger = logging.getLogger()
logger.debug('often makes a very good meal of %s', 'visiting tourists')
########################################################################################################
FILEPATH = 'mp3/'


def get_year(album_url):
    html = NetworkService.get_year_html(album_url)
    soup_year = BeautifulSoup(html, 'html.parser')
    soup_album_info = soup_year.find_all("div", id="album_info")[0]
    album_year_string = soup_album_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
    album_year = album_year_string.replace('��', '-').replace('��', '-').replace('��', '')
    logging.info("ר������ʱ��Ϊ%s" % album_year)
    return album_year


def update_audio_tag():
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(FILEPATH)):
        file_path = os.path.join(FILEPATH, file_name)
        #file_path2 = unicode(file_path , "utf8")
        try:
            audio_file = eyed3.load(file_path)
            #audio_file = eyed3.load(u'mp3\�������ֶ� - ��˵�ټ�.mp3'.decode('gbk'))
            if audio_file is None:
                raise IOError
        except IOError:
            logger.warning("���ļ�ʧ�ܣ�")
        else:
            tag = audio_file.tag
            recording_date = tag.recording_date
            if recording_date:
                logging.info("�ļ����ƣ�'%s'��������(%s)������������" % (file_name, recording_date))
                continue
            else:
                try:
                    song_artist = tag.artist
                    song_title = tag.title
                    song_album = tag.album
                    logging.info("�ļ����ƣ�" + song_artist + " - " + song_title)

                    if (song_artist != "") & (song_title != ""):
                        search_content = song_artist + " " + song_title
                    else:
                        search_content = file_name

                    r = NetworkService.get_song_info_html(search_content)
                    soup = BeautifulSoup(r, 'html.parser')

                    song_section_soup = soup.find_all('table', class_='track_list')
                    song_name_soup_list = song_section_soup[0].find_all('tr')[1:]

                    album_url = ""
                    found = False
                    for i, item in enumerate(song_name_soup_list):
                        if item.find_all('td', class_="song_name")[0].find_all('a')[0]['title'] == "�������ݳ��������汾":
                            song_title_from_web = item.find_all('td', class_="song_name")[0].find_all('a')[1]['title']
                        else:
                            song_title_from_web = item.find_all('td', class_="song_name")[0].find_all('a')[0]['title']
                        song_artist_from_web = item.find_all('td', class_='song_artist')[0].find_all('a')[0]['title']
                        song_album_from_web = item.find_all('td', class_='song_album')[0].find_all('a')[0][
                            'title'].replace("��", "").replace("��", "")

                        if (song_title_from_web == song_title) | (song_artist_from_web == song_artist):
                            if song_artist == "":
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
                        logger.warning("δ�ҵ�����")
                        raise Exception

                    logging.info("�ҵ�ר����%s�������� %s ץȡ" % (song_album, album_url))
                    year_str = get_year(album_url)
                    song_year = datetime.strptime(year_str, "%Y-%m-%d")
                    date = eyed3.core.Date(song_year.year, song_year.month, song_year.day)
                    tag.recording_date = date
                except Exception:
                    logger.warning("")
                else:
                    tag.save(version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')
                finally:
                    sleep(2)
        finally:
            logger.info("")


if "__main__" == __name__:
    logging.info('----------����ʼִ��----------')
    update_audio_tag()
    logging.info('----------����ִ�н���----------')
# audiofile.tag.artist = "Maroon 5"
# audiofile.tag.track_num = 2
