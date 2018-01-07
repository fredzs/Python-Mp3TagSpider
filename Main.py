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
        logging.info("��������(%s)������������" % recording_date)
        pass_this = True

    return pass_this


def get_album_details(song_title, song_album, album_url):
    logging.info("�ҵ�ר����%s�������� %s ץȡ" % (song_album, album_url))
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
        album_year = album_year_string.replace('��', '-').replace('��', '-').replace('��', '')
        logging.info("ר������ʱ��Ϊ%s" % album_year)

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
        logging.info("ר������%d�ŵ�������%sΪ��%d�ŵ��ĵ�%d�ף����ŵ�����%d�ס�" % (disc_total, song_title,
                                                             disc, track, track_total))
    except Exception as e:
        logging.warning("���ִ���%s" % e)
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
                if soup_title[0]['title'] == "�������ݳ��������汾":
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
                    .replace("��", "").replace("��", "")

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
                    logger.info("Title��Artist��Album��ǩ��ȫƥ�䣬��λ׼ȷ��")
                elif len(flag) >= 3:
                    if "title" not in flag:
                        logger.warning("Titleδ��ȫƥ�䣬���ֶ�����")
                        publisher += "Title "
                    if ("artist_album_artist" not in flag) & ("artist" not in flag):
                        logger.warning("Artistδ��ȫƥ�䣬���ֶ�����")
                        publisher += "Artist Album_artist"
                    if ("artist_album_artist" not in flag) & ("artist" in flag):
                        if "album" in flag:
                            logger.warning("Artistδ��ȫƥ�䣬��Album_artistƥ�䣬�Զ����¡�")
                            logger.info("д��Album_artist��%s��" % album_artist_from_web)
                            tag.album_artist = album_artist_from_web
                            publisher += "NewArtist "
                        else:
                            logger.warning("Artistδ��ȫƥ�䣬���ֶ�����")
                            publisher += "Artist "
                    if "album" not in flag:
                        if update_album:
                            logger.warning("Albumδ��ȫƥ�䣬�Զ����¡�")
                            tag.album = song_album_from_web
                            logger.info("��Album��%s����Album��%s��" % (song_album, song_album_from_web))
                            publisher += "NewAlbum "
                        else:
                            logger.warning("Albumδ��ȫƥ�䣬���ֶ�����")
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
                logger.warning("δ�ҵ�����")
    except Exception as e:
        logger.warning("����:%s" % e)
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
                logger.info("д������(%s)�ɹ���" % tag.recording_date)
                result = True

            tag.track_num = (disc_and_track["track"], disc_and_track["track_total"])
            tag.disc_num = (disc_and_track["disc"], disc_and_track["disc_total"])
            logger.info("д��������ųɹ���")
        else:
            raise Exception
    except Exception as e:
        logger.warning("д��ר����Ϣ����:%s" % e)
    finally:
        return result


def update_audio_tag():
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(FILE_PATH)):
        success = False
        logging.info("�ļ����ƣ�'%s'��" % file_name)
        file_path = os.path.join(FILE_PATH, file_name)
        try:
            audio_file = eyed3.load(file_path)
            if audio_file is None:
                raise IOError

            tag = audio_file.tag
            pass_this = check_tag_complete(tag)
            if pass_this:
                logging.info("������ǩ������������")
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
            logger.warning("���ļ�ʧ�ܣ�")
        finally:
            if success:
                tag.save()
                # version=eyed3.id3.ID3_DEFAULT_VERSION, encoding='utf-8')
                shutil.move(os.path.join(FILE_PATH, file_name), os.path.join(DONE_PATH, file_name))
                logger.info("��ǩд����ϣ��ļ��ƶ�����Ŀ¼�¡�")

            logger.info("��ǰ�ļ�'%s'������ϡ�" % file_name)
            logging.info('----------------------------------------------------'
                         '-----------------------------------------------')
            sleep(2)


if "__main__" == __name__:
    if not os.path.exists(DONE_PATH):
        os.makedirs(DONE_PATH)

    logging.info('-------------------------------------------'
                 '����ʼִ��-------------------------------------------')
    update_audio_tag()
    logging.info('-------------------------------------------'
                 '����ִ�н���-------------------------------------------')
