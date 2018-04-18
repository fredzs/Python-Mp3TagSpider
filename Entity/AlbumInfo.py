#
from datetime import datetime


class AlbumInfo(object):
    def __init__(self, tag):
        self._song_title = tag.title

        if tag.album is not None:
            self._album_title = tag.album
        else:
            self._album_title = ""

        if tag.album_artist is not None:
            self._album_artist = self.tag_to_list(tag.album_artist)
        else:
            self._album_artist = []

        self._album_date = datetime.strptime("1900-01-01", "%Y-%m-%d")
        self._new_album_artist = []
        self._new_song_artist = []
        self._album_url = ""
        self._disc_num = (1, 1)
        self._track_num = (1, 1)
        self._update_song_artists = False
        self._update_album_artists = False

    @property
    def update_song_artists(self):
        # return True if len(self._new_album_artist) > 0 else False
        return self._update_song_artists

    @update_song_artists.setter
    def update_song_artists(self, update_song_artists):
        self._update_song_artists = update_song_artists

    @property
    def update_album_artists(self):
        return self._update_album_artists

    @update_album_artists.setter
    def update_album_artists(self, update_album_artists):
        self._update_album_artists = update_album_artists

    @property
    def new_album_artist_str(self):
        if len(self._new_album_artist) == 0:
            s = ""
        else:
            s = '; '.join(self._new_album_artist)
        return s

    @property
    def new_song_artist_str(self):
        if len(self._new_song_artist) == 0:
            s = ""
        else:
            s = '; '.join(self._new_song_artist)
        return s

    @staticmethod
    def tag_to_list(artist_str):
        artist_list = artist_str.split(chr(0))
        return artist_list

    @property
    def song_title(self):
        return self._song_title

    @property
    def album_title(self):
        return self._album_title

    @property
    def album_artist(self):
        return self._album_artist

    @property
    def album_date(self):
        return self._album_date

    @property
    def album_date_str(self):
        return str(self._album_date)

    @album_date.setter
    def album_date(self, album_date):
        if isinstance(album_date, datetime):
            self._album_date = album_date
        elif isinstance(album_date, str):
            self._album_date = datetime.strptime(album_date, "%Y-%m-%d")

    @property
    def new_album_artist(self):
        return self._new_album_artist

    @new_album_artist.setter
    def new_album_artist(self, new_album_artist):
        self._new_album_artist.extend(new_album_artist)

    @property
    def new_song_artist(self):
        return self._new_song_artist

    @new_song_artist.setter
    def new_song_artist(self, new_song_artist):
        self._new_song_artist.extend(new_song_artist)

    @property
    def album_url(self):
        return self._album_url

    @album_url.setter
    def album_url(self, album_url):
        self._album_url = album_url

    @property
    def disc_num(self):
        return self._disc_num

    @disc_num.setter
    def disc_num(self, disc_num):
        self._disc_num = disc_num

    @property
    def track_num(self):
        return self._track_num

    @track_num.setter
    def track_num(self, track_num):
        self._track_num = track_num
