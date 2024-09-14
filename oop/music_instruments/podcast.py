from oop.music_instruments.AudioTrack import AudioTrack


class Podcast(AudioTrack):
    def __init__(self, title: str, artist: str, duration: int, episode_number: int):
        super().__init__(title, artist, duration)
        self.episode_number = episode_number

    def play(self) -> str:
        return f"Playing podcast: {self.title}, Episode {self.episode_number}"
