import random
from abc import ABC, abstractmethod
from collections import Counter
from typing import List, Tuple, Optional


class AudioTrack(ABC):
    def __init__(self, title: str, artist: str, duration: int):
        self.title = title
        self.artist = artist
        self.duration = duration

    @abstractmethod
    def play(self) -> str:
        pass

    def get_info(self) -> str:
        return f"{self.title} by {self.artist} {self.duration} second."


class Song(AudioTrack):
    def __init__(self, title: str, artist: str, duration: int, album: str):
        super().__init__(title, artist, duration)
        self.album = album

    def play(self) -> str:
        return f"Playing song: {self.title} from album {self.album}"


class Podcast(AudioTrack):
    def __init__(self, title: str, artist: str, duration: int, episode_number: int):
        super().__init__(title, artist, duration)
        self.episode_number = episode_number

    def play(self) -> str:
        return f"Playing podcast: {self.title}, Episode {self.episode_number}"


class Playlist:
    def __init__(self, name: str):
        self.name: name
        self.tracks: List[AudioTrack] = []

    def add_track(self, track: AudioTrack) -> None:
        if track not in self.tracks:
            self.tracks.append(track)
        else:
            print(f"Track {track} already it the playlist.")

    def remove_track(self, title: str) -> bool:
        for track in self.tracks:
            if track.title == title:
                self.tracks.remove(track)
                return True
        return False

    def get_total_duration(self) -> int:
        return sum(track.duration for track in self.tracks)

    def play_all(self) -> List[AudioTrack:str]:
        return [track.play() for track in self.tracks]

    def shuffle(self) -> None:
        random.shuffle(self.tracks)


class MusicStreamingService:
    def __init__(self):
        self.playlists = dict[str, Playlist]

    def create_playlist(self, name: str) -> None:
        if name not in self.playlists:
            self.playlists[name] = Playlist(name)
        else:
            print(f"Playlist '{name}' already exists.")

    def delete_playlist(self, name: str) -> bool:
        return self.playlists.pop(name, None) is not None

    def add_track_to_playlist(self, playlist_name: str, track: AudioTrack) -> bool:
        if playlist_name not in self.playlists:
            self.playlists[playlist_name].add_track(track)
            return True
        return False

    def find_track(self, title: str) -> List[Tuple[str, AudioTrack]]:
        return [(playlist_name, track)
                for playlist_name, playlist in self.playlists.items()
                for track in playlist.tracks
                if track.title == title]

    def get_most_popular_track(self) -> Optional[Tuple[AudioTrack, int]]:
        all_tracks = [track for playlist in self.playlists.values() for track in playlist.tracks]
        if not all_tracks:
            return None
        track_counts = Counter(all_tracks)
        most_common = track_counts.most_common(1)[0]
        return most_common


if __name__ == "__main__":
    # Create some tracks
    song1 = Song("Song 1", "Artist 1", 180, "Album 1")
    song2 = Song("Song 2", "Artist 2", 200, "Album 2")
    podcast1 = Podcast("Podcast 1", "Host 1", 1800, 1)

    # Create a streaming service
    service = MusicStreamingService()

    # Create playlists and add tracks
    service.create_playlist("My Favorites")
    service.create_playlist("Workout Mix")

    service.add_track_to_playlist("My Favorites", song1)
    service.add_track_to_playlist("My Favorites", song2)
    service.add_track_to_playlist("Workout Mix", song1)
    service.add_track_to_playlist("Workout Mix", podcast1)

    # Find a track
    found_tracks = service.find_track("Song 1")
    print("Found 'Song 1' in:", [playlist for playlist, _ in found_tracks])

    # Get most popular track
    popular_track, count = service.get_most_popular_track()
    print(f"Most popular track: {popular_track.title}, in {count} playlists")

    # Play all tracks in a playlist
    print("\nPlaying 'Workout Mix':")
    for play_output in service.playlists["Workout Mix"].play_all():
        print(play_output)
