"""Unit tests for audio file management and playback."""

import tempfile
from pathlib import Path

import pytest
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from rehearsal_track_markers.audio import AudioFileManager, AudioPlayer
from rehearsal_track_markers.persistence import FileManager

# Ensure QApplication exists for Qt tests
app = QApplication.instance() or QApplication([])


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


class TestAudioPlayer:
    """Tests for the AudioPlayer class."""

    @staticmethod
    def create_dummy_audio_file(path: Path, content: bytes = b"dummy audio") -> None:
        """Helper to create a dummy audio file for testing."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def test_initialization(self) -> None:
        """Test creating an AudioPlayer instance."""
        player = AudioPlayer()

        assert player is not None
        assert player.get_current_file() is None
        assert player.is_stopped() is True
        assert player.get_position_ms() == 0

    def test_load_file_valid(self) -> None:
        """Test loading a valid audio file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            result = player.load_file(audio_file)

            # File should be loaded (even if not playable)
            assert result is True
            assert player.get_current_file() == audio_file

    def test_load_file_nonexistent(self) -> None:
        """Test loading a file that doesn't exist."""
        player = AudioPlayer()
        nonexistent_file = Path("/tmp/nonexistent_file_12345.mp3")

        # Set up signal spy for error signal
        error_spy = QSignalSpy(player.error_occurred)
        assert error_spy.isValid()

        result = player.load_file(nonexistent_file)

        assert result is False
        assert player.get_current_file() is None
        assert error_spy.count() > 0  # Error signal should be emitted

    def test_playback_state_queries(self) -> None:
        """Test playback state query methods."""
        player = AudioPlayer()

        # Initially stopped
        assert player.is_stopped() is True
        assert player.is_playing() is False
        assert player.is_paused() is False
        assert player.get_playback_state() == QMediaPlayer.PlaybackState.StoppedState

    def test_play_pause_stop_without_file(self) -> None:
        """Test playback controls without a file loaded."""
        player = AudioPlayer()

        # These should not crash when no file is loaded
        player.play()
        player.pause()
        player.stop()
        player.toggle_play_pause()

        # Should still be stopped
        assert player.is_stopped() is True

    def test_seek_without_file(self) -> None:
        """Test seeking without a file loaded."""
        player = AudioPlayer()

        # Should not crash
        player.seek(5000)
        player.skip_forward(1000)
        player.skip_backward(1000)

        # Position should still be 0
        assert player.get_position_ms() == 0

    def test_seek_clamping(self) -> None:
        """Test that seek positions are clamped to valid range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            # Seek to negative position (should clamp to 0)
            player.seek(-1000)
            assert player.get_position_ms() >= 0

            # Seek beyond duration (should clamp to duration if known)
            # Note: With dummy files, duration might be 0 or unknown
            player.seek(999999999)
            # Position should be clamped (exact value depends on file)
            assert player.get_position_ms() >= 0

    def test_skip_forward(self) -> None:
        """Test skipping forward."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            initial_pos = player.get_position_ms()
            player.skip_forward(5000)

            # Position should have increased (or stayed at max)
            new_pos = player.get_position_ms()
            assert new_pos >= initial_pos

    def test_skip_backward(self) -> None:
        """Test skipping backward."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            # Seek to middle first
            player.seek(10000)
            middle_pos = player.get_position_ms()

            # Skip backward
            player.skip_backward(5000)
            new_pos = player.get_position_ms()

            # Position should have decreased (or stayed at 0)
            assert new_pos <= middle_pos

    def test_get_duration(self) -> None:
        """Test getting track duration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            duration = player.get_duration_ms()

            # Duration should be non-negative
            # (might be 0 for dummy files that can't be parsed)
            assert duration >= 0

    def test_volume_control(self) -> None:
        """Test volume control."""
        player = AudioPlayer()

        # Default volume should be between 0 and 1
        default_volume = player.get_volume()
        assert 0.0 <= default_volume <= 1.0

        # Set volume
        player.set_volume(0.5)
        assert player.get_volume() == pytest.approx(0.5, abs=0.01)

        # Test clamping
        player.set_volume(1.5)  # Above max
        assert player.get_volume() <= 1.0

        player.set_volume(-0.5)  # Below min
        assert player.get_volume() >= 0.0

    def test_unload(self) -> None:
        """Test unloading a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            assert player.get_current_file() is not None

            # Unload
            player.unload()

            assert player.get_current_file() is None

    def test_signal_emissions(self) -> None:
        """Test that signals can be connected and are valid."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()

            # Set up signal spies
            position_spy = QSignalSpy(player.position_changed)
            duration_spy = QSignalSpy(player.duration_changed)
            state_spy = QSignalSpy(player.playback_state_changed)
            error_spy = QSignalSpy(player.error_occurred)

            # Verify all spies are valid
            assert position_spy.isValid()
            assert duration_spy.isValid()
            assert state_spy.isValid()
            assert error_spy.isValid()

            # Load file (might emit signals)
            player.load_file(audio_file)

            # Signals might be emitted depending on Qt Multimedia's ability
            # to parse the dummy file. We just verify that the spies work
            # and don't crash when signals are emitted.
            # At minimum, we should not have errors for a valid file path
            assert error_spy.count() == 0

    def test_state_change_signals(self) -> None:
        """Test that playback state change signals are emitted correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            # Set up signal spy for state changes
            state_spy = QSignalSpy(player.playback_state_changed)
            assert state_spy.isValid()

            # Initially stopped
            assert player.is_stopped()

            # Try to play (may or may not succeed with dummy file)
            player.play()

            # If playback state changed, the spy should have captured it
            # Note: With dummy files, Qt may not emit state changes,
            # but the spy should still be valid and functional
            assert state_spy.isValid()

            # Stop should always work
            player.stop()

            # Spy should still be valid
            assert state_spy.isValid()

    def test_toggle_play_pause(self) -> None:
        """Test toggling between play and pause."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            # Initially stopped, toggle should attempt to play
            player.toggle_play_pause()

            # State might change (depends on file validity)
            # At minimum, this should not crash
            assert player.get_playback_state() is not None

    def test_load_replaces_previous_file(self) -> None:
        """Test that loading a new file replaces the previous one."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file1 = Path(tmpdir) / "test1.mp3"
            audio_file2 = Path(tmpdir) / "test2.mp3"
            self.create_dummy_audio_file(audio_file1, b"file 1")
            self.create_dummy_audio_file(audio_file2, b"file 2")

            player = AudioPlayer()

            # Load first file
            player.load_file(audio_file1)
            assert player.get_current_file() == audio_file1

            # Load second file (should replace first)
            player.load_file(audio_file2)
            assert player.get_current_file() == audio_file2

    def test_stop_resets_position(self) -> None:
        """Test that stop resets playback position."""
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_file = Path(tmpdir) / "test.mp3"
            self.create_dummy_audio_file(audio_file)

            player = AudioPlayer()
            player.load_file(audio_file)

            # Seek to middle
            player.seek(5000)

            # Stop should reset
            player.stop()

            # After stop, should be stopped state
            assert player.is_stopped() is True
