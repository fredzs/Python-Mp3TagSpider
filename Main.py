import eyed3

audiofile = eyed3.load("mp3/Maroon 5 - Sugar.mp3")
print(audiofile.tag.artist)
#audiofile.tag.album = u"Humanity Is The Devil"
#audiofile.tag.album_artist = u"Integrity"
#audiofile.tag.title = u"Hollow"
#audiofile.tag.track_num = 2

#audiofile.tag.save()
