"""Unit tests for persistence layer."""

import json
import tempfile
from pathlib import Path

import pytest

from rehearsal_track_markers.models import Marker, Track, Show
from rehearsal_track_markers.persistence import FileManager, ShowRepository


class TestFileManager:
    """Tests for the FileManager class."""

    def test_custom_base_path(self) -> None:
        """Test creating FileManager with custom base path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_path = Path(tmpdir)
            fm = FileManager(base_path=base_path)
            assert fm.base_path == base_path

    def test_get_shows_directory(self) -> None:
        """Test getting shows directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            shows_dir = fm.get_shows_directory()
            assert shows_dir == Path(tmpdir) / "shows"

    def test_get_show_directory(self) -> None:
        """Test getting specific show directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            show_dir = fm.get_show_directory("Test Show")
            assert show_dir == Path(tmpdir) / "shows" / "Test Show"

    def test_get_show_audio_directory(self) -> None:
        """Test getting show's audio directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            audio_dir = fm.get_show_audio_directory("Test Show")
            assert audio_dir == Path(tmpdir) / "shows" / "Test Show" / "audio"

    def test_get_show_file_path(self) -> None:
        """Test getting show's JSON file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            file_path = fm.get_show_file_path("Test Show")
            assert file_path == Path(tmpdir) / "shows" / "Test Show" / "Test Show.json"

    def test_create_show_directories(self) -> None:
        """Test creating show directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            fm.create_show_directories("Test Show")

            show_dir = fm.get_show_directory("Test Show")
            audio_dir = fm.get_show_audio_directory("Test Show")

            assert show_dir.exists()
            assert show_dir.is_dir()
            assert audio_dir.exists()
            assert audio_dir.is_dir()

    def test_show_exists(self) -> None:
        """Test checking if show exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))

            # Show doesn't exist initially
            assert fm.show_exists("Test Show") is False

            # Create show directories and file
            fm.create_show_directories("Test Show")
            show_file = fm.get_show_file_path("Test Show")
            show_file.write_text("{}")

            # Now show exists
            assert fm.show_exists("Test Show") is True

    def test_list_shows(self) -> None:
        """Test listing all shows."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))

            # No shows initially
            assert fm.list_shows() == []

            # Create multiple shows
            for show_name in ["Show A", "Show B", "Show C"]:
                fm.create_show_directories(show_name)
                show_file = fm.get_show_file_path(show_name)
                show_file.write_text("{}")

            # List shows
            shows = fm.list_shows()
            assert len(shows) == 3
            assert "Show A" in shows
            assert "Show B" in shows
            assert "Show C" in shows

    def test_delete_show(self) -> None:
        """Test deleting a show."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))

            # Create a show
            fm.create_show_directories("Test Show")
            show_file = fm.get_show_file_path("Test Show")
            show_file.write_text("{}")

            # Verify it exists
            assert fm.show_exists("Test Show")

            # Delete the show
            result = fm.delete_show("Test Show")
            assert result is True

            # Verify it's gone
            assert not fm.show_exists("Test Show")
            assert not fm.get_show_directory("Test Show").exists()

    def test_delete_nonexistent_show(self) -> None:
        """Test deleting a show that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            result = fm.delete_show("Nonexistent Show")
            assert result is False


class TestShowRepository:
    """Tests for the ShowRepository class."""

    def test_save_and_load_show(self) -> None:
        """Test saving and loading a show."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Create a show with tracks and markers
            show = Show(name="Test Show")
            track = Track(filename="song.mp3", audio_path=Path("/dummy/path.mp3"))
            track.add_marker(Marker(name="Intro", timestamp_ms=0))
            track.add_marker(Marker(name="Chorus", timestamp_ms=5000))
            show.add_track(track)

            # Save the show
            repo.save(show)

            # Verify file was created
            assert fm.show_exists("Test Show")

            # Load the show
            loaded_show = repo.load("Test Show")

            # Verify data
            assert loaded_show.name == "Test Show"
            assert len(loaded_show.tracks) == 1
            assert loaded_show.tracks[0].filename == "song.mp3"
            assert len(loaded_show.tracks[0].markers) == 2
            assert loaded_show.tracks[0].markers[0].name == "Intro"
            assert loaded_show.tracks[0].markers[1].name == "Chorus"

    def test_load_nonexistent_show(self) -> None:
        """Test loading a show that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            with pytest.raises(FileNotFoundError):
                repo.load("Nonexistent Show")

    def test_exists(self) -> None:
        """Test checking if show exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Show doesn't exist initially
            assert repo.exists("Test Show") is False

            # Create and save a show
            show = Show(name="Test Show")
            repo.save(show)

            # Now it exists
            assert repo.exists("Test Show") is True

    def test_delete(self) -> None:
        """Test deleting a show through repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Create and save a show
            show = Show(name="Test Show")
            repo.save(show)

            # Delete it
            result = repo.delete("Test Show")
            assert result is True
            assert not repo.exists("Test Show")

    def test_list_shows(self) -> None:
        """Test listing shows through repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Create multiple shows
            for name in ["Show A", "Show B", "Show C"]:
                show = Show(name=name)
                repo.save(show)

            # List shows
            shows = repo.list_shows()
            assert len(shows) == 3
            assert "Show A" in shows

    def test_export_show(self) -> None:
        """Test exporting a show to external JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Create a show
            show = Show(name="Test Show")
            track = Track(filename="song.mp3", audio_path=Path("/dummy/path.mp3"))
            track.add_marker(Marker(name="Test", timestamp_ms=1000))
            show.add_track(track)

            # Export to external file
            export_path = Path(tmpdir) / "exported" / "show.json"
            repo.export_show(show, export_path)

            # Verify export file exists and contains data
            assert export_path.exists()

            with open(export_path, "r") as f:
                data = json.load(f)

            assert data["show_name"] == "Test Show"
            assert len(data["tracks"]) == 1

    def test_import_show(self) -> None:
        """Test importing a show from external JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an export file manually
            export_data = {
                "show_name": "Imported Show",
                "settings": {
                    "skip_increment_seconds": 10,
                    "marker_nudge_increment_ms": 50,
                },
                "tracks": [
                    {
                        "filename": "song.mp3",
                        "markers": [{"name": "Test", "timestamp_ms": 1000}],
                    }
                ],
            }

            import_path = Path(tmpdir) / "import.json"
            with open(import_path, "w") as f:
                json.dump(export_data, f)

            # Import the show
            repo = ShowRepository()
            show = repo.import_show(import_path)

            # Verify imported data
            assert show.name == "Imported Show"
            assert show.settings.skip_increment_seconds == 10
            assert len(show.tracks) == 1
            assert show.tracks[0].filename == "song.mp3"

    def test_json_round_trip(self) -> None:
        """Test that save/load produces identical data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            repo = ShowRepository(file_manager=fm)

            # Create a complex show
            show = Show(name="Complex Show")
            show.settings.skip_increment_seconds = 10
            show.settings.marker_nudge_increment_ms = 200

            for i in range(3):
                track = Track(
                    filename=f"song{i}.mp3", audio_path=Path(f"/dummy/song{i}.mp3")
                )
                for j in range(5):
                    track.add_marker(
                        Marker(name=f"Marker {i}-{j}", timestamp_ms=j * 1000)
                    )
                show.add_track(track)

            # Save and load
            repo.save(show)
            loaded_show = repo.load("Complex Show")

            # Verify all data matches
            assert loaded_show.name == show.name
            assert (
                loaded_show.settings.skip_increment_seconds
                == show.settings.skip_increment_seconds
            )
            assert (
                loaded_show.settings.marker_nudge_increment_ms
                == show.settings.marker_nudge_increment_ms
            )
            assert len(loaded_show.tracks) == len(show.tracks)

            for orig_track, loaded_track in zip(show.tracks, loaded_show.tracks):
                assert loaded_track.filename == orig_track.filename
                assert len(loaded_track.markers) == len(orig_track.markers)

                for orig_marker, loaded_marker in zip(
                    orig_track.markers, loaded_track.markers
                ):
                    assert loaded_marker.name == orig_marker.name
                    assert loaded_marker.timestamp_ms == orig_marker.timestamp_ms
