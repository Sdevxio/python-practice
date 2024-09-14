from oop.music_instruments.AudioTrack import AudioTrack


class Song(AudioTrack):
    def __init__(self, title, artist, duration, album):
        super().__init__(title, artist, duration)
        self.album = album

    def play_songs(self) -> str:
        return f"Playing song: {self.title} from album {self.album}"
