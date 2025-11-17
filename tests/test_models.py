"""Unit tests for data models."""

from pathlib import Path

import pytest

from rehearsal_track_markers.models import Marker, Track, Show
from rehearsal_track_markers.models.show import Settings


class TestMarker:
    """Tests for the Marker model."""

    def test_marker_creation(self) -> None:
        """Test creating a valid marker."""
        marker = Marker(name="Measure 42", timestamp_ms=15000)
        assert marker.name == "Measure 42"
        assert marker.timestamp_ms == 15000

    def test_marker_empty_name(self) -> None:
        """Test that empty marker names raise ValueError."""
        with pytest.raises(ValueError, match="Marker name cannot be empty"):
            Marker(name="", timestamp_ms=1000)

        with pytest.raises(ValueError, match="Marker name cannot be empty"):
            Marker(name="   ", timestamp_ms=1000)

    def test_marker_negative_timestamp(self) -> None:
        """Test that negative timestamps raise ValueError."""
        with pytest.raises(ValueError, match="Marker timestamp cannot be negative"):
            Marker(name="Test", timestamp_ms=-100)

    def test_marker_to_dict(self) -> None:
        """Test marker serialization to dictionary."""
        marker = Marker(name="Reh A", timestamp_ms=5000)
        data = marker.to_dict()
        assert data == {"name": "Reh A", "timestamp_ms": 5000}

    def test_marker_from_dict(self) -> None:
        """Test marker deserialization from dictionary."""
        data = {"name": "Reh B", "timestamp_ms": 10000}
        marker = Marker.from_dict(data)
        assert marker.name == "Reh B"
        assert marker.timestamp_ms == 10000

    def test_marker_str(self) -> None:
        """Test marker string representation."""
        marker = Marker(name="Test", timestamp_ms=125000)  # 2:05
        result = str(marker)
        assert "Test" in result
        assert "2:" in result


class TestTrack:
    """Tests for the Track model."""

    def test_track_creation(self) -> None:
        """Test creating a valid track."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        assert track.filename == "song.mp3"
        assert track.audio_path == Path("/path/to/song.mp3")
        assert len(track.markers) == 0

    def test_track_empty_filename(self) -> None:
        """Test that empty filenames raise ValueError."""
        with pytest.raises(ValueError, match="Track filename cannot be empty"):
            Track(filename="", audio_path=Path("/path"))

    def test_track_add_marker(self) -> None:
        """Test adding markers to a track."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        marker1 = Marker(name="Intro", timestamp_ms=0)
        marker2 = Marker(name="Chorus", timestamp_ms=5000)

        track.add_marker(marker1)
        track.add_marker(marker2)

        assert len(track.markers) == 2
        assert track.markers[0].name == "Intro"
        assert track.markers[1].name == "Chorus"

    def test_track_markers_sorted_by_timestamp(self) -> None:
        """Test that markers are automatically sorted by timestamp."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))

        # Add markers out of order
        track.add_marker(Marker(name="End", timestamp_ms=10000))
        track.add_marker(Marker(name="Start", timestamp_ms=0))
        track.add_marker(Marker(name="Middle", timestamp_ms=5000))

        assert track.markers[0].name == "Start"
        assert track.markers[1].name == "Middle"
        assert track.markers[2].name == "End"

    def test_track_duplicate_marker_name(self) -> None:
        """Test that duplicate marker names raise ValueError."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        track.add_marker(Marker(name="Reh A", timestamp_ms=1000))

        with pytest.raises(ValueError, match="already exists"):
            track.add_marker(Marker(name="Reh A", timestamp_ms=2000))

    def test_track_remove_marker(self) -> None:
        """Test removing markers from a track."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        track.add_marker(Marker(name="Intro", timestamp_ms=0))
        track.add_marker(Marker(name="Outro", timestamp_ms=5000))

        result = track.remove_marker("Intro")
        assert result is True
        assert len(track.markers) == 1
        assert track.markers[0].name == "Outro"

        result = track.remove_marker("NonExistent")
        assert result is False

    def test_track_get_marker(self) -> None:
        """Test getting a marker by name."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        marker = Marker(name="Test", timestamp_ms=1000)
        track.add_marker(marker)

        found = track.get_marker("Test")
        assert found is not None
        assert found.name == "Test"

        not_found = track.get_marker("NonExistent")
        assert not_found is None

    def test_track_has_marker(self) -> None:
        """Test checking if a marker exists."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        track.add_marker(Marker(name="Test", timestamp_ms=1000))

        assert track.has_marker("Test") is True
        assert track.has_marker("NonExistent") is False

    def test_track_rename_marker(self) -> None:
        """Test renaming a marker."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        track.add_marker(Marker(name="OldName", timestamp_ms=1000))

        result = track.rename_marker("OldName", "NewName")
        assert result is True
        assert track.has_marker("NewName")
        assert not track.has_marker("OldName")

    def test_track_rename_marker_duplicate(self) -> None:
        """Test that renaming to existing name raises ValueError."""
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))
        track.add_marker(Marker(name="Name1", timestamp_ms=1000))
        track.add_marker(Marker(name="Name2", timestamp_ms=2000))

        with pytest.raises(ValueError, match="already exists"):
            track.rename_marker("Name1", "Name2")

    def test_track_to_dict(self) -> None:
        """Test track serialization to dictionary."""
        track = Track(
            filename="song.mp3",
            audio_path=Path("/path/to/song.mp3"),
            duration_ms=60000,
        )
        track.add_marker(Marker(name="Start", timestamp_ms=0))

        data = track.to_dict()
        assert data["filename"] == "song.mp3"
        assert data["duration_ms"] == 60000
        assert len(data["markers"]) == 1
        assert data["markers"][0]["name"] == "Start"

    def test_track_from_dict(self) -> None:
        """Test track deserialization from dictionary."""
        data = {
            "filename": "song.mp3",
            "duration_ms": 60000,
            "markers": [{"name": "Start", "timestamp_ms": 0}],
        }
        track = Track.from_dict(data, Path("/path/to/song.mp3"))

        assert track.filename == "song.mp3"
        assert track.duration_ms == 60000
        assert len(track.markers) == 1
        assert track.markers[0].name == "Start"


class TestSettings:
    """Tests for the Settings model."""

    def test_settings_default(self) -> None:
        """Test default settings values."""
        settings = Settings()
        assert settings.skip_increment_seconds == 5
        assert settings.marker_nudge_increment_ms == 100

    def test_settings_custom(self) -> None:
        """Test custom settings values."""
        settings = Settings(skip_increment_seconds=10, marker_nudge_increment_ms=50)
        assert settings.skip_increment_seconds == 10
        assert settings.marker_nudge_increment_ms == 50

    def test_settings_invalid_values(self) -> None:
        """Test that invalid settings raise ValueError."""
        with pytest.raises(ValueError, match="Skip increment must be positive"):
            Settings(skip_increment_seconds=0)

        with pytest.raises(ValueError, match="Marker nudge increment must be positive"):
            Settings(marker_nudge_increment_ms=-1)

    def test_settings_to_dict(self) -> None:
        """Test settings serialization."""
        settings = Settings(skip_increment_seconds=10, marker_nudge_increment_ms=50)
        data = settings.to_dict()
        assert data["skip_increment_seconds"] == 10
        assert data["marker_nudge_increment_ms"] == 50

    def test_settings_from_dict(self) -> None:
        """Test settings deserialization."""
        data = {"skip_increment_seconds": 10, "marker_nudge_increment_ms": 50}
        settings = Settings.from_dict(data)
        assert settings.skip_increment_seconds == 10
        assert settings.marker_nudge_increment_ms == 50


class TestShow:
    """Tests for the Show model."""

    def test_show_creation(self) -> None:
        """Test creating a valid show."""
        show = Show(name="Into the Woods")
        assert show.name == "Into the Woods"
        assert len(show.tracks) == 0
        assert show.settings.skip_increment_seconds == 5

    def test_show_empty_name(self) -> None:
        """Test that empty show names raise ValueError."""
        with pytest.raises(ValueError, match="Show name cannot be empty"):
            Show(name="")

    def test_show_add_track(self) -> None:
        """Test adding tracks to a show."""
        show = Show(name="Test Show")
        track = Track(filename="song.mp3", audio_path=Path("/path/to/song.mp3"))

        show.add_track(track)
        assert len(show.tracks) == 1
        assert show.tracks[0].filename == "song.mp3"

    def test_show_remove_track(self) -> None:
        """Test removing tracks by index."""
        show = Show(name="Test Show")
        show.add_track(Track(filename="song1.mp3", audio_path=Path("/path/1.mp3")))
        show.add_track(Track(filename="song2.mp3", audio_path=Path("/path/2.mp3")))

        result = show.remove_track(0)
        assert result is True
        assert len(show.tracks) == 1
        assert show.tracks[0].filename == "song2.mp3"

        result = show.remove_track(10)
        assert result is False

    def test_show_remove_track_by_filename(self) -> None:
        """Test removing tracks by filename."""
        show = Show(name="Test Show")
        show.add_track(Track(filename="song1.mp3", audio_path=Path("/path/1.mp3")))
        show.add_track(Track(filename="song2.mp3", audio_path=Path("/path/2.mp3")))

        result = show.remove_track_by_filename("song1.mp3")
        assert result is True
        assert len(show.tracks) == 1

        result = show.remove_track_by_filename("nonexistent.mp3")
        assert result is False

    def test_show_get_track(self) -> None:
        """Test getting a track by index."""
        show = Show(name="Test Show")
        track = Track(filename="song.mp3", audio_path=Path("/path/song.mp3"))
        show.add_track(track)

        found = show.get_track(0)
        assert found is not None
        assert found.filename == "song.mp3"

        not_found = show.get_track(10)
        assert not_found is None

    def test_show_reorder_track(self) -> None:
        """Test reordering tracks."""
        show = Show(name="Test Show")
        show.add_track(Track(filename="song1.mp3", audio_path=Path("/path/1.mp3")))
        show.add_track(Track(filename="song2.mp3", audio_path=Path("/path/2.mp3")))
        show.add_track(Track(filename="song3.mp3", audio_path=Path("/path/3.mp3")))

        # Move first track to last position
        result = show.reorder_track(0, 2)
        assert result is True
        assert show.tracks[0].filename == "song2.mp3"
        assert show.tracks[1].filename == "song3.mp3"
        assert show.tracks[2].filename == "song1.mp3"

    def test_show_to_dict(self) -> None:
        """Test show serialization to dictionary."""
        show = Show(name="Test Show")
        track = Track(filename="song.mp3", audio_path=Path("/path/song.mp3"))
        track.add_marker(Marker(name="Start", timestamp_ms=0))
        show.add_track(track)

        data = show.to_dict()
        assert data["show_name"] == "Test Show"
        assert "settings" in data
        assert len(data["tracks"]) == 1
        assert data["tracks"][0]["filename"] == "song.mp3"

    def test_show_from_dict(self) -> None:
        """Test show deserialization from dictionary."""
        data = {
            "show_name": "Test Show",
            "settings": {"skip_increment_seconds": 10, "marker_nudge_increment_ms": 50},
            "tracks": [
                {
                    "filename": "song.mp3",
                    "markers": [{"name": "Start", "timestamp_ms": 0}],
                }
            ],
        }

        show = Show.from_dict(data, Path("/path/to/audio"))
        assert show.name == "Test Show"
        assert show.settings.skip_increment_seconds == 10
        assert len(show.tracks) == 1
        assert show.tracks[0].filename == "song.mp3"
        assert len(show.tracks[0].markers) == 1
