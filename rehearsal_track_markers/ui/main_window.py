"""Main window for the Rehearsal Track Marker application."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .marker_list import MarkerList
from .playback_controls import PlaybackControls
from .track_sidebar import TrackSidebar
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.

    Features:
    - Menu bar (File, Edit, Help)
    - Track sidebar (left)
    - Playback controls and marker list (right)
    - Splitter layout for resizable sections
    - Keyboard shortcuts (Space: play/pause, M: add marker)

    Signals:
        space_pressed: Emitted when spacebar is pressed (toggle play/pause)
        m_key_pressed: Emitted when M key is pressed (add marker)
    """

    # Signals for keyboard shortcuts
    space_pressed = Signal()
    m_key_pressed = Signal()

    def __init__(self) -> None:
        """Initialize the main window."""
        super().__init__()

        self._setup_window()
        self._setup_menu_bar()
        self._setup_ui()
        self._setup_shortcuts()

        logger.info("MainWindow initialized")

    def _setup_window(self) -> None:
        """Set up basic window properties."""
        self.setWindowTitle("Rehearsal Track Marker")
        self.setMinimumSize(800, 600)

        # Set default window size
        self.resize(1000, 700)

    def _setup_menu_bar(self) -> None:
        """Set up the menu bar."""
        menu_bar = self.menuBar()

        # File menu
        file_menu = menu_bar.addMenu("&File")

        self._new_show_action = QAction("&New Show...", self)
        self._open_show_action = QAction("&Open Show...", self)
        self._save_show_action = QAction("&Save Show", self)
        self._save_show_as_action = QAction("Save Show &As...", self)

        file_menu.addAction(self._new_show_action)
        file_menu.addAction(self._open_show_action)
        file_menu.addSeparator()
        file_menu.addAction(self._save_show_action)
        file_menu.addAction(self._save_show_as_action)
        file_menu.addSeparator()

        self._import_show_action = QAction("&Import Show...", self)
        self._export_show_action = QAction("&Export Show...", self)

        file_menu.addAction(self._import_show_action)
        file_menu.addAction(self._export_show_action)
        file_menu.addSeparator()

        self._quit_action = QAction("&Quit", self)
        self._quit_action.triggered.connect(self.close)
        file_menu.addAction(self._quit_action)

        # Edit menu
        edit_menu = menu_bar.addMenu("&Edit")

        self._settings_action = QAction("&Settings...", self)
        edit_menu.addAction(self._settings_action)

        # Help menu
        help_menu = menu_bar.addMenu("&Help")

        self._about_action = QAction("&About...", self)
        help_menu.addAction(self._about_action)

        logger.debug("Menu bar created")

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Create track sidebar
        self._track_sidebar = TrackSidebar()

        # Create main content area
        main_content = self._create_main_content_area()

        # Add widgets to splitter
        splitter.addWidget(self._track_sidebar)
        splitter.addWidget(main_content)

        # Set initial splitter sizes (sidebar: 250px, content: rest)
        splitter.setSizes([250, 750])

        # Add splitter to main layout
        main_layout.addWidget(splitter)

        logger.debug("UI layout created")

    def _setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Spacebar: toggle play/pause
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self._on_space_pressed)

        # M key: add marker
        m_shortcut = QShortcut(QKeySequence(Qt.Key.Key_M), self)
        m_shortcut.activated.connect(self._on_m_key_pressed)

        logger.debug("Keyboard shortcuts configured")

    def _on_space_pressed(self) -> None:
        """Handle spacebar press."""
        logger.debug("Spacebar pressed")
        self.space_pressed.emit()

    def _on_m_key_pressed(self) -> None:
        """Handle M key press."""
        logger.debug("M key pressed")
        self.m_key_pressed.emit()

    def _create_main_content_area(self) -> QWidget:
        """
        Create the main content area (playback controls + marker list).

        Returns:
            Widget containing the main content area
        """
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Create playback controls
        self._playback_controls = PlaybackControls()

        # Create marker list
        self._marker_list = MarkerList()

        # Add widgets to layout
        content_layout.addWidget(self._playback_controls, stretch=1)
        content_layout.addWidget(self._marker_list, stretch=2)

        return content_widget

    # Public accessors for UI components

    @property
    def track_sidebar(self) -> TrackSidebar:
        """Get the track sidebar widget."""
        return self._track_sidebar

    @property
    def playback_controls(self) -> PlaybackControls:
        """Get the playback controls widget."""
        return self._playback_controls

    @property
    def marker_list(self) -> MarkerList:
        """Get the marker list widget."""
        return self._marker_list

    # Menu action accessors

    @property
    def new_show_action(self) -> QAction:
        """Get the New Show menu action."""
        return self._new_show_action

    @property
    def open_show_action(self) -> QAction:
        """Get the Open Show menu action."""
        return self._open_show_action

    @property
    def save_show_action(self) -> QAction:
        """Get the Save Show menu action."""
        return self._save_show_action

    @property
    def save_show_as_action(self) -> QAction:
        """Get the Save Show As menu action."""
        return self._save_show_as_action

    @property
    def import_show_action(self) -> QAction:
        """Get the Import Show menu action."""
        return self._import_show_action

    @property
    def export_show_action(self) -> QAction:
        """Get the Export Show menu action."""
        return self._export_show_action

    @property
    def settings_action(self) -> QAction:
        """Get the Settings menu action."""
        return self._settings_action

    @property
    def about_action(self) -> QAction:
        """Get the About menu action."""
        return self._about_action
