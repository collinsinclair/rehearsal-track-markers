"""Marker list widget for displaying and managing markers."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MarkerList(QWidget):
    """
    Widget for displaying and managing markers for the current track.

    Features:
    - "Add Marker" button with hotkey hint
    - List of markers with selection
    - Edit and Delete buttons
    - Visual highlight for selected marker

    Signals:
        add_marker_clicked: Emitted when "Add Marker" button is clicked
        marker_selected: Emitted when a marker is selected (index: int)
        edit_marker_clicked: Emitted when edit button is clicked (index: int)
        delete_marker_clicked: Emitted when delete button is clicked (index: int)
        marker_double_clicked: Emitted when marker is double-clicked (index: int)
    """

    # Signals
    add_marker_clicked = Signal()
    marker_selected = Signal(int)  # Marker index
    edit_marker_clicked = Signal(int)  # Marker index
    delete_marker_clicked = Signal(int)  # Marker index
    marker_double_clicked = Signal(int)  # Marker index (for jumping to marker)

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the marker list.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._connect_signals()

        logger.debug("MarkerList initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout
        layout = QVBoxLayout(self)

        # Section header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QPushButton("MARKERS")
        title_label.setEnabled(False)
        title_label.setStyleSheet("font-weight: bold; text-align: left;")

        header_layout.addWidget(title_label)
        header_layout.addStretch()

        layout.addWidget(header)

        # Add Marker button
        self._add_marker_button = QPushButton("+ Add Marker (M)")
        layout.addWidget(self._add_marker_button)

        # Marker list
        self._marker_list = QListWidget()
        self._marker_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self._marker_list)

        # Edit/Delete buttons
        button_layout = QHBoxLayout()

        self._edit_button = QPushButton("Edit")
        self._delete_button = QPushButton("Delete")

        button_layout.addWidget(self._edit_button)
        button_layout.addWidget(self._delete_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        # Initially disable edit/delete buttons (no marker selected)
        self._edit_button.setEnabled(False)
        self._delete_button.setEnabled(False)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._add_marker_button.clicked.connect(self._on_add_marker_clicked)
        self._marker_list.currentRowChanged.connect(self._on_selection_changed)
        self._marker_list.itemDoubleClicked.connect(self._on_marker_double_clicked)
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._delete_button.clicked.connect(self._on_delete_clicked)

    def add_marker(self, marker_name: str, timestamp_ms: int) -> None:
        """
        Add a marker to the list.

        Args:
            marker_name: Name of the marker
            timestamp_ms: Timestamp in milliseconds
        """
        # Format: "Marker Name"
        # Store timestamp as data for later use
        item = QListWidgetItem(marker_name)
        item.setData(Qt.ItemDataRole.UserRole, timestamp_ms)
        self._marker_list.addItem(item)
        logger.debug(f"Added marker to list: {marker_name} ({timestamp_ms}ms)")

    def remove_marker(self, index: int) -> bool:
        """
        Remove a marker from the list.

        Args:
            index: Index of the marker to remove

        Returns:
            True if marker was removed, False if index invalid
        """
        if 0 <= index < self._marker_list.count():
            item = self._marker_list.takeItem(index)
            logger.debug(f"Removed marker from list: {item.text()}")
            return True
        return False

    def clear_markers(self) -> None:
        """Clear all markers from the list."""
        self._marker_list.clear()
        logger.debug("Cleared all markers from list")

    def get_marker_count(self) -> int:
        """
        Get the number of markers in the list.

        Returns:
            Number of markers
        """
        return self._marker_list.count()

    def set_selected_marker(self, index: int) -> None:
        """
        Set the selected marker by index.

        Args:
            index: Index of the marker to select
        """
        if 0 <= index < self._marker_list.count():
            self._marker_list.setCurrentRow(index)

    def get_selected_index(self) -> int:
        """
        Get the index of the currently selected marker.

        Returns:
            Index of selected marker, or -1 if none selected
        """
        return self._marker_list.currentRow()

    def update_marker(self, index: int, marker_name: str, timestamp_ms: int) -> bool:
        """
        Update a marker's display.

        Args:
            index: Index of the marker to update
            marker_name: New marker name
            timestamp_ms: New timestamp in milliseconds

        Returns:
            True if marker was updated, False if index invalid
        """
        if 0 <= index < self._marker_list.count():
            item = self._marker_list.item(index)
            if item:
                item.setText(marker_name)
                item.setData(Qt.ItemDataRole.UserRole, timestamp_ms)
                logger.debug(f"Updated marker: {marker_name} ({timestamp_ms}ms)")
                return True
        return False

    def set_markers(
        self, markers: list[tuple[str, int]]
    ) -> None:  # List of (name, timestamp_ms)
        """
        Set the entire marker list.

        Args:
            markers: List of tuples (marker_name, timestamp_ms)
        """
        self.clear_markers()
        for name, timestamp_ms in markers:
            self.add_marker(name, timestamp_ms)

    def _on_add_marker_clicked(self) -> None:
        """Handle Add Marker button click."""
        logger.debug("Add Marker button clicked")
        self.add_marker_clicked.emit()

    def _on_selection_changed(self, current_row: int) -> None:
        """
        Handle marker selection changes.

        Args:
            current_row: Index of newly selected row (-1 if none)
        """
        has_selection = current_row >= 0

        # Enable/disable edit and delete buttons
        self._edit_button.setEnabled(has_selection)
        self._delete_button.setEnabled(has_selection)

        if has_selection:
            logger.debug(f"Marker selected: index {current_row}")
            self.marker_selected.emit(current_row)

    def _on_marker_double_clicked(self, item: QListWidgetItem) -> None:
        """
        Handle marker double-click (jump to marker).

        Args:
            item: The clicked list item
        """
        index = self._marker_list.row(item)
        logger.debug(f"Marker double-clicked: index {index}")
        self.marker_double_clicked.emit(index)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        index = self.get_selected_index()
        if index >= 0:
            logger.debug(f"Edit marker clicked: index {index}")
            self.edit_marker_clicked.emit(index)

    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        index = self.get_selected_index()
        if index >= 0:
            logger.debug(f"Delete marker clicked: index {index}")
            self.delete_marker_clicked.emit(index)
