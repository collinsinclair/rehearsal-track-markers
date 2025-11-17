"""Welcome screen widget for when no show is loaded."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class WelcomeScreen(QWidget):
    """
    Welcome screen displayed when no show is loaded.

    Provides clear call-to-action buttons for creating or opening a show,
    improving discoverability for non-technical users.

    Signals:
        new_show_requested: Emitted when user clicks "Create New Show"
        open_show_requested: Emitted when user clicks "Open Existing Show"
    """

    # Signals
    new_show_requested = Signal()
    open_show_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """
        Initialize the welcome screen.

        Args:
            parent: Optional parent widget
        """
        super().__init__(parent)

        self._setup_ui()
        self._connect_signals()

        logger.debug("WelcomeScreen initialized")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Main layout - centered
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("Welcome to Rehearsal Track Marker")
        title.setStyleSheet("font-size: 24pt; font-weight: bold; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        subtitle = QLabel(
            "Add timestamped markers to audio tracks\n"
            "and jump to specific locations instantly"
        )
        subtitle.setStyleSheet("font-size: 12pt; margin-bottom: 30px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        # "Create New Show" button - prominent
        self._new_show_button = QPushButton("Create New Show")
        self._new_show_button.setStyleSheet(
            "font-size: 14pt; padding: 15px 30px; font-weight: bold;"
        )
        self._new_show_button.setMinimumWidth(300)
        layout.addWidget(self._new_show_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacing
        layout.addSpacing(15)

        # "Open Existing Show" button
        self._open_show_button = QPushButton("Open Existing Show")
        self._open_show_button.setStyleSheet("font-size: 14pt; padding: 15px 30px;")
        self._open_show_button.setMinimumWidth(300)
        layout.addWidget(self._open_show_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacing
        layout.addSpacing(40)

        # Quick tips
        tips_label = QLabel(
            "<b>Quick Tips:</b><br>"
            "• Press <b>Space</b> to play/pause<br>"
            "• Press <b>M</b> to add a marker at current position<br>"
            "• <b>Double-click</b> a marker to jump to it<br>"
            "• Use <b>← →</b> arrow keys to nudge selected marker"
        )
        tips_label.setStyleSheet(
            "font-size: 11pt; padding: 15px; "
            "border: 1px solid palette(mid); border-radius: 5px;"
        )
        tips_label.setMaximumWidth(400)
        layout.addWidget(tips_label, alignment=Qt.AlignmentFlag.AlignCenter)

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        self._new_show_button.clicked.connect(self._on_new_show_clicked)
        self._open_show_button.clicked.connect(self._on_open_show_clicked)

    def _on_new_show_clicked(self) -> None:
        """Handle Create New Show button click."""
        logger.debug("Create New Show button clicked on welcome screen")
        self.new_show_requested.emit()

    def _on_open_show_clicked(self) -> None:
        """Handle Open Existing Show button click."""
        logger.debug("Open Existing Show button clicked on welcome screen")
        self.open_show_requested.emit()
