"""Application controller coordinating UI, data models, and audio playback."""

from pathlib import Path

from PySide6.QtWidgets import QFileDialog

from .audio import AudioFileManager, AudioPlayer
from .models import Marker, Show
from .persistence import FileManager, ShowRepository
from .ui import MainWindow
from .ui.dialogs import (
    AddMarkerDialog,
    EditMarkerDialog,
    NewShowDialog,
    confirm,
    show_error,
    show_info,
    show_warning,
)
from .utils.logging_config import get_logger

logger = get_logger(__name__)


class AppController:
    """
    Main application controller.

    Coordinates between UI components, data models, and audio playback engine.
    Manages application state and user interactions.
    """

    def __init__(self, main_window: MainWindow) -> None:
        """
        Initialize the application controller.

        Args:
            main_window: The main application window
        """
        self._main_window = main_window
        self._current_show: Show | None = None
        self._current_track_index: int = -1
        self._show_file_path: Path | None = None  # Path to current show JSON file
        self._is_modified = False  # Track unsaved changes

        # Initialize managers
        self._file_manager = FileManager()
        self._audio_file_manager = AudioFileManager(self._file_manager)
        self._show_repository = ShowRepository(self._file_manager)
        self._audio_player = AudioPlayer()

        # Connect signals
        self._connect_menu_actions()
        self._connect_ui_signals()
        self._connect_audio_player_signals()

        logger.info("AppController initialized")

    def _connect_menu_actions(self) -> None:
        """Connect menu actions to handlers."""
        # File menu
        self._main_window.new_show_action.triggered.connect(self._on_new_show)
        self._main_window.open_show_action.triggered.connect(self._on_open_show)
        self._main_window.save_show_action.triggered.connect(self._on_save_show)
        self._main_window.save_show_as_action.triggered.connect(self._on_save_show_as)
        # Import/export will be implemented in Phase 6
        self._main_window.import_show_action.setEnabled(False)
        self._main_window.export_show_action.setEnabled(False)

        # Edit menu
        self._main_window.settings_action.triggered.connect(self._on_settings)

        # Help menu
        self._main_window.about_action.triggered.connect(self._on_about)

    def _connect_ui_signals(self) -> None:
        """Connect UI component signals to handlers."""
        # Main window keyboard shortcuts
        self._main_window.space_pressed.connect(self._on_toggle_play_pause)
        self._main_window.m_key_pressed.connect(self._on_add_marker)

        # Track sidebar
        self._main_window.track_sidebar.add_track_clicked.connect(self._on_add_track)
        self._main_window.track_sidebar.track_selected.connect(self._on_track_selected)

        # Playback controls
        self._main_window.playback_controls.play_clicked.connect(self._on_play)
        self._main_window.playback_controls.pause_clicked.connect(self._on_pause)
        self._main_window.playback_controls.skip_forward_clicked.connect(
            self._on_skip_forward
        )
        self._main_window.playback_controls.skip_backward_clicked.connect(
            self._on_skip_backward
        )
        self._main_window.playback_controls.position_changed.connect(
            self._on_position_changed
        )

        # Marker list
        self._main_window.marker_list.add_marker_clicked.connect(self._on_add_marker)
        self._main_window.marker_list.marker_selected.connect(self._on_marker_selected)
        self._main_window.marker_list.marker_double_clicked.connect(
            self._on_marker_double_clicked
        )
        self._main_window.marker_list.edit_marker_clicked.connect(self._on_edit_marker)
        self._main_window.marker_list.delete_marker_clicked.connect(
            self._on_delete_marker
        )

    def _connect_audio_player_signals(self) -> None:
        """Connect audio player signals to handlers."""
        self._audio_player.position_changed.connect(self._on_audio_position_changed)
        self._audio_player.duration_changed.connect(self._on_audio_duration_changed)
        self._audio_player.error_occurred.connect(self._on_audio_error)

    # Show Management (4.1)

    def _on_new_show(self) -> None:
        """Handle New Show menu action."""
        logger.info("New show requested")

        # Check for unsaved changes
        if not self._check_unsaved_changes():
            return

        # Show dialog
        dialog = NewShowDialog(self._main_window)
        if dialog.exec():
            show_name = dialog.get_show_name()
            logger.info(f"Creating new show: {show_name}")

            # Create new show
            self._current_show = Show(name=show_name)
            self._current_track_index = -1
            self._show_file_path = None
            self._is_modified = True

            # Update UI
            self._update_ui_for_show()
            self._update_window_title()

            show_info(
                self._main_window,
                "Show Created",
                f'New show "{show_name}" created successfully.',
            )

    def _on_open_show(self) -> None:
        """Handle Open Show menu action."""
        logger.info("Open show requested")

        # Check for unsaved changes
        if not self._check_unsaved_changes():
            return

        # Show file dialog
        shows_dir = self._file_manager.get_shows_directory()
        shows_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Open Show",
            str(shows_dir),
            "Show Files (*.json);;All Files (*)",
        )

        if file_path:
            self._load_show(Path(file_path))

    def _on_save_show(self) -> None:
        """Handle Save Show menu action."""
        if self._current_show is None:
            logger.warning("No show to save")
            return

        if self._show_file_path is None:
            # No file path yet, use Save As
            self._on_save_show_as()
        else:
            # Save to existing path
            self._save_show(self._show_file_path)

    def _on_save_show_as(self) -> None:
        """Handle Save Show As menu action."""
        if self._current_show is None:
            logger.warning("No show to save")
            return

        # Show file dialog
        shows_dir = self._file_manager.get_shows_directory()
        shows_dir.mkdir(parents=True, exist_ok=True)

        # Suggest filename based on show name
        suggested_name = self._current_show.name.replace(" ", "_") + ".json"
        suggested_path = shows_dir / suggested_name

        file_path, _ = QFileDialog.getSaveFileName(
            self._main_window,
            "Save Show As",
            str(suggested_path),
            "Show Files (*.json);;All Files (*)",
        )

        if file_path:
            self._save_show(Path(file_path))

    def _load_show(self, file_path: Path) -> None:
        """
        Load a show from a file.

        Args:
            file_path: Path to the show JSON file
        """
        try:
            logger.info(f"Loading show from: {file_path}")
            # Import show from the file path
            show = self._show_repository.import_show(file_path)

            self._current_show = show
            self._show_file_path = file_path
            self._current_track_index = -1
            self._is_modified = False

            # Update UI
            self._update_ui_for_show()
            self._update_window_title()

            logger.info(f"Show loaded successfully: {show.name}")
            show_info(
                self._main_window,
                "Show Loaded",
                f'Show "{show.name}" loaded successfully.',
            )

        except Exception as e:
            logger.error(f"Failed to load show: {e}")
            show_error(
                self._main_window,
                "Load Failed",
                f"Failed to load show: {e}",
            )

    def _save_show(self, file_path: Path) -> None:
        """
        Save the current show to a file.

        Args:
            file_path: Path to save the show JSON file
        """
        if self._current_show is None:
            return

        try:
            logger.info(f"Saving show to: {file_path}")
            # Export show to the file path
            self._show_repository.export_show(self._current_show, file_path)

            self._show_file_path = file_path
            self._is_modified = False

            # Update window title
            self._update_window_title()

            logger.info("Show saved successfully")
            show_info(
                self._main_window,
                "Show Saved",
                f'Show "{self._current_show.name}" saved successfully.',
            )

        except Exception as e:
            logger.error(f"Failed to save show: {e}")
            show_error(
                self._main_window,
                "Save Failed",
                f"Failed to save show: {e}",
            )

    def _check_unsaved_changes(self) -> bool:
        """
        Check for unsaved changes and prompt user if needed.

        Returns:
            True if it's safe to proceed (no changes or user confirmed), False otherwise
        """
        if not self._is_modified or self._current_show is None:
            return True

        result = confirm(
            self._main_window,
            "Unsaved Changes",
            f'Show "{self._current_show.name}" has unsaved changes. Discard changes?',
        )

        return result

    def _update_ui_for_show(self) -> None:
        """Update UI to reflect current show state."""
        if self._current_show is None:
            # Clear UI
            self._main_window.track_sidebar.clear_tracks()
            self._main_window.marker_list.clear_markers()
            self._main_window.playback_controls.set_track_title("No track selected")
            return

        # Update track sidebar
        track_names = [track.filename for track in self._current_show.tracks]
        self._main_window.track_sidebar.set_tracks(track_names)

        # Update skip increment buttons
        skip_seconds = self._current_show.settings.skip_increment_seconds
        self._main_window.playback_controls.set_skip_increment(skip_seconds)

        # If tracks exist, select first one
        if self._current_show.tracks:
            self._main_window.track_sidebar.set_selected_track(0)

    def _update_window_title(self) -> None:
        """Update the main window title to reflect current show."""
        base_title = "Rehearsal Track Marker"

        if self._current_show is None:
            self._main_window.setWindowTitle(base_title)
        else:
            show_name = self._current_show.name
            modified_marker = "*" if self._is_modified else ""
            self._main_window.setWindowTitle(
                f"{base_title} - {show_name}{modified_marker}"
            )

    # Track Management (4.2)

    def _on_add_track(self) -> None:
        """Handle Add Track button click."""
        if self._current_show is None:
            show_warning(
                self._main_window,
                "No Show",
                "Please create or open a show first.",
            )
            return

        logger.info("Add track requested")

        # Show file dialog
        file_paths, _ = QFileDialog.getOpenFileNames(
            self._main_window,
            "Add Audio Files",
            str(Path.home()),
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg);;All Files (*)",
        )

        for file_path_str in file_paths:
            self._add_audio_file(Path(file_path_str))

    def _add_audio_file(self, file_path: Path) -> None:
        """
        Add an audio file to the current show.

        Args:
            file_path: Path to the audio file
        """
        if self._current_show is None:
            return

        try:
            logger.info(f"Adding audio file: {file_path}")

            # Check if file is supported
            if not self._audio_file_manager.is_supported_format(file_path):
                show_error(
                    self._main_window,
                    "Unsupported Format",
                    f"Audio format not supported: {file_path.suffix}",
                )
                return

            # Add file to show
            track = self._audio_file_manager.add_audio_file_to_show(
                file_path, self._current_show.name
            )

            # Add track to show model
            self._current_show.add_track(track)

            # Update UI
            self._main_window.track_sidebar.add_track(track.filename)

            # Mark as modified
            self._is_modified = True
            self._update_window_title()

            logger.info(f"Track added successfully: {track.filename}")

        except Exception as e:
            logger.error(f"Failed to add track: {e}")
            show_error(
                self._main_window,
                "Add Track Failed",
                f"Failed to add track: {e}",
            )

    def _on_track_selected(self, index: int) -> None:
        """
        Handle track selection change.

        Args:
            index: Index of selected track
        """
        if self._current_show is None or index < 0:
            return

        logger.info(f"Track selected: index {index}")

        self._current_track_index = index
        track = self._current_show.get_track(index)

        if track is None:
            return

        # Load audio file
        if track.audio_path.exists():
            self._audio_player.load_file(track.audio_path)

            # Update UI
            self._main_window.playback_controls.set_track_title(track.filename)

            # Update marker list
            markers = [(m.name, m.timestamp_ms) for m in track.markers]
            self._main_window.marker_list.set_markers(markers)

            # Update marker visualization on progress bar
            marker_positions = [m.timestamp_ms for m in track.markers]
            self._main_window.playback_controls.set_markers(marker_positions)

        else:
            logger.error(f"Audio file not found: {track.audio_path}")
            show_error(
                self._main_window,
                "File Not Found",
                f"Audio file not found: {track.audio_path}",
            )

    # Playback Controls (4.3)

    def _on_toggle_play_pause(self) -> None:
        """Handle toggle play/pause (spacebar shortcut)."""
        self._audio_player.toggle_play_pause()

    def _on_play(self) -> None:
        """Handle play button click."""
        self._audio_player.play()

    def _on_pause(self) -> None:
        """Handle pause button click."""
        self._audio_player.pause()

    def _on_skip_forward(self) -> None:
        """Handle skip forward button click."""
        if self._current_show is None:
            return

        skip_ms = self._current_show.settings.skip_increment_seconds * 1000
        self._audio_player.skip_forward(skip_ms)

    def _on_skip_backward(self) -> None:
        """Handle skip backward button click."""
        if self._current_show is None:
            return

        skip_ms = self._current_show.settings.skip_increment_seconds * 1000
        self._audio_player.skip_backward(skip_ms)

    def _on_position_changed(self, position_ms: int) -> None:
        """
        Handle position change from scrubbing.

        Args:
            position_ms: New position in milliseconds
        """
        self._audio_player.seek(position_ms)

    def _on_audio_position_changed(self, position_ms: int) -> None:
        """
        Handle position change from audio player.

        Args:
            position_ms: Current position in milliseconds
        """
        duration_ms = self._audio_player.get_duration_ms()
        self._main_window.playback_controls.set_position(position_ms)
        self._main_window.playback_controls.update_time_display(
            position_ms, duration_ms
        )

    def _on_audio_duration_changed(self, duration_ms: int) -> None:
        """
        Handle duration change from audio player.

        Args:
            duration_ms: Track duration in milliseconds
        """
        self._main_window.playback_controls.set_duration(duration_ms)

    def _on_audio_error(self, error_msg: str) -> None:
        """
        Handle audio playback error.

        Args:
            error_msg: Error message
        """
        show_error(
            self._main_window,
            "Playback Error",
            f"Audio playback error: {error_msg}",
        )

    # Marker Management (4.4, 4.6, 4.7)

    def _on_add_marker(self) -> None:
        """Handle add marker button click."""
        if self._current_show is None or self._current_track_index < 0:
            show_warning(
                self._main_window,
                "No Track Selected",
                "Please select a track first.",
            )
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        # Get current position
        position_ms = self._audio_player.get_position_ms()

        # Get existing marker names for validation
        existing_names = [m.name for m in track.markers]

        # Show dialog with inline validation
        dialog = AddMarkerDialog(position_ms, existing_names, self._main_window)
        if dialog.exec():
            marker_name = dialog.get_marker_name()
            timestamp_ms = dialog.get_timestamp_ms()
            self._add_marker_to_track(marker_name, timestamp_ms)

    def _add_marker_to_track(self, name: str, timestamp_ms: int) -> None:
        """
        Add a marker to the current track.

        Args:
            name: Marker name (already validated as unique by dialog)
            timestamp_ms: Timestamp in milliseconds
        """
        if self._current_show is None or self._current_track_index < 0:
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        try:
            # Create and add marker (validation already done by dialog)
            marker = Marker(name=name, timestamp_ms=timestamp_ms)
            track.add_marker(marker)

            # Update UI
            self._main_window.marker_list.add_marker(name, timestamp_ms)

            # Update marker visualization on progress bar
            marker_positions = [m.timestamp_ms for m in track.markers]
            self._main_window.playback_controls.set_markers(marker_positions)

            # Mark as modified
            self._is_modified = True
            self._update_window_title()

            logger.info(f"Marker added: {name} @ {timestamp_ms}ms")

        except Exception as e:
            logger.error(f"Failed to add marker: {e}")
            show_error(
                self._main_window,
                "Add Marker Failed",
                f"Failed to add marker: {e}",
            )

    def _on_marker_selected(self, index: int) -> None:
        """
        Handle marker selection change.

        Args:
            index: Index of selected marker
        """
        logger.debug(f"Marker selected: index {index}")

    def _on_marker_double_clicked(self, index: int) -> None:
        """
        Handle marker double-click (jump to marker).

        Args:
            index: Index of marker
        """
        if self._current_show is None or self._current_track_index < 0:
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        if 0 <= index < len(track.markers):
            marker = track.markers[index]
            logger.info(f"Jumping to marker: {marker.name} @ {marker.timestamp_ms}ms")
            self._audio_player.seek(marker.timestamp_ms)

    def _on_edit_marker(self, index: int) -> None:
        """
        Handle edit marker button click.

        Args:
            index: Index of marker to edit
        """
        if self._current_show is None or self._current_track_index < 0:
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        if 0 <= index < len(track.markers):
            marker = track.markers[index]

            # Show edit dialog
            dialog = EditMarkerDialog(marker.name, self._main_window)
            if dialog.exec():
                new_name = dialog.get_marker_name()

                # Check for duplicate name (excluding current marker)
                for i, m in enumerate(track.markers):
                    if i != index and m.name == new_name:
                        show_error(
                            self._main_window,
                            "Duplicate Marker",
                            f'Marker "{new_name}" already exists in this track.',
                        )
                        return

                # Update marker
                marker.name = new_name

                # Update UI
                self._main_window.marker_list.update_marker(
                    index, new_name, marker.timestamp_ms
                )

                # Update marker visualization (positions haven't changed, but refresh)
                marker_positions = [m.timestamp_ms for m in track.markers]
                self._main_window.playback_controls.set_markers(marker_positions)

                # Mark as modified
                self._is_modified = True
                self._update_window_title()

                logger.info(f"Marker renamed to: {new_name}")

    def _on_delete_marker(self, index: int) -> None:
        """
        Handle delete marker button click.

        Args:
            index: Index of marker to delete
        """
        if self._current_show is None or self._current_track_index < 0:
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        if 0 <= index < len(track.markers):
            marker = track.markers[index]

            # Confirm deletion
            if confirm(
                self._main_window,
                "Delete Marker",
                f'Are you sure you want to delete marker "{marker.name}"?',
            ):
                # Remove marker by name
                track.remove_marker(marker.name)

                # Update UI
                self._main_window.marker_list.remove_marker(index)

                # Update marker visualization on progress bar
                marker_positions = [m.timestamp_ms for m in track.markers]
                self._main_window.playback_controls.set_markers(marker_positions)

                # Mark as modified
                self._is_modified = True
                self._update_window_title()

                logger.info(f"Marker deleted: {marker.name}")

    # Settings and About

    def _on_settings(self) -> None:
        """Handle settings menu action."""
        # Settings dialog will be implemented in Phase 5
        show_info(
            self._main_window,
            "Settings",
            "Settings dialog will be implemented in Phase 5.",
        )

    def _on_about(self) -> None:
        """Handle about menu action."""
        import rehearsal_track_markers

        show_info(
            self._main_window,
            "About Rehearsal Track Marker",
            f"Rehearsal Track Marker v{rehearsal_track_markers.__version__}\n\n"
            "A musical theatre rehearsal tool for adding timestamped markers "
            "to audio tracks and quickly jumping to specific locations.\n\n"
            "Built with PySide6 and Qt Multimedia.",
        )
