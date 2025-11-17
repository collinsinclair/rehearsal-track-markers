"""Show model representing a production with multiple tracks."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .track import Track


@dataclass
class Settings:
    """
    User-configurable settings for a show.

    Attributes:
        skip_increment_seconds: Seconds to skip forward/backward
        marker_nudge_increment_ms: Milliseconds to nudge marker position
    """

    skip_increment_seconds: int = 5
    marker_nudge_increment_ms: int = 100

    def __post_init__(self) -> None:
        """Validate settings after initialization."""
        if self.skip_increment_seconds <= 0:
            raise ValueError("Skip increment must be positive")
        if self.marker_nudge_increment_ms <= 0:
            raise ValueError("Marker nudge increment must be positive")

    def to_dict(self) -> dict[str, Any]:
        """Convert settings to dictionary."""
        return {
            "skip_increment_seconds": self.skip_increment_seconds,
            "marker_nudge_increment_ms": self.marker_nudge_increment_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Settings":
        """Create settings from dictionary."""
        return cls(
            skip_increment_seconds=data.get("skip_increment_seconds", 5),
            marker_nudge_increment_ms=data.get("marker_nudge_increment_ms", 100),
        )


@dataclass
class Show:
    """
    A show/production containing multiple audio tracks.

    Attributes:
        name: Name of the show/production
        tracks: Ordered list of tracks in the show
        settings: User-configurable settings
    """

    name: str
    tracks: list[Track] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)

    def __post_init__(self) -> None:
        """Validate show data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Show name cannot be empty")

    def add_track(self, track: Track) -> None:
        """
        Add a track to the show.

        Args:
            track: The track to add
        """
        self.tracks.append(track)

    def remove_track(self, index: int) -> bool:
        """
        Remove a track by index.

        Args:
            index: Index of the track to remove

        Returns:
            True if track was removed, False if index invalid
        """
        if 0 <= index < len(self.tracks):
            del self.tracks[index]
            return True
        return False

    def remove_track_by_filename(self, filename: str) -> bool:
        """
        Remove a track by filename.

        Args:
            filename: Filename of the track to remove

        Returns:
            True if track was removed, False if not found
        """
        for i, track in enumerate(self.tracks):
            if track.filename == filename:
                del self.tracks[i]
                return True
        return False

    def get_track(self, index: int) -> Track | None:
        """
        Get a track by index.

        Args:
            index: Index of the track to get

        Returns:
            The track if found, None otherwise
        """
        if 0 <= index < len(self.tracks):
            return self.tracks[index]
        return None

    def reorder_track(self, from_index: int, to_index: int) -> bool:
        """
        Reorder a track from one position to another.

        Args:
            from_index: Current index of the track
            to_index: New index for the track

        Returns:
            True if track was reordered, False if indices invalid
        """
        if (
            0 <= from_index < len(self.tracks)
            and 0 <= to_index < len(self.tracks)
            and from_index != to_index
        ):
            track = self.tracks.pop(from_index)
            self.tracks.insert(to_index, track)
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert show to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the show
        """
        return {
            "show_name": self.name,
            "settings": self.settings.to_dict(),
            "tracks": [track.to_dict() for track in self.tracks],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], audio_base_path: Path) -> "Show":
        """
        Create a show from a dictionary.

        Args:
            data: Dictionary containing show data
            audio_base_path: Base path for audio files (show's audio directory)

        Returns:
            A new Show instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        settings = Settings.from_dict(data.get("settings", {}))

        tracks = []
        for track_data in data.get("tracks", []):
            audio_path = audio_base_path / track_data["filename"]
            tracks.append(Track.from_dict(track_data, audio_path))

        return cls(name=data["show_name"], tracks=tracks, settings=settings)

    def __str__(self) -> str:
        """Return string representation of show."""
        return f"Show: {self.name} ({len(self.tracks)} tracks)"
