"""Audio playback engine using Qt Multimedia."""

from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class AudioPlayer(QObject):
    """
    Audio playback engine for rehearsal tracks.

    Provides low-latency playback control, seeking, and position tracking
    using Qt Multimedia (QMediaPlayer).

    Signals:
        position_changed: Emitted when playback position changes (position_ms: int)
        duration_changed: Emitted when track duration is available (duration_ms: int)
        playback_state_changed: Emitted when playback state changes (state: QMediaPlayer.PlaybackState)
        error_occurred: Emitted when a playback error occurs (error_msg: str)
    """

    # Signals for notifying listeners of state changes
    position_changed = Signal(int)  # position in milliseconds
    duration_changed = Signal(int)  # duration in milliseconds
    playback_state_changed = Signal(QMediaPlayer.PlaybackState)
    error_occurred = Signal(str)  # error message

    def __init__(self) -> None:
        """Initialize the audio player."""
        super().__init__()

        # Create media player and audio output
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)

        # Track current state
        self._current_file: Path | None = None
        self._was_playing_before_seek = False

        # Connect internal signals
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.errorOccurred.connect(self._on_error_occurred)

        logger.info("AudioPlayer initialized")

    def load_file(self, file_path: Path) -> bool:
        """
        Load an audio file for playback.

        Args:
            file_path: Path to the audio file

        Returns:
            True if file was loaded successfully, False otherwise
        """
        if not file_path.exists():
            logger.error(f"Cannot load file: does not exist at {file_path}")
            self.error_occurred.emit(f"File not found: {file_path}")
            return False

        try:
            # Stop current playback
            self.stop()

            # Load new file
            url = QUrl.fromLocalFile(str(file_path.resolve()))
            self._player.setSource(url)
            self._current_file = file_path

            logger.info(f"Loaded audio file: {file_path.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to load audio file: {e}")
            self.error_occurred.emit(f"Failed to load file: {e}")
            return False

    def play(self) -> None:
        """Start or resume playback."""
        if self._current_file is None:
            logger.warning("Cannot play: no file loaded")
            return

        self._player.play()
        logger.debug("Playback started")

    def pause(self) -> None:
        """Pause playback."""
        if self._current_file is None:
            logger.warning("Cannot pause: no file loaded")
            return

        self._player.pause()
        logger.debug("Playback paused")

    def stop(self) -> None:
        """Stop playback and reset position to beginning."""
        if self._current_file is None:
            return

        self._player.stop()
        logger.debug("Playback stopped")

    def toggle_play_pause(self) -> None:
        """Toggle between playing and paused states."""
        if self.is_playing():
            self.pause()
        else:
            self.play()

    def seek(self, position_ms: int) -> None:
        """
        Seek to a specific position in the track.

        Args:
            position_ms: Target position in milliseconds

        Notes:
            - Maintains playback state (if playing, continues playing; if paused, stays paused)
            - Clamps position to valid range [0, duration]
        """
        if self._current_file is None:
            logger.warning("Cannot seek: no file loaded")
            return

        # Clamp position to valid range
        duration = self.get_duration_ms()
        if duration > 0:
            position_ms = max(0, min(position_ms, duration))
        else:
            position_ms = max(0, position_ms)

        # Seek to position
        self._player.setPosition(position_ms)
        logger.debug(f"Seeked to position: {position_ms}ms")

    def skip_forward(self, increment_ms: int) -> None:
        """
        Skip forward by a specified amount.

        Args:
            increment_ms: Amount to skip forward in milliseconds
        """
        current_pos = self.get_position_ms()
        new_pos = current_pos + increment_ms
        self.seek(new_pos)

    def skip_backward(self, increment_ms: int) -> None:
        """
        Skip backward by a specified amount.

        Args:
            increment_ms: Amount to skip backward in milliseconds
        """
        current_pos = self.get_position_ms()
        new_pos = current_pos - increment_ms
        self.seek(new_pos)

    def get_position_ms(self) -> int:
        """
        Get current playback position.

        Returns:
            Current position in milliseconds
        """
        return self._player.position()

    def get_duration_ms(self) -> int:
        """
        Get duration of currently loaded track.

        Returns:
            Duration in milliseconds, or 0 if no track loaded or duration unknown
        """
        duration = self._player.duration()
        return duration if duration > 0 else 0

    def is_playing(self) -> bool:
        """
        Check if audio is currently playing.

        Returns:
            True if playing, False otherwise
        """
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState

    def is_paused(self) -> bool:
        """
        Check if audio is currently paused.

        Returns:
            True if paused, False otherwise
        """
        return self._player.playbackState() == QMediaPlayer.PlaybackState.PausedState

    def is_stopped(self) -> bool:
        """
        Check if audio is currently stopped.

        Returns:
            True if stopped, False otherwise
        """
        return self._player.playbackState() == QMediaPlayer.PlaybackState.StoppedState

    def get_playback_state(self) -> QMediaPlayer.PlaybackState:
        """
        Get current playback state.

        Returns:
            Current playback state
        """
        return self._player.playbackState()

    def get_current_file(self) -> Path | None:
        """
        Get the currently loaded file.

        Returns:
            Path to current file, or None if no file loaded
        """
        return self._current_file

    def set_volume(self, volume: float) -> None:
        """
        Set playback volume.

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        volume = max(0.0, min(1.0, volume))
        self._audio_output.setVolume(volume)
        logger.debug(f"Volume set to: {volume}")

    def get_volume(self) -> float:
        """
        Get current playback volume.

        Returns:
            Volume level (0.0 to 1.0)
        """
        return self._audio_output.volume()

    def unload(self) -> None:
        """Unload the current file and clean up resources."""
        self.stop()
        self._player.setSource(QUrl())
        self._current_file = None
        logger.info("Audio file unloaded")

    # Internal signal handlers

    def _on_position_changed(self, position: int) -> None:
        """
        Handle position changes from QMediaPlayer.

        Args:
            position: New position in milliseconds
        """
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int) -> None:
        """
        Handle duration changes from QMediaPlayer.

        Args:
            duration: Track duration in milliseconds
        """
        if duration > 0:
            logger.debug(f"Duration available: {duration}ms")
            self.duration_changed.emit(duration)

    def _on_playback_state_changed(self, state: QMediaPlayer.PlaybackState) -> None:
        """
        Handle playback state changes from QMediaPlayer.

        Args:
            state: New playback state
        """
        state_names = {
            QMediaPlayer.PlaybackState.StoppedState: "Stopped",
            QMediaPlayer.PlaybackState.PlayingState: "Playing",
            QMediaPlayer.PlaybackState.PausedState: "Paused",
        }
        logger.debug(f"Playback state changed: {state_names.get(state, 'Unknown')}")
        self.playback_state_changed.emit(state)

    def _on_error_occurred(self, error: QMediaPlayer.Error, error_string: str) -> None:
        """
        Handle errors from QMediaPlayer.

        Args:
            error: Error code
            error_string: Human-readable error description
        """
        logger.error(f"Media player error: {error_string} (code: {error})")
        self.error_occurred.emit(error_string)

    def __del__(self) -> None:
        """Cleanup when player is destroyed."""
        try:
            self.unload()
        except Exception:
            pass
