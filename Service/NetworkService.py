import logging
import requests
from urllib import request
from urllib import parse
from http import cookiejar

from Entity.Config import Config

logger = logging.getLogger()


class NetworkService(object):
    proxies = dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    }
    cookies = dict()
    # cookies = dict(gid='152449204124155',  _unsign_token='a36aece2325b79ba07f08e1fb5c59e29',  cna='C9VkE2vhTXcCAXaQhSSQrihK',  UM_distinctid='162f2ce959f569-0412cd481a3e19-1373565-1fa400-162f2ce95a0827',  login_method='emaillogin',  _xiamitoken='132b33850319a9d1747cf8498a52bb9f',  _umdata='ED82BDCEC1AA6EB914DCEFC67662FACA91FFC3B9E5CDD4432D438BEB077BAFB154126CA46D222E90CD43AD3E795C914CA7486438032EAF2A7D3DD8E457B95F79',  xmgid='78209830-b518-4025-a599-d10f1508fe1f',  xm_token='a10819bf0abc04c131acedef6b377503',  uidXM='24103194',  member_auth='hT%2BeTo1Oums0gveRTdwwcCAY5uCBSGWHlIRS3uIotwVwIYgNNov4x6uTRgpI2yGarGFpVujIsnEN',  user='24103194%22Fred_zs%22images%2Favatar_new%2F482%2F24103194_1381370321_1.gif%220%224888%22%3Ca+href%3D%27http%3A%2F%2Fwww.xiami.com%2Fwebsitehelp%23help9_3%27+%3ELv6%3C%2Fa%3E%2211%220%224490%221b3e33b0e8%221525594436',  CNZZDATA2629111='cnzz_eid%3D1551544802-1524488888-https%253A%252F%252Flogin.xiami.com%252F%26ntime%3D1525610727',  CNZZDATA921634='cnzz_eid%3D1403646431-1524486787-https%253A%252F%252Flogin.xiami.com%252F%26ntime%3D1525613331',  x5sec='7b22617365727665723b32223a223430373435623638656138366639303333623865613330386561393235323261434e6149764e6346454b626674705446794f4b3043413d3d227d',  XMPLAYER_url='/song/playlist/id/2088578/object_name/default/object_id/0',  XMPLAYER_addSongsToggler='0',  __guestplay='MjA4ODU3OCwxOzE3NzI5Mjg2ODQsMTsxNzcyOTI4NjY5LDE7MTc5NjM3NzY1MywxOzMyNTA1MTYsMTsxNzY4OTkyMzgxLDE7MTc2OTMwMzA4OCwxOzIwNzQxNjEsMzsxNzcxODMzNjk5LDI7MjA3MzUxMywxOzM5NTMzMywxOzE3OTY3MzEwNzksMTsxNzcwMDYwOTU2LDE7MTc5NjM4NzAyOSwxOzE3NzExMjYwNjMsMTsyNDA3ODEzLDE7MTc3MTY2NDAyMywxOzE3NzE2NjQwMjQsMQ%3D%3D',  XMPLAYER_isOpen='0',  isg='BAkJZCLjt1fSZkuR_D7EkpDeGDWj_jomwXWh9Kt_J_Am8isE-qfXWHVDMFbEkpXA')

    @staticmethod
    def get_cookies():
        home_page_url = Config.get_config_field()["home_page"]
        # headers = requests.get(home_page_url, headers=NetworkService.headers).headers

        # 声明一个CookieJar对象实例来保存cookie
        cookie = cookiejar.CookieJar()
        # 利用urllib.request库的HTTPCookieProcessor对象来创建cookie处理器,也就CookieHandler
        handler = request.HTTPCookieProcessor(cookie)
        # 通过CookieHandler创建opener
        opener = request.build_opener(handler)
        # 此处的open方法打开网页
        response = opener.open('http://www.xiami.com')
        # 打印cookie信息
        for item in cookie:
            print('Name = %s' % item.name)
            print('Value = %s' % item.value)

    @staticmethod
    def str_2_cookies():
        cookies_str = Config.get_config_field()["cookies"]
        new_str = cookies_str.replace(";", "',").replace("=", "='") + "'"
        cookies_dict = eval("dict(" + new_str + ")")
        NetworkService.cookies = cookies_dict

    @staticmethod
    def get_year_html(album_url):
        logger.debug("开始处理：" + album_url)
        year_html = requests.get(album_url, headers=NetworkService.headers, cookies=NetworkService.cookies).text
        return year_html

    @staticmethod
    def get_song_info_html(search_content):
        try:
            logger.info("搜索项目：%s" % search_content)
        except UnicodeEncodeError as e:
            pass
        raw_url = Config.get_config_field()["search_url"] + search_content
        url = parse.quote_plus(raw_url, safe=':/?=')
        logger.info("访问地址：%s" % url)
        try:
            item_html = requests.get(url, headers=NetworkService.headers).text
        except Exception as e:
            raise e
        return item_html
