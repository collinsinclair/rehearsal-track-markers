"""Track model for audio files with markers."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .marker import Marker


@dataclass
class Track:
    """
    An audio track with associated markers.

    Attributes:
        filename: Original filename of the audio file
        audio_path: Path to the audio file in app storage
        markers: Ordered list of markers for this track
        duration_ms: Duration of the track in milliseconds (optional metadata)
    """

    filename: str
    audio_path: Path
    markers: list[Marker] = field(default_factory=list)
    duration_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate track data after initialization."""
        if not self.filename or not self.filename.strip():
            raise ValueError("Track filename cannot be empty")

        # Ensure audio_path is a Path object
        if isinstance(self.audio_path, str):
            self.audio_path = Path(self.audio_path)

    def add_marker(self, marker: Marker) -> None:
        """
        Add a marker to this track.

        Args:
            marker: The marker to add

        Raises:
            ValueError: If a marker with the same name already exists
        """
        if self.has_marker(marker.name):
            raise ValueError(f"Marker with name '{marker.name}' already exists")

        self.markers.append(marker)
        # Keep markers sorted by timestamp
        self.markers.sort(key=lambda m: m.timestamp_ms)

    def remove_marker(self, name: str) -> bool:
        """
        Remove a marker by name.

        Args:
            name: The name of the marker to remove

        Returns:
            True if marker was removed, False if not found
        """
        for i, marker in enumerate(self.markers):
            if marker.name == name:
                del self.markers[i]
                return True
        return False

    def get_marker(self, name: str) -> Marker | None:
        """
        Get a marker by name.

        Args:
            name: The name of the marker to find

        Returns:
            The marker if found, None otherwise
        """
        for marker in self.markers:
            if marker.name == name:
                return marker
        return None

    def has_marker(self, name: str) -> bool:
        """
        Check if a marker with the given name exists.

        Args:
            name: The name to check

        Returns:
            True if marker exists, False otherwise
        """
        return any(marker.name == name for marker in self.markers)

    def rename_marker(self, old_name: str, new_name: str) -> bool:
        """
        Rename a marker.

        Args:
            old_name: Current name of the marker
            new_name: New name for the marker

        Returns:
            True if marker was renamed, False if old marker not found

        Raises:
            ValueError: If new_name is empty or already exists
        """
        if not new_name or not new_name.strip():
            raise ValueError("New marker name cannot be empty")

        if old_name != new_name and self.has_marker(new_name):
            raise ValueError(f"Marker with name '{new_name}' already exists")

        marker = self.get_marker(old_name)
        if marker:
            marker.name = new_name
            return True
        return False

    def to_dict(self) -> dict[str, Any]:
        """
        Convert track to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the track
        """
        result: dict[str, Any] = {
            "filename": self.filename,
            "markers": [m.to_dict() for m in self.markers],
        }

        if self.duration_ms is not None:
            result["duration_ms"] = self.duration_ms

        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any], audio_path: Path) -> "Track":
        """
        Create a track from a dictionary.

        Args:
            data: Dictionary containing track data
            audio_path: Path to the audio file in app storage

        Returns:
            A new Track instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        markers = [Marker.from_dict(m) for m in data.get("markers", [])]

        return cls(
            filename=data["filename"],
            audio_path=audio_path,
            markers=markers,
            duration_ms=data.get("duration_ms"),
        )

    def __str__(self) -> str:
        """Return string representation of track."""
        return f"Track: {self.filename} ({len(self.markers)} markers)"
