from typing import List

from oop.music_instruments.AudioTrack import AudioTrack


class Playlist:
    def __init__(self, name: str):
        self.name = name
        self.tracks: List[AudioTrack] = []

    def add_track(self, track: AudioTrack) -> None:
        if track not in self.tracks:
            self.tracks.append(track)
        else:
            print(f"Track '{track.title}' already in the playlist.")

    def remove_track(self, title: str) -> bool:
        for track in self.tracks:
            if track.title == title:
                self.tracks.remove(track)
                return True
        return False

    def get_total_duration(self) -> int:
        return sum(track.duration for track in self.tracks)

    def play_all(self) -> List[str]:
        return [track.play() for track in self.tracks]

    def shuffle(self) -> None:
        random.shuffle(self.tracks)
