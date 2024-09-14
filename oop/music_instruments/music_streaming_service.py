from collections import Counter
from typing import List, Tuple, Optional

from oop.music_instruments.AudioTrack import AudioTrack
from oop.music_instruments.palylist import Playlist


class MusicStreamingService:
    def __init__(self):
        self.playlists: dict[str, Playlist] = {}

    def create_playlist(self, name: str) -> None:
        if name not in self.playlists:
            self.playlists[name] = Playlist(name)
        else:
            print(f"Playlist '{name}' already exists.")

    def delete_playlist(self, name: str) -> bool:
        return self.playlists.pop(name, None) is not None

    def add_track_to_playlist(self, playlist_name: str, track: AudioTrack) -> bool:
        if playlist_name in self.playlists:
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
