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
