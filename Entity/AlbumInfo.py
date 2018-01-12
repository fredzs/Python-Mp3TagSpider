#
from datetime import datetime


class AlbumInfo(object):
    def __init__(self, tag):
        self.song_title = tag.title

        if tag.album is not None:
            self.__album_title = tag.album
        else:
            self.__album_title = ""

        if tag.album_artist is not None:
            self.__album_artist = self.artist_to_list(tag.album_artist)
        else:
            self.__album_artist = []

        self.album_date = datetime.strptime("1900-01-01", "%Y-%m-%d")
        self.new_album_artist = []
        self.new_song_artist = []
        self.album_url = ""
        self.disc_num = (1, 1)
        self.track_num = (1, 1)

    def update_artists(self):
        return True if len(self.new_album_artist) > 0 else False

    @staticmethod
    def artist_to_list(artist_str):
        artist_list = []
        # artist.replace(chr(0), ' ')
        return artist_list

    @property
    def album_title(self):
        return self.album_title

    @property
    def album_artist(self):
        return self.album_artist

    @property
    def album_date(self):
        return self.album_date

    @property
    def album_date_str(self):
        return str(self.album_date)

    @album_date.setter
    def album_date(self, album_date):
        self.album_date = album_date

    @property
    def new_album_artist(self):
        return self.new_album_artist

    @new_album_artist.setter
    def new_album_artist(self, new_album_artist):
        self.new_album_artist.extend(new_album_artist)

    @property
    def new_song_artist(self):
        return self.new_song_artist

    @new_song_artist.setter
    def new_song_artist(self, new_song_artist):
        self.new_song_artist.extend(new_song_artist)

    @property
    def album_url(self):
        return self.album_url

    @album_url.setter
    def album_url(self, album_url):
        self.album_url = album_url

    @property
    def disc_num(self):
        return self.disc_num

    @disc_num.setter
    def disc_num(self, disc_num):
        self.disc_num = disc_num

    @property
    def track_num(self):
        return self.track_num

    @track_num.setter
    def track_num(self, track_num):
        self.track_num = track_num

