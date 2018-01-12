#


class SongInfo(object):
    def __init__(self, album_title, album_artitst):
        self.album_title = album_title
        self.album_artitst = album_artitst

        self.album_url = ""
        self.new_album_artist = ""
        self.new_album_date = ""

    @property
    def album_title(self):
        return self.album_title

    @property
    def album_artitst(self):
        return self.album_artitst

    @property
    def new_album_artist(self):
        return self.new_album_artist

    @property
    def new_album_date(self):
        return self.new_album_date

    @property
    def album_url(self):
        return self.album_url

    @new_album_artist.setter
    def new_album_artist(self, new_album_artist):
        self.new_album_artist = new_album_artist

    @new_album_date.setter
    def new_album_date(self, new_album_date):
        self.new_album_date = new_album_date

    @album_url.setter
    def album_url(self, album_url):
        self.album_url = album_url
