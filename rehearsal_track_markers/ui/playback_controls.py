"""Playback controls widget for audio playback."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .marker_progress_bar import MarkerProgressBar
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class PlaybackControls(QWidget):
    """
    Widget for audio playback controls.

    Features:
    - Track title display
    - Play/Pause/Skip buttons
    - Progress bar with marker ticks
    - Time display (current / total)

    Signals:
        play_clicked: Emitted when play button is clicked
        pause_clicked: Emitted when pause button is clicked
        skip_forward_clicked: Emitted when skip forward button is clicked
        skip_backward_clicked: Emitted when skip backward button is clicked
        position_changed: Emitted when user scrubs the progress bar (position_ms: int)
    """

    # Signals
    play_clicked = Signal()
    pause_clicked = Signal()
    skip_forward_clicked = Signal()
    skip_backward_clicked = Signal()
    position_changed = Signal(int)  # Position in milliseconds

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the playback controls.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._connect_signals()

        logger.debug("PlaybackControls initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)

        # Track title
        self._track_title = QLabel("No track selected")
        self._track_title.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self._track_title)

        # Playback buttons
        button_layout = QHBoxLayout()

        self._play_button = QPushButton("Play")
        self._play_button.setToolTip("Start playback (or press Space)")

        self._pause_button = QPushButton("Pause")
        self._pause_button.setToolTip("Pause playback (or press Space)")

        self._skip_back_button = QPushButton("<<5s")
        self._skip_back_button.setToolTip("Skip backward by configured increment")

        self._skip_forward_button = QPushButton("5s>>")
        self._skip_forward_button.setToolTip("Skip forward by configured increment")

        button_layout.addWidget(self._play_button)
        button_layout.addWidget(self._pause_button)
        button_layout.addWidget(self._skip_back_button)
        button_layout.addWidget(self._skip_forward_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Progress bar with marker visualization
        self._progress_slider = MarkerProgressBar(Qt.Orientation.Horizontal)
        self._progress_slider.setRange(0, 0)  # Will be updated when track loads
        self._progress_slider.setValue(0)
        self._progress_slider.setToolTip(
            "Click or drag to scrub through the track\n"
            "Red markers indicate saved positions"
        )
        layout.addWidget(self._progress_slider)

        # Time display
        self._time_label = QLabel("0:00 / 0:00")
        self._time_label.setStyleSheet("color: gray;")
        layout.addWidget(self._time_label)

        # Add stretch to push everything to the top
        layout.addStretch()

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._play_button.clicked.connect(self._on_play_clicked)
        self._pause_button.clicked.connect(self._on_pause_clicked)
        self._skip_forward_button.clicked.connect(self._on_skip_forward_clicked)
        self._skip_back_button.clicked.connect(self._on_skip_backward_clicked)
        self._progress_slider.sliderMoved.connect(self._on_slider_moved)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)

    def set_track_title(self, title: str) -> None:
        """
        Set the track title display.

        Args:
            title: Track title to display
        """
        self._track_title.setText(title)

    def set_position(self, position_ms: int) -> None:
        """
        Set the current playback position.

        Args:
            position_ms: Position in milliseconds
        """
        # Block signals to avoid feedback loop
        self._progress_slider.blockSignals(True)

        # Slider range is in milliseconds, so set value directly
        self._progress_slider.setValue(position_ms)

        self._progress_slider.blockSignals(False)

    def set_duration(self, duration_ms: int) -> None:
        """
        Set the track duration.

        Args:
            duration_ms: Duration in milliseconds
        """
        self._progress_slider.setMaximum(duration_ms)
        self._update_time_display(0, duration_ms)

    def update_time_display(self, current_ms: int, total_ms: int) -> None:
        """
        Update the time display.

        Args:
            current_ms: Current position in milliseconds
            total_ms: Total duration in milliseconds
        """
        self._update_time_display(current_ms, total_ms)

    def set_skip_increment(self, seconds: int) -> None:
        """
        Set the skip increment display on buttons.

        Args:
            seconds: Number of seconds for skip increment
        """
        self._skip_back_button.setText(f"<<{seconds}s")
        self._skip_forward_button.setText(f"{seconds}s>>")

    def set_markers(self, marker_positions: list[int]) -> None:
        """
        Set marker positions to display on the progress bar.

        Args:
            marker_positions: List of marker timestamps in milliseconds
        """
        self._progress_slider.set_markers(marker_positions)

    def clear_markers(self) -> None:
        """Clear all markers from the progress bar."""
        self._progress_slider.clear_markers()

    def _update_time_display(self, current_ms: int, total_ms: int) -> None:
        """
        Update the time display label.

        Args:
            current_ms: Current position in milliseconds
            total_ms: Total duration in milliseconds
        """
        current_str = self._format_time(current_ms)
        total_str = self._format_time(total_ms)
        self._time_label.setText(f"{current_str} / {total_str}")

    @staticmethod
    def _format_time(milliseconds: int) -> str:
        """
        Format time in milliseconds to M:SS format.

        Args:
            milliseconds: Time in milliseconds

        Returns:
            Formatted time string
        """
        seconds = milliseconds // 1000
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}:{secs:02d}"

    def _on_play_clicked(self) -> None:
        """Handle play button click."""
        logger.debug("Play button clicked")
        self.play_clicked.emit()

    def _on_pause_clicked(self) -> None:
        """Handle pause button click."""
        logger.debug("Pause button clicked")
        self.pause_clicked.emit()

    def _on_skip_forward_clicked(self) -> None:
        """Handle skip forward button click."""
        logger.debug("Skip forward button clicked")
        self.skip_forward_clicked.emit()

    def _on_skip_backward_clicked(self) -> None:
        """Handle skip backward button click."""
        logger.debug("Skip backward button clicked")
        self.skip_backward_clicked.emit()

    def _on_slider_moved(self, value: int) -> None:
        """
        Handle slider movement.

        Args:
            value: New slider value (0-duration_ms)
        """
        logger.debug(f"Slider moved to: {value}ms")
        self.position_changed.emit(value)

    def _on_slider_pressed(self) -> None:
        """Handle slider press (start of scrubbing)."""
        logger.debug("Slider pressed (scrubbing started)")
