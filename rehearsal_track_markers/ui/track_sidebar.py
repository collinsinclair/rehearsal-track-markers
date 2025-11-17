"""Track sidebar widget for displaying and selecting tracks."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class TrackSidebar(QWidget):
    """
    Sidebar widget displaying the list of tracks in a show.

    Features:
    - List of track names with selection
    - Visual highlight for selected track
    - "Add Track" button
    - Drag-to-reorder support (future)

    Signals:
        track_selected: Emitted when a track is selected (index: int)
        add_track_clicked: Emitted when "Add Track" button is clicked
    """

    # Signals
    track_selected = Signal(int)  # Track index
    add_track_clicked = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the track sidebar.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._connect_signals()

        logger.debug("TrackSidebar initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Create main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create track list widget
        self._track_list = QListWidget()
        self._track_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)

        # Create "Add Track" button
        self._add_track_button = QPushButton("+ Add Track")

        # Add widgets to layout
        layout.addWidget(self._track_list)
        layout.addWidget(self._add_track_button)

        # Set minimum width for sidebar
        self.setMinimumWidth(200)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._track_list.currentRowChanged.connect(self._on_selection_changed)
        self._add_track_button.clicked.connect(self._on_add_track_clicked)

    def add_track(self, track_name: str) -> None:
        """
        Add a track to the list.

        Args:
            track_name: Name of the track to add
        """
        item = QListWidgetItem(track_name)
        self._track_list.addItem(item)
        logger.debug(f"Added track to sidebar: {track_name}")

    def remove_track(self, index: int) -> bool:
        """
        Remove a track from the list.

        Args:
            index: Index of the track to remove

        Returns:
            True if track was removed, False if index invalid
        """
        if 0 <= index < self._track_list.count():
            item = self._track_list.takeItem(index)
            logger.debug(f"Removed track from sidebar: {item.text()}")
            return True
        return False

    def clear_tracks(self) -> None:
        """Clear all tracks from the list."""
        self._track_list.clear()
        logger.debug("Cleared all tracks from sidebar")

    def get_track_count(self) -> int:
        """
        Get the number of tracks in the list.

        Returns:
            Number of tracks
        """
        return self._track_list.count()

    def set_selected_track(self, index: int) -> None:
        """
        Set the selected track by index.

        Args:
            index: Index of the track to select
        """
        if 0 <= index < self._track_list.count():
            self._track_list.setCurrentRow(index)

    def get_selected_index(self) -> int:
        """
        Get the index of the currently selected track.

        Returns:
            Index of selected track, or -1 if none selected
        """
        return self._track_list.currentRow()

    def set_tracks(self, track_names: list[str]) -> None:
        """
        Set the entire track list.

        Args:
            track_names: List of track names to display
        """
        self.clear_tracks()
        for name in track_names:
            self.add_track(name)

        # Select first track if available
        if track_names:
            self.set_selected_track(0)

    def _on_selection_changed(self, current_row: int) -> None:
        """
        Handle track selection changes.

        Args:
            current_row: Index of newly selected row (-1 if none)
        """
        if current_row >= 0:
            logger.debug(f"Track selected: index {current_row}")
            self.track_selected.emit(current_row)

    def _on_add_track_clicked(self) -> None:
        """Handle Add Track button click."""
        logger.debug("Add Track button clicked")
        self.add_track_clicked.emit()
