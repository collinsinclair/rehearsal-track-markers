"""Dialog widgets for user interactions."""

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QInputDialog,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class NewShowDialog(QDialog):
    """
    Dialog for creating a new show.

    Prompts user for show name and validates input.
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the new show dialog.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("New Show")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Show name input
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Into the Woods - Spring 2025")
        form_layout.addRow("Show Name:", self._name_input)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Set focus to name input
        self._name_input.setFocus()

    def get_show_name(self) -> str:
        """
        Get the entered show name.

        Returns:
            The show name entered by the user
        """
        return self._name_input.text().strip()

    def accept(self) -> None:
        """Accept the dialog if validation passes."""
        if not self.get_show_name():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a show name.",
            )
            return

        super().accept()


class AddMarkerDialog(QDialog):
    """
    Dialog for adding a new marker with inline validation.

    Shows validation errors inline and keeps the dialog open until
    a valid, unique name is entered or the user cancels.
    """

    def __init__(
        self, timestamp_ms: int, existing_names: list[str], parent=None
    ) -> None:
        """
        Initialize the add marker dialog.

        Args:
            timestamp_ms: Timestamp for the marker in milliseconds
            existing_names: List of existing marker names (for duplicate checking)
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Add Marker")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._timestamp_ms = timestamp_ms
        self._existing_names = [name.lower() for name in existing_names]

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Timestamp display (read-only)
        time_str = self._format_timestamp(self._timestamp_ms)
        timestamp_label = QLineEdit(time_str)
        timestamp_label.setReadOnly(True)
        timestamp_label.setStyleSheet("color: gray;")
        form_layout.addRow("Position:", timestamp_label)

        # Marker name input
        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText("e.g., Measure 42, Reh A, Dorothy enters")
        self._name_input.textChanged.connect(self._on_text_changed)
        form_layout.addRow("Marker Name:", self._name_input)

        layout.addLayout(form_layout)

        # Error message label (initially hidden)
        self._error_label = QLineEdit()
        self._error_label.setReadOnly(True)
        self._error_label.setStyleSheet(
            "color: red; background: transparent; border: none;"
        )
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Set focus to name input
        self._name_input.setFocus()

    def _format_timestamp(self, milliseconds: int) -> str:
        """
        Format timestamp in M:SS.mmm format.

        Args:
            milliseconds: Time in milliseconds

        Returns:
            Formatted time string
        """
        total_seconds = milliseconds / 1000
        minutes = int(total_seconds // 60)
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:06.3f}"

    def _on_text_changed(self) -> None:
        """Handle text changes to clear error message."""
        self._error_label.setVisible(False)

    def get_marker_name(self) -> str:
        """
        Get the entered marker name.

        Returns:
            The marker name entered by the user
        """
        return self._name_input.text().strip()

    def get_timestamp_ms(self) -> int:
        """
        Get the marker timestamp.

        Returns:
            The timestamp in milliseconds
        """
        return self._timestamp_ms

    def _show_error(self, message: str) -> None:
        """
        Show an error message inline.

        Args:
            message: Error message to display
        """
        self._error_label.setText(message)
        self._error_label.setVisible(True)

    def accept(self) -> None:
        """Accept the dialog if validation passes."""
        name = self.get_marker_name()

        # Validate non-empty
        if not name:
            self._show_error("Please enter a marker name.")
            self._name_input.setFocus()
            return

        # Validate uniqueness (case-insensitive)
        if name.lower() in self._existing_names:
            self._show_error(
                f'Marker "{name}" already exists. Please choose a different name.'
            )
            self._name_input.selectAll()
            self._name_input.setFocus()
            return

        # Validation passed
        super().accept()


class EditMarkerDialog(QDialog):
    """
    Dialog for editing a marker name.

    Prompts user for new marker name and validates input.
    """

    def __init__(self, current_name: str, parent=None) -> None:
        """
        Initialize the edit marker dialog.

        Args:
            current_name: Current name of the marker
            parent: Optional parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Edit Marker")
        self.setModal(True)
        self.setMinimumWidth(400)

        self._current_name = current_name
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Form layout
        form_layout = QFormLayout()

        # Marker name input
        self._name_input = QLineEdit()
        self._name_input.setText(self._current_name)
        self._name_input.selectAll()
        self._name_input.setPlaceholderText("e.g., Measure 42, Reh A, Dorothy enters")
        form_layout.addRow("Marker Name:", self._name_input)

        layout.addLayout(form_layout)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Set focus to name input
        self._name_input.setFocus()

    def get_marker_name(self) -> str:
        """
        Get the entered marker name.

        Returns:
            The marker name entered by the user
        """
        return self._name_input.text().strip()

    def accept(self) -> None:
        """Accept the dialog if validation passes."""
        if not self.get_marker_name():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please enter a marker name.",
            )
            return

        super().accept()


def show_error(parent, title: str, message: str) -> None:
    """
    Show an error message dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Error message
    """
    QMessageBox.critical(parent, title, message)
    logger.error(f"{title}: {message}")


def show_warning(parent, title: str, message: str) -> None:
    """
    Show a warning message dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Warning message
    """
    QMessageBox.warning(parent, title, message)
    logger.warning(f"{title}: {message}")


def show_info(parent, title: str, message: str) -> None:
    """
    Show an informational message dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Information message
    """
    QMessageBox.information(parent, title, message)
    logger.info(f"{title}: {message}")


def confirm(parent, title: str, message: str) -> bool:
    """
    Show a confirmation dialog.

    Args:
        parent: Parent widget
        title: Dialog title
        message: Confirmation message

    Returns:
        True if user confirmed, False otherwise
    """
    result = QMessageBox.question(
        parent,
        title,
        message,
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return result == QMessageBox.StandardButton.Yes


def get_text_input(
    parent, title: str, label: str, default_text: str = ""
) -> str | None:
    """
    Show an input dialog for text entry.

    Args:
        parent: Parent widget
        title: Dialog title
        label: Input label
        default_text: Default text value

    Returns:
        The entered text, or None if cancelled
    """
    text, ok = QInputDialog.getText(parent, title, label, text=default_text)
    if ok and text.strip():
        return text.strip()
    return None
