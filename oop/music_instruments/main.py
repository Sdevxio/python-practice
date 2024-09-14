from oop.music_instruments.music_streaming_service import MusicStreamingService
from oop.music_instruments.palylist import Playlist
from oop.music_instruments.podcast import Podcast
from oop.music_instruments.song import Song

if __name__ == '__main__':
    # Create some tracks
    song1 = Song("Song 1", "Artist 1", 180, "Album 1")
    song2 = Song("Song 2", "Artist 2", 200, "Album 2")
    podcast1 = Podcast("Podcast 1", "Host 1", 1800, 1)

    # Create a streaming service
    service = MusicStreamingService()

    # Create playlists and add tracks
    print(service.create_playlist("My Favorites"))
    print(service.create_playlist("Workout Mix"))

    service.add_track_to_playlist("My Favorites", song1)
    service.add_track_to_playlist("My Favorites", song2)
    service.add_track_to_playlist("Workout Mix", song1)
    service.add_track_to_playlist("Workout Mix", podcast1)

    # Find a tracks
    found_tracks = service.find_track("Song 1")
    print("Found 'Song 1' in:", [playlist for playlist, _ in found_tracks])
