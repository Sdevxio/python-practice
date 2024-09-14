playlists = {
    'playlist1': ['title1', 'artist1', 'duration1', 'track1'],
    'playlist2': ['title2', 'artist2', 'duration2', 'track2'],
}

for pl in playlists['playlist1']:
    # print(pl)
    track = 'track1'
    if track in pl:
        print(track)
