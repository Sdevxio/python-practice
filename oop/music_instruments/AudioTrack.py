from abc import ABC, abstractmethod


class AudioTrack(ABC):
    def __init__(self, title, artist, duration):
        self.title = title
        self.artist = artist
        self.duration = duration

    @abstractmethod
    def play_songs(self) -> str:
        pass

    def get_info(self) -> str:
        return f"Title: {self.title} by \n Artist: {self.artist}\n Duration: {self.duration} seconds.\n"

    # def __str__(self):
    #     return self.get_info()
