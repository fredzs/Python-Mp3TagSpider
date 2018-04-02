import logging
import requests
from urllib import parse

from Entity.Config import Config


class NetworkService(object):
    proxies = dict(http='socks5://127.0.0.1:1080', https='socks5://127.0.0.1:1080')
    headers = {
         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    cookies = dict(gid='149691899551074', _unsign_token='749eabe5517bfc2ff915e3af76944952',
                   cna='+NfADiBhlD8CAXL/KAkvQXvx', bdshare_firstime='1496919006832',
                   UM_distinctid='160b72b67fe4da-09983bec7af1e2-b7a103e-1fa400-160b72b67ff22c',
                   _xiamitoken='5a74a13c428c780d55a79a19520e6772', xmgid='ccf5d219-7a5c-43b8-80d3-130b5bbfea9d',
                   uidXM='24103194', user_from='1',
                   CNZZDATA921634='cnzz_eid%3D187493467-1514899922-%26ntime%3D1522670548',
                   __XIAMI_SESSID='294672cd8bfdb6bfd878106e04658a7d', login_method='tblogin',
                   CNZZDATA2629111='cnzz_eid%3D492183730-1514898251-%26ntime%3D1522674279',
                   isg='BBMTWz32Tfh6EwElJV_a1MoKopf9YGAkLonNRcUwNjJpRDHmT5zX21TWerQqX_-C',
                   xm_token='455bb6e74bb2037b317a7ca242d5ffc3',
                   member_auth='hT%2BeTo1Oums0gveRTdwwcCAY5uCBSGWHlIRS3uIotwVwIYgNNov4x6uTRgpI2yGarGFpVujIsnEN')

    @staticmethod
    def get_year_html(album_url):
        logging.debug("开始处理：" + album_url)
        year_html = requests.get(album_url, headers=NetworkService.headers, cookies=NetworkService.cookies).text
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
