#
import eyed3
from Entity import AlbumInfo


class SongInfo(object):
    def __init__(self, tag):
        self.song_title = tag.title
        if tag.song_artist is not None:
            self.song_artist = self.__artist_to_list(tag.song_artist)
        else:
            self.song_artist = []

        if tag.album_artist is not None:
            self.album_artist = self.__artist_to_list(tag.album_artist)
        else:
            self.album_artist = []
        if tag.album is not None:
            self.album_title = tag.album
        else:
            self.album_title = ""

        self.new_album_artist = []

    @staticmethod
    def __artist_to_list(self, artist_str):
        artist_list = []
        # artist.replace(chr(0), ' ')
        return artist_list

    def has_album_artist(self):
        return True if self.album_artist!="" else False

    def same_sa_and_aa(self):
        return True if self.album_artist.lower() == self.song_artist.lower() else False

    def update_song_info(self):
        return True if len(self.new_album_artist) > 0 else

    @property
    def song_title(self):
        return self.song_title

    @property
    def song_artist(self):
        return self.song_artist

    @property
    def album_artist(self):
        return self.album_artist

    @property
    def album_title(self):
        return self.album_title

    @property
    def new_album_artist(self):
        return self.new_album_artist

    @new_album_artist.setter
    def new_album_artist(self, new_album_artist):
        self.new_album_artist = new_album_artist
