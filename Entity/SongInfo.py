#
import eyed3
from Entity import AlbumInfo


class SongInfo(object):
    def __init__(self, tag):
        self.song_title = tag.title
        self.song_artist = tag.artist.replace(chr(0), ' ')
        if tag.album_artist is not None:
            self.album_artist = str()
        else:
            self.album_artist = ""
        if tag.album is not None:
            self.album_title = tag.album
        else:
            self.album_title = ""

        self.new_album_artist = ""

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
