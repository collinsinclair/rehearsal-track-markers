"""Marker model for timestamped positions in audio tracks."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Marker:
    """
    A timestamped marker in an audio track.

    Attributes:
        name: The name/label of the marker (must be unique per track)
        timestamp_ms: The timestamp in milliseconds from the start of the track
    """

    name: str
    timestamp_ms: int

    def __post_init__(self) -> None:
        """Validate marker data after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Marker name cannot be empty")

        if self.timestamp_ms < 0:
            raise ValueError("Marker timestamp cannot be negative")

    def to_dict(self) -> dict[str, Any]:
        """
        Convert marker to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the marker
        """
        return {"name": self.name, "timestamp_ms": self.timestamp_ms}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Marker":
        """
        Create a marker from a dictionary.

        Args:
            data: Dictionary containing marker data

        Returns:
            A new Marker instance

        Raises:
            KeyError: If required keys are missing
            ValueError: If data is invalid
        """
        return cls(name=data["name"], timestamp_ms=data["timestamp_ms"])

    def __str__(self) -> str:
        """Return string representation of marker."""
        seconds = self.timestamp_ms / 1000
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{self.name} ({minutes}:{secs:05.2f})"
