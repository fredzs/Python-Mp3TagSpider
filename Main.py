import os
import logging
import warnings
import eyed3
from bs4 import BeautifulSoup
from datetime import datetime
from time import sleep

from Factory.LogFactory import LogFactory
from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService

########################################################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
LogFactory().init()
########################################################################################################
FILEPATH = "mp3/"


def get_year(album_url):
    html = NetworkService.get_year_html(album_url)
    soup_year = BeautifulSoup(html, 'html.parser')
    soup_album_info = soup_year.find_all("div", id="album_info")[0]
    album_year_string = soup_album_info.find_all("table")[0].find_all("tr")[3].find_all("td")[1].text
    album_year = album_year_string.replace('年', '-').replace('月', '-').replace('日', '')
    logging.info("专辑发行时间为%s" % album_year)
    return album_year


def update_audio_tag():
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(FILEPATH)):
        audio_file = eyed3.load(FILEPATH + file_name)
        tag = audio_file.tag

        print(tag.version)

        if tag.recording_date:
            continue
        else:
            song_artist = tag.artist
            song_title = tag.title
            song_album = tag.album
            logging.warning("文件名称：" + song_artist + " - " + song_title)

            if (song_artist != "") & (song_title != ""):
                search_content = song_artist + " " + song_title
            else:
                search_content = file_name

            r = NetworkService.get_song_info_html(search_content)
            soup = BeautifulSoup(r, 'html.parser')

            song_section_soup = soup.find_all('table', class_='track_list')
            song_name_soup_list = song_section_soup[0].find_all('td', class_='song_name')
            if song_name_soup_list[0].find_all('a')[0]['title'] == "该艺人演唱的其他版本":
                del song_name_soup_list[0]
            song_artist_soup_list = song_section_soup[0].find_all('td', class_='song_artist')
            song_album_soup_list = song_section_soup[0].find_all('td', class_='song_album')

            album_url = ""
            for i, item in enumerate(song_name_soup_list):
                song_title_from_web = item.find_all('a')[0]['title']
                song_artist_from_web = song_artist_soup_list[0].find_all('a')[i]['title']
                song_album_from_web = song_album_soup_list[0].find_all('a')[i]['title'].replace("《", "").replace("》", "")
                if (song_artist != "") & (song_title != ""):
                    if song_title_from_web == song_title: # & (song_artist_from_web == song_artist):
                        if song_album == "":
                            song_album = song_album_from_web
                        album_url = song_album_soup_list[0].find_all('a')[i]['href']
                        break
                else:
                    song_artist = song_artist_from_web
                    song_title = song_title_from_web
                    song_album = song_album_from_web
                    album_url = song_album_soup_list[0].find_all('a')[i]['href']
            logging.debug("找到专辑《%s》，进入 %s 抓取" % (song_album, album_url))
            year_str = get_year(album_url) + " 00:00:00"
            song_year = datetime.strptime(year_str, "%Y-%m-%d %H:%M:%S")
            tag.recording_date = song_year

            tag.save()
            sleep(2)


if "__main__" == __name__:
    logging.info('----------程序开始执行----------')
    update_audio_tag()
    logging.info('----------程序执行结束----------')
# audiofile.tag.artist = "Maroon 5"
# audiofile.tag.track_num = 2
