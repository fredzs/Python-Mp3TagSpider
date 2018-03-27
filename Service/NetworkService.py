import logging
import requests
from urllib import parse

from Entity.Config import Config


class NetworkService(object):
    proxies = dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
    }

    @staticmethod
    def get_year_html(album_url):
        logging.debug("开始处理：" + album_url)
        year_html = requests.get(album_url, headers=NetworkService.headers).text
        return year_html

    @staticmethod
    def get_song_info_html(search_content):
        logging.info("搜索项目：%s" % search_content)
        raw_url = Config.get_config_field()["search_url"] + search_content
        url = parse.quote_plus(raw_url, safe=':/?=')
        logging.info("访问地址：%s" % url)
        try:
            item_html = requests.get(url, headers=NetworkService.headers).text
        except Exception as e:
            raise e
        return item_html
