import logging
import requests

from Entity.Config import Config


class NetworkService(object):
    proxies = dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.101 Safari/537.36'
    }

    @staticmethod
    def get_year_html(album_url):
        logging.info("开始处理" + album_url)
        year_html = requests.get(album_url, headers=NetworkService.headers).text
        return year_html

    @staticmethod
    def get_song_info_html(search_content):
        logging.info("搜索项目：%s" % search_content)
        url = Config.get_config_field()["search_url"] + search_content
        logging.info("访问地址：%s" % url)
        item_html = requests.get(url, headers=NetworkService.headers).text
        return item_html
