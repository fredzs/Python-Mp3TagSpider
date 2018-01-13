#


class SongInfo(object):
    def __init__(self, tag):
        self._song_title = tag.title

        if tag.artist is not None:
            self._song_artist = self.tag_to_list(tag.artist)
        else:
            self._song_artist = []

        if tag.album_artist is not None:
            self._album_artist = self.tag_to_list(tag.album_artist)
        else:
            self._album_artist = []
        if tag.album is not None:
            self._album_title = tag.album
        else:
            self._album_title = ""

    @staticmethod
    def tag_to_list(artist_str):
        if ';' in artist_str:
            artist_list = artist_str.split(';')
        else:
            artist_list = artist_str.split(chr(0))
        return artist_list

    def valid_tag_amount(self):
        amount = 0
        for i in filter(lambda x: x is not None,
                        [self._song_title, self._song_artist, self._album_title, self._album_artist]):
            if len(i) > 0:
                amount = amount + 1
        return amount

    def song_artist_str(self):
        return ' '.join(self._song_artist)

    def album_artist_str(self):
        return ' '.join(self._album_artist)

    def has_album_artist(self):
        return True if len(self._album_artist) != 0 else False

    def same_sa_and_aa(self):
        return True if [aa.lower() for aa in self._album_artist] == [sa.lower() for sa in self._song_artist] else False

    @property
    def song_title(self):
        return self._song_title

    @property
    def song_artist(self):
        return self._song_artist

    @property
    def album_artist(self):
        return self._album_artist

    @album_artist.deleter
    def album_artist(self):
        self._album_artist = []

    @property
    def album_title(self):
        return self._album_title
