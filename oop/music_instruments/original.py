from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import random
from collections import Counter


class AudioTrack(ABC):
    """
    Abstract base class for all audio tracks.
    Defines the common structure and interface for Songs and Podcasts.
    """

    def __init__(self, title: str, artist: str, duration: int):
        self.title = title
        self.artist = artist
        self.duration = duration  # Duration in seconds

    @abstractmethod
    def play(self) -> str:
        """
        Abstract method to be implemented by subclasses.
        This ensures that all AudioTrack subclasses have a play method.
        """
        pass

    def get_info(self) -> str:
        """
        Returns a formatted string with track information.
        This method is common to all AudioTrack subclasses.
        """
        return f"{self.title} by {self.artist} ({self.duration} seconds)"


class Song(AudioTrack):
    """
    Represents a song, inheriting from AudioTrack.
    Adds an 'album' attribute specific to songs.
    """

    def __init__(self, title: str, artist: str, duration: int, album: str):
        super().__init__(title, artist, duration)
        self.album = album

    def play(self) -> str:
        """
        Implements the play method for songs.
        This fulfills the contract set by the AudioTrack abstract base class.
        """
        return f"Playing song: {self.title} from album {self.album}"


class Podcast(AudioTrack):
    """
    Represents a podcast episode, inheriting from AudioTrack.
    Adds an 'episode_number' attribute specific to podcasts.
    """

    def __init__(self, title: str, artist: str, duration: int, episode_number: int):
        super().__init__(title, artist, duration)
        self.episode_number = episode_number

    def play(self) -> str:
        """
        Implements the play method for podcasts.
        This fulfills the contract set by the AudioTrack abstract base class.
        """
        return f"Playing podcast: {self.title}, Episode {self.episode_number}"


class Playlist:
    """
    Represents a playlist, which is a collection of AudioTrack objects.
    This class demonstrates composition, as it contains but does not inherit from AudioTrack.
    """

    def __init__(self, name: str):
        self.name = name
        self.tracks: List[AudioTrack] = []  # Can contain both Songs and Podcasts

    def add_track(self, track: AudioTrack) -> None:
        """
        Adds an AudioTrack to the playlist.
        Demonstrates polymorphism: can add any subclass of AudioTrack.
        """
        if track not in self.tracks:
            self.tracks.append(track)
        else:
            print(f"Track '{track.title}' already in the playlist.")

    def remove_track(self, title: str) -> bool:
        """
        Removes a track from the playlist by its title.
        Returns True if a track was removed, False otherwise.
        """
        for track in self.tracks:
            if track.title == title:
                self.tracks.remove(track)
                return True
        return False

    def get_total_duration(self) -> int:
        """
        Calculates the total duration of all tracks in the playlist.
        Uses a list comprehension for efficient computation.
        """
        return sum(track.duration for track in self.tracks)

    def play_all(self) -> List[str]:
        """
        Plays all tracks in the playlist.
        Demonstrates polymorphism: calls play() on each track regardless of its specific type.
        """
        return [track.play() for track in self.tracks]

    def shuffle(self) -> None:
        """
        Randomly shuffles the order of tracks in the playlist.
        Modifies the tracks list in-place.
        """
        random.shuffle(self.tracks)


class MusicStreamingService:
    """
    Represents a music streaming service that manages multiple playlists.
    This class demonstrates the use of composition to build a complex system.
    """

    def __init__(self):
        self.playlists: dict[str, Playlist] = {}

    def create_playlist(self, name: str) -> None:
        """
        Creates a new playlist.
        Demonstrates error handling by checking for existing playlists.
        """
        if name not in self.playlists:
            self.playlists[name] = Playlist(name)
        else:
            print(f"Playlist '{name}' already exists.")

    def delete_playlist(self, name: str) -> bool:
        """
        Deletes a playlist by its name.
        Returns True if the playlist was found and deleted, False otherwise.
        """
        return self.playlists.pop(name, None) is not None

    def add_track_to_playlist(self, playlist_name: str, track: AudioTrack) -> bool:
        """
        Adds a track to a specified playlist.
        Demonstrates the interaction between MusicStreamingService, Playlist, and AudioTrack classes.
        """
        if playlist_name in self.playlists:
            self.playlists[playlist_name].add_track(track)
            return True
        return False

    def find_track(self, title: str) -> List[Tuple[str, AudioTrack]]:
        """
        Finds all occurrences of a track across all playlists.
        Demonstrates the use of list comprehensions for complex queries.
        """
        return [(playlist_name, track)
                for playlist_name, playlist in self.playlists.items()
                for track in playlist.tracks
                if track.title == title]

    def get_most_popular_track(self) -> Optional[Tuple[AudioTrack, int]]:
        """
        Finds the track that appears in the most playlists.
        Demonstrates the use of the Counter class for efficient counting.
        """
        all_tracks = [track for playlist in self.playlists.values() for track in playlist.tracks]
        if not all_tracks:
            return None
        track_counts = Counter(all_tracks)
        return track_counts.most_common(1)[0]


# Demonstration of how the classes and functions work together
if __name__ == "__main__":
    # Create instances of Song and Podcast, demonstrating how these classes are used
    song1 = Song("Song 1", "Artist 1", 180, "Album 1")
    song2 = Song("Song 2", "Artist 2", 200, "Album 2")
    podcast1 = Podcast("Podcast 1", "Host 1", 1800, 1)

    # Create an instance of MusicStreamingService
    service = MusicStreamingService()

    # Demonstrate creating playlists and adding tracks
    service.create_playlist("My Favorites")
    service.create_playlist("Workout Mix")
    service.add_track_to_playlist("My Favorites", song1)
    service.add_track_to_playlist("My Favorites", song2)
    service.add_track_to_playlist("Workout Mix", song1)
    service.add_track_to_playlist("Workout Mix", podcast1)

    # Demonstrate finding a track across playlists
    found_tracks = service.find_track("Song 1")
    print("Found 'Song 1' in:", [playlist for playlist, _ in found_tracks])

    # Demonstrate getting the most popular track
    popular_track, count = service.get_most_popular_track()
    print(f"Most popular track: {popular_track.title}, in {count} playlists")

    # Demonstrate playing all tracks in a playlist
    print("\nPlaying 'Workout Mix':")
    for play_output in service.playlists["Workout Mix"].play_all():
        print(play_output)
