"""Unit tests for audio file management."""

import pytest
import tempfile
from pathlib import Path

from rehearsal_track_markers.audio import AudioFileManager
from rehearsal_track_markers.persistence import FileManager


class TestAudioFileManager:
    """Tests for the AudioFileManager class."""

    @staticmethod
    def create_dummy_audio_file(path: Path, content: bytes = b"dummy audio") -> None:
        """Helper to create a dummy audio file for testing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def test_is_supported_format(self) -> None:
        """Test checking if audio format is supported."""
        afm = AudioFileManager()

        # Supported formats
        assert afm.is_supported_format(Path("song.mp3")) is True
        assert afm.is_supported_format(Path("song.wav")) is True
        assert afm.is_supported_format(Path("song.m4a")) is True
        assert afm.is_supported_format(Path("song.flac")) is True
        assert afm.is_supported_format(Path("song.ogg")) is True

        # Unsupported formats
        assert afm.is_supported_format(Path("song.txt")) is False
        assert afm.is_supported_format(Path("song.pdf")) is False
        assert afm.is_supported_format(Path("song.mp4")) is False

        # Case insensitive
        assert afm.is_supported_format(Path("song.MP3")) is True
        assert afm.is_supported_format(Path("song.WaV")) is True

    def test_copy_audio_file(self) -> None:
        """Test copying an audio file to app storage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file manager with temp directory
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            # Create a dummy source file
            source_path = Path(tmpdir) / "source" / "song.mp3"
            self.create_dummy_audio_file(source_path, b"test audio content")

            # Copy the file
            dest_path = afm.copy_audio_file(source_path, "Test Show")

            # Verify destination
            expected_dest = fm.get_show_audio_directory("Test Show") / "song.mp3"
            assert dest_path == expected_dest
            assert dest_path.exists()
            assert dest_path.read_bytes() == b"test audio content"

    def test_copy_audio_file_nonexistent(self) -> None:
        """Test copying a file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            source_path = Path(tmpdir) / "nonexistent.mp3"

            with pytest.raises(FileNotFoundError):
                afm.copy_audio_file(source_path, "Test Show")

    def test_copy_audio_file_unsupported_format(self) -> None:
        """Test copying a file with unsupported format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            source_path = Path(tmpdir) / "source" / "file.txt"
            self.create_dummy_audio_file(source_path)

            with pytest.raises(ValueError, match="Unsupported audio format"):
                afm.copy_audio_file(source_path, "Test Show")

    def test_copy_audio_file_duplicate_identical(self) -> None:
        """Test copying a file that already exists with identical content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            source_path = Path(tmpdir) / "source" / "song.mp3"
            self.create_dummy_audio_file(source_path, b"identical content")

            # Copy file first time
            dest_path1 = afm.copy_audio_file(source_path, "Test Show")

            # Copy again (should detect identical file)
            dest_path2 = afm.copy_audio_file(source_path, "Test Show")

            # Should return same path
            assert dest_path1 == dest_path2

    def test_copy_audio_file_duplicate_different(self) -> None:
        """Test copying a file with same name but different content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            # Copy first file
            source_path1 = Path(tmpdir) / "source1" / "song.mp3"
            self.create_dummy_audio_file(source_path1, b"content 1")
            dest_path1 = afm.copy_audio_file(source_path1, "Test Show")

            # Copy different file with same name
            source_path2 = Path(tmpdir) / "source2" / "song.mp3"
            self.create_dummy_audio_file(source_path2, b"content 2")
            dest_path2 = afm.copy_audio_file(source_path2, "Test Show")

            # Should have different filenames
            assert dest_path1 != dest_path2
            assert dest_path2.name == "song_1.mp3"

            # Verify both files exist with correct content
            assert dest_path1.read_bytes() == b"content 1"
            assert dest_path2.read_bytes() == b"content 2"

    def test_add_audio_file_to_show(self) -> None:
        """Test adding an audio file and creating a Track."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            # Create source file
            source_path = Path(tmpdir) / "source" / "mysong.mp3"
            self.create_dummy_audio_file(source_path)

            # Add to show
            track = afm.add_audio_file_to_show(source_path, "Test Show")

            # Verify Track was created correctly
            assert track.filename == "mysong.mp3"
            assert track.audio_path.exists()
            assert track.audio_path.name == "mysong.mp3"
            assert len(track.markers) == 0

    def test_delete_audio_file(self) -> None:
        """Test deleting an audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            # Create and copy a file
            source_path = Path(tmpdir) / "source" / "song.mp3"
            self.create_dummy_audio_file(source_path)
            dest_path = afm.copy_audio_file(source_path, "Test Show")

            # Verify it exists
            assert dest_path.exists()

            # Delete it
            result = afm.delete_audio_file(dest_path)
            assert result is True
            assert not dest_path.exists()

    def test_delete_nonexistent_audio_file(self) -> None:
        """Test deleting a file that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            afm = AudioFileManager()
            nonexistent_path = Path(tmpdir) / "nonexistent.mp3"

            result = afm.delete_audio_file(nonexistent_path)
            assert result is False

    def test_files_are_identical(self) -> None:
        """Test comparing files for identity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create two identical files
            file1 = Path(tmpdir) / "file1.mp3"
            file2 = Path(tmpdir) / "file2.mp3"
            content = b"identical content here" * 1000  # Make it larger

            file1.write_bytes(content)
            file2.write_bytes(content)

            # Should be identical
            assert AudioFileManager._files_are_identical(file1, file2) is True

            # Create different file
            file3 = Path(tmpdir) / "file3.mp3"
            file3.write_bytes(b"different content")

            # Should be different
            assert AudioFileManager._files_are_identical(file1, file3) is False

    def test_get_unique_filename(self) -> None:
        """Test generating unique filenames."""
        with tempfile.TemporaryDirectory() as tmpdir:
            directory = Path(tmpdir)

            # Create some existing files
            (directory / "song.mp3").touch()
            (directory / "song_1.mp3").touch()
            (directory / "song_2.mp3").touch()

            # Get unique filename
            unique_path = AudioFileManager._get_unique_filename(directory, "song.mp3")

            # Should be song_3.mp3
            assert unique_path.name == "song_3.mp3"
            assert not unique_path.exists()

    def test_multiple_formats(self) -> None:
        """Test copying files with various audio formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fm = FileManager(base_path=Path(tmpdir))
            afm = AudioFileManager(file_manager=fm)

            formats = [".mp3", ".wav", ".m4a", ".flac", ".ogg"]

            for fmt in formats:
                source_path = Path(tmpdir) / f"source/song{fmt}"
                self.create_dummy_audio_file(source_path)

                track = afm.add_audio_file_to_show(source_path, "Test Show")

                assert track.filename == f"song{fmt}"
                assert track.audio_path.exists()
                assert track.audio_path.suffix == fmt
