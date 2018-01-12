#!user/bin/env python3
# -*- coding: gbk -*-
import logging
import os
import re
import shutil
import warnings
from datetime import datetime
from logging.config import fileConfig
from time import sleep

import eyed3
from bs4 import BeautifulSoup

from Service.ConfigService import ConfigService
from Service.NetworkService import NetworkService
from Utility.Const import Const
##########################################################################
warnings.filterwarnings("ignore")
ConfigService().init()
fileConfig('logging_config.ini')
logger = logging.getLogger()

##########################################################################


def check_tag_complete(tag):
    pass_this = False
    recording_date = tag.recording_date
    if recording_date is not None:
        logging.info("��������(%s)������������" % recording_date)
        pass_this = True

    return pass_this


def get_album_details(song_title, song_album, album_url):
    logging.info("�ҵ�ר����%s�������� %s ץȡ" % (song_album, album_url))
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


# return result, album_url, new_artist
def locate_song(soup_song_list, song_info, search_strictly=True, search_times=10):
    result = Const.NOT_FOUND
    album_url = ""
    new_artist = {}
    for i, line in enumerate(soup_song_list[:search_times - 1]):
        song_info_web = {}
        flag = {}
        new_artist_str = ""
        soup_title = line.find_all('td', class_="song_name")[0].find_all('a')
        soup_album = line.find_all('td', class_='song_album')[0].find_all('a')[0]
        song_info_web["title"] = soup_title[1]['title'] if soup_title[0]['title'] == "�������ݳ��������汾" else soup_title[0][
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
        song_info_web["album"] = soup_album.text.replace("��", "").replace("��", "")

        for key in Const.KEY_TAGS:
            if key in song_info:
                if song_info_web[key].lower() == song_info[key].lower():
                    flag[key] = 1

        count = int(i + 1)
        if search_strictly:
            if len(flag) < len(song_info):
                continue
            if len(flag) == len(song_info):
                logger.info("------��%s��ƥ��ɹ���Title��Artist��Album��ǩ��ȫƥ�䣬��λ׼ȷ��" % count)
                result = Const.DONE
        else:
            if len(flag) < len(song_info) - 1:
                continue
            if len(flag) == len(song_info) - 1:
                logger.info("------��%s��ƥ��ɹ�������ǩδ��ȫƥ�䣬���ע��" % count)
                result = Const.CHECK
                if ("title" in flag) & ("album" in flag):
                    if song_info_web["album_artist"].lower() == song_info["song_artist"].lower():
                        new_artist['new_song_artist'] = new_artist_str
                        new_artist['new_album_artist'] = song_info_web["album_artist"]
                        logger.info("------ץȡ���µ�ר��������Ϣ��ͬʱ���¡�")

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
def get_album_url(tag, search_content, has_album_artist=False):
    soup_song_list = locate_song_list(search_content)
    if soup_song_list is None:
        return Const.NOT_FOUND, ""

    song_info = {"title": tag.title, "song_artist": tag.artist.replace(chr(0), ' ')}
    if has_album_artist:
        song_info["album_artist"] = tag.album_artist.replace(chr(0), ' ')
    if tag.album is not None:
        song_info["album"] = tag.album
    logger.info("----�ϸ�ģʽ���á�")
    result, album_url, new_artist = locate_song(soup_song_list, song_info)
    if result == 'NOT_FOUND':
        logger.info("----�ϸ�ģʽδ�ҵ�����������ģ����ѯ��")
        result, album_url, new_artist = locate_song(soup_song_list, song_info, False)
    if result == 'NOT_FOUND':
        logger.info("----ģ����ѯδ�ҵ�������")
    return album_url, new_artist


def update_song_info(tag, new_artist):
    result = False
    if len(new_artist) > 0:
        try:
            tag.artist = new_artist["new_song_artist"]
            tag.album_artist = new_artist["new_album_artist"]
        except Exception as e:
            logger.warning("д���¸���ʧ�ܣ�%s" % e)
        else:
            logger.info("д���¸��ֳɹ���")
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
                logger.info("д������(%s)�ɹ���" % tag.recording_date)
                result = 'DONE'

            tag.track_num = (disc_and_track["track"], disc_and_track["track_total"])
            tag.disc_num = (disc_and_track["disc"], disc_and_track["disc_total"])
            logger.info("д��������ųɹ���")
        else:
            raise Exception
    except Exception as e:
        logger.warning("д��ר����Ϣ����:%s" % e)
    finally:
        return result


# ----------------------------------------------------------------------------------#


def update_audio_tag():
    for file_name in filter(lambda x: x.endswith(".mp3"), os.listdir(FILE_PATH)):
        result = "Failed"
        logging.info("�ļ����ƣ�'%s'��" % file_name)
        file_path = os.path.join(FILE_PATH, file_name)
        new_artist = {}
        try:
            audio_file = eyed3.load(file_path)
            if audio_file is None:
                raise IOError

            tag = audio_file.tag
            pass_this = False  # check_tag_complete(tag)
            if pass_this:
                logging.info("������ǩ������������")
                continue
            else:
                if tag.artist is None:
                    search_content = file_name
                else:
                    search_content = "%s %s" % (tag.artist, tag.title)
                if tag.album_artist is not None:
                    if tag.album_artist.lower() != tag.artist.lower():
                        logging.info("--ר�����ִ��ڣ����Ȳ��ҡ�")
                        search_content = "%s %s" % (tag.album_artist, tag.title)
                        album_url, new_artist = get_album_url(tag, search_content, True)
                        if album_url == "":
                            logging.info("--����ר��������ƥ�䣬���Ҹ������֡�")
                            search_content = "%s %s" % (tag.artist, tag.title)
                            album_url, new_artist = get_album_url(tag, search_content, True)
                    else:
                        logging.info("--ר�����������������ͬ�����Ҹ������֡�")
                        album_url, new_artist = get_album_url(tag, search_content)
                else:
                    logging.info("--ר�����ֲ����ڣ����Ҹ������֡�")
                    album_url, new_artist = get_album_url(tag, search_content)

                if album_url == "":
                    logger.warning("δ�ҵ���Ŀ:%s" % search_content)
                elif len(new_artist) == 0:
                    result = update_album_info(tag, album_url)
                else:
                    result = update_album_info(tag, album_url) & update_song_info(tag, new_artist)

        except IOError:
            logger.warning("���ļ�ʧ�ܣ�")
        finally:
            result_path = MOVE_PATH.get(result,'Failed')
            if (result == 'Done') | (result == 'Check'):
                try:
                    tag.save()
                except Exception as e:
                    logger.warning("�ļ�����ʧ��: %s" % e)
            if result == 'Failed':
                logger.info("��ǩ����ʧ�ܣ����ֶ�����")
            shutil.move(os.path.join(FILE_PATH, file_name), os.path.join(result_path, file_name))
            logger.info("��ǰ�ļ�'%s'�������,�ļ��ƶ���%sĿ¼�¡�" % (file_name,result_path))
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
