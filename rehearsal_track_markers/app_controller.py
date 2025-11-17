"""Application controller coordinating UI, data models, and audio playback."""

import json
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFileDialog

from .audio import AudioFileManager, AudioPlayer
from .models import Marker, Show
from .persistence import FileManager, ShowRepository
from .ui import MainWindow
from .ui.dialogs import (
    AddMarkerDialog,
    EditMarkerDialog,
    NewShowDialog,
    SettingsDialog,
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

        # Setup auto-save debounce timer
        # Instead of saving every 2 minutes, save 500ms after any change
        # This makes auto-save feel instant while preventing excessive saves
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._on_auto_save)
        self._auto_save_timer.setSingleShot(True)  # Only fire once per start
        self._auto_save_debounce_ms = 500  # 500ms after last change

        # Connect signals
        self._connect_menu_actions()
        self._connect_ui_signals()
        self._connect_audio_player_signals()

        # Show welcome screen initially (no show loaded yet)
        self._main_window.show_welcome_screen()

        logger.info("AppController initialized with auto-save after each change")

    def _connect_menu_actions(self) -> None:
        """Connect menu actions to handlers."""
        # File menu
        self._main_window.new_show_action.triggered.connect(self._on_new_show)
        self._main_window.open_show_action.triggered.connect(self._on_open_show)
        self._main_window.save_show_action.triggered.connect(self._on_save_show)
        self._main_window.save_show_as_action.triggered.connect(self._on_save_show_as)

        # Edit menu
        self._main_window.settings_action.triggered.connect(self._on_settings)

        # Help menu
        self._main_window.about_action.triggered.connect(self._on_about)

        # Enable import/export actions
        self._main_window.import_show_action.triggered.connect(self._on_import_show)
        self._main_window.export_show_action.triggered.connect(self._on_export_show)

    def _connect_ui_signals(self) -> None:
        """Connect UI component signals to handlers."""
        # Welcome screen
        self._main_window.welcome_screen.new_show_requested.connect(self._on_new_show)
        self._main_window.welcome_screen.open_show_requested.connect(self._on_open_show)

        # Main window keyboard shortcuts
        self._main_window.space_pressed.connect(self._on_toggle_play_pause)
        self._main_window.m_key_pressed.connect(self._on_add_marker)
        self._main_window.arrow_left_pressed.connect(self._on_nudge_marker_backward)
        self._main_window.arrow_right_pressed.connect(self._on_nudge_marker_forward)

        # Track sidebar
        self._main_window.track_sidebar.add_track_clicked.connect(self._on_add_track)
        self._main_window.track_sidebar.track_selected.connect(self._on_track_selected)
        self._main_window.track_sidebar.remove_track_clicked.connect(
            self._on_remove_track
        )

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
            self._is_modified = True

            # Create show directories
            self._file_manager.create_show_directories(show_name)

            # Set the file path to where it will be saved
            self._show_file_path = self._file_manager.get_show_file_path(show_name)

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

        # Always save to proper app storage location
        self._save_show()

    def _on_save_show_as(self) -> None:
        """Handle Save Show As menu action (rename show)."""
        if self._current_show is None:
            logger.warning("No show to save")
            return

        # For "Save As", we need to create a new show with a different name
        # This is essentially renaming the show
        from .ui.dialogs import get_text_input

        new_name = get_text_input(
            self._main_window,
            "Save Show As",
            "Enter new show name:",
            default_text=self._current_show.name,
        )

        if new_name and new_name != self._current_show.name:
            # Rename the show
            old_name = self._current_show.name
            self._current_show.name = new_name

            # Save with new name
            self._save_show()

            logger.info(f"Show renamed from '{old_name}' to '{new_name}'")

    def _on_export_show(self) -> None:
        """Handle Export Show menu action."""
        if self._current_show is None:
            logger.warning("No show to export")
            show_warning(
                self._main_window,
                "No Show",
                "Please create or open a show first.",
            )
            return

        logger.info("Export show requested")

        # Show file dialog for export location
        suggested_name = self._current_show.name.replace(" ", "_") + ".json"
        default_path = str(Path.home() / suggested_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self._main_window,
            "Export Show",
            default_path,
            "Show Files (*.json);;All Files (*)",
        )

        if file_path:
            self._export_show(Path(file_path))

    def _on_import_show(self) -> None:
        """Handle Import Show menu action."""
        logger.info("Import show requested")

        # Check for unsaved changes
        if not self._check_unsaved_changes():
            return

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self._main_window,
            "Import Show",
            str(Path.home()),
            "Show Files (*.json);;All Files (*)",
        )

        if file_path:
            self._import_show(Path(file_path))

    def _export_show(self, export_path: Path) -> None:
        """
        Export the current show to a file.

        Args:
            export_path: Path to export the show JSON file

        Note:
            Audio files are NOT included in the export. Users need to
            manually copy the audio files if sharing with others.
        """
        if self._current_show is None:
            return

        try:
            logger.info(f"Exporting show to: {export_path}")

            # Export show to the file path
            self._show_repository.export_show(self._current_show, export_path)

            logger.info("Show exported successfully")
            show_info(
                self._main_window,
                "Show Exported",
                f'Show "{self._current_show.name}" exported successfully to:\n'
                f"{export_path}\n\n"
                f"Note: Audio files are NOT included in the export. "
                f"To share this show with others, you'll also need to share the audio files.",
            )

        except Exception as e:
            logger.error(f"Failed to export show: {e}")
            show_error(
                self._main_window,
                "Export Failed",
                f"Failed to export show: {e}",
            )

    def _import_show(self, import_path: Path) -> None:
        """
        Import a show from a file.

        Args:
            import_path: Path to the show JSON file to import

        Note:
            Expects audio files to be in an "audio" subdirectory next to the JSON file.
            Audio files will be copied to app storage.
        """
        try:
            logger.info(f"Importing show from: {import_path}")

            # Check if audio directory exists
            audio_dir = import_path.parent / "audio"
            if not audio_dir.exists():
                # Ask user to locate audio directory
                audio_dir_str = QFileDialog.getExistingDirectory(
                    self._main_window,
                    "Locate Audio Files Directory",
                    str(import_path.parent),
                    QFileDialog.Option.ShowDirsOnly,
                )

                if not audio_dir_str:
                    show_warning(
                        self._main_window,
                        "Import Cancelled",
                        "Audio files directory not selected. Import cancelled.",
                    )
                    return

                audio_dir = Path(audio_dir_str)

            # Import show from the file path
            show = self._show_repository.import_show(import_path, audio_dir)

            # Copy audio files to app storage
            for track in show.tracks:
                source_audio_path = audio_dir / track.filename

                if not source_audio_path.exists():
                    show_warning(
                        self._main_window,
                        "Audio File Missing",
                        f"Audio file not found: {track.filename}\n\n"
                        f"This track will be imported but audio playback won't work.",
                    )
                    continue

                # Copy audio file to app storage
                try:
                    dest_track = self._audio_file_manager.add_audio_file_to_show(
                        source_audio_path, show.name
                    )
                    # Update track's audio path to the copied location
                    track.audio_path = dest_track.audio_path
                    logger.info(f"Copied audio file: {track.filename}")
                except Exception as e:
                    logger.error(f"Failed to copy audio file {track.filename}: {e}")
                    show_warning(
                        self._main_window,
                        "Audio Copy Failed",
                        f"Failed to copy audio file: {track.filename}\n\n{e}",
                    )

            # Save the imported show
            self._show_repository.save(show)

            # Load the imported show
            self._current_show = show
            self._show_file_path = self._file_manager.get_show_file_path(show.name)
            self._current_track_index = -1
            self._is_modified = False

            # Update UI
            self._update_ui_for_show()
            self._update_window_title()

            logger.info(f"Show imported successfully: {show.name}")
            show_info(
                self._main_window,
                "Show Imported",
                f'Show "{show.name}" imported successfully with {len(show.tracks)} track(s).',
            )

        except FileNotFoundError as e:
            logger.error(f"Import file not found: {e}")
            show_error(
                self._main_window,
                "Import Failed",
                f"Import file not found: {e}",
            )

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in import file: {e}")
            show_error(
                self._main_window,
                "Import Failed",
                f"Invalid JSON file: {e}\n\n"
                f"Please ensure the file is a valid show export.",
            )

        except Exception as e:
            logger.error(f"Failed to import show: {e}")
            show_error(
                self._main_window,
                "Import Failed",
                f"Failed to import show: {e}",
            )

    def _load_show(self, file_path: Path) -> None:
        """
        Load a show from app storage.

        Args:
            file_path: Path to the show JSON file in app storage

        Note:
            This is for loading shows from the app's storage directory.
            For importing external shows, use _import_show() instead.
        """
        try:
            logger.info(f"Loading show from: {file_path}")

            # Extract show name from file path (parent directory name)
            # File structure: ~/AppData/shows/[show-name]/[show-name].json
            show_name = file_path.parent.name

            # Load show from app storage using the proper method
            show = self._show_repository.load(show_name)

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

    def _save_show(self) -> None:
        """
        Save the current show to app storage.

        Uses the proper app directory structure via ShowRepository.save().
        """
        if self._current_show is None:
            return

        try:
            logger.info(f"Saving show: {self._current_show.name}")

            # Save using the proper repository method (handles paths internally)
            self._show_repository.save(self._current_show)

            # Update our tracked path to the correct location
            self._show_file_path = self._file_manager.get_show_file_path(
                self._current_show.name
            )
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
            # Show welcome screen when no show is loaded
            self._main_window.show_welcome_screen()

            # Clear UI
            self._main_window.track_sidebar.clear_tracks()
            self._main_window.marker_list.clear_markers()
            self._main_window.playback_controls.set_track_title("No track selected")
            return

        # Show main UI when a show is loaded
        self._main_window.show_main_ui()

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

            # Trigger auto-save
            self._trigger_auto_save()

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

    def _on_remove_track(self, index: int) -> None:
        """
        Handle remove track button click.

        Args:
            index: Index of track to remove
        """
        if self._current_show is None or index < 0:
            return

        track = self._current_show.get_track(index)
        if track is None:
            return

        logger.info(f"Remove track requested: {track.filename} at index {index}")

        # Confirm deletion
        if not confirm(
            self._main_window,
            "Remove Track",
            f'Are you sure you want to remove track "{track.filename}"?\n\n'
            f"This will delete the audio file and all markers for this track.",
        ):
            return

        try:
            # Stop playback if this track is currently selected
            if self._current_track_index == index:
                self._audio_player.stop()
                self._audio_player.unload()
                self._current_track_index = -1

            # Remove track from show model
            self._current_show.remove_track(index)

            # Remove from UI
            self._main_window.track_sidebar.remove_track(index)

            # Clear marker list if this was the selected track
            if self._current_track_index == -1:
                self._main_window.marker_list.clear_markers()
                self._main_window.playback_controls.set_track_title("No track selected")
                self._main_window.playback_controls.clear_markers()

            # Update current track index if needed
            if self._current_track_index > index:
                self._current_track_index -= 1

            # Delete audio file from storage
            # Note: We delete the file to save space, but this is irreversible
            if track.audio_path.exists():
                track.audio_path.unlink()
                logger.info(f"Deleted audio file: {track.audio_path}")

            # Trigger auto-save
            self._trigger_auto_save()

            logger.info(f"Track removed successfully: {track.filename}")

        except Exception as e:
            logger.error(f"Failed to remove track: {e}")
            show_error(
                self._main_window,
                "Remove Track Failed",
                f"Failed to remove track: {e}",
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

            # Trigger auto-save
            self._trigger_auto_save()

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

                # Trigger auto-save
                self._trigger_auto_save()

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

                # Trigger auto-save
                self._trigger_auto_save()

                logger.info(f"Marker deleted: {marker.name}")

    def _on_nudge_marker_backward(self) -> None:
        """Handle left arrow key press to nudge marker backward."""
        self._nudge_selected_marker(-1)

    def _on_nudge_marker_forward(self) -> None:
        """Handle right arrow key press to nudge marker forward."""
        self._nudge_selected_marker(1)

    def _nudge_selected_marker(self, direction: int) -> None:
        """
        Nudge the selected marker's timestamp by the configured increment.

        Args:
            direction: 1 for forward (right arrow), -1 for backward (left arrow)
        """
        if self._current_show is None or self._current_track_index < 0:
            return

        track = self._current_show.get_track(self._current_track_index)
        if track is None:
            return

        # Get selected marker index from UI
        selected_index = self._main_window.marker_list.get_selected_index()
        if selected_index < 0:
            logger.debug("No marker selected for nudging")
            return

        if selected_index >= len(track.markers):
            return

        marker = track.markers[selected_index]

        # Get nudge increment from settings
        nudge_increment_ms = self._current_show.settings.marker_nudge_increment_ms

        # Calculate new timestamp
        new_timestamp = marker.timestamp_ms + (direction * nudge_increment_ms)

        # Clamp to valid range (0 to track duration)
        new_timestamp = max(0, new_timestamp)
        duration_ms = self._audio_player.get_duration_ms()
        if duration_ms > 0:
            new_timestamp = min(new_timestamp, duration_ms)

        # Update marker timestamp
        marker.timestamp_ms = new_timestamp

        # Update UI
        self._main_window.marker_list.update_marker(
            selected_index, marker.name, marker.timestamp_ms
        )

        # Update marker visualization on progress bar
        marker_positions = [m.timestamp_ms for m in track.markers]
        self._main_window.playback_controls.set_markers(marker_positions)

        # Trigger auto-save
        self._trigger_auto_save()

        logger.debug(
            f"Marker '{marker.name}' nudged {direction * nudge_increment_ms}ms "
            f"to {marker.timestamp_ms}ms"
        )

    # Auto-Save

    def _trigger_auto_save(self) -> None:
        """
        Trigger a debounced auto-save.

        Called after any modification action. Uses a timer to debounce rapid changes,
        so multiple quick actions only result in one save operation.
        """
        if self._current_show is None:
            return

        # Mark as modified
        self._is_modified = True
        self._update_window_title()

        # Restart the debounce timer
        # If already running, this resets it (prevents saving during rapid edits)
        self._auto_save_timer.start(self._auto_save_debounce_ms)

    def _on_auto_save(self) -> None:
        """Handle auto-save timer timeout (debounced save)."""
        # Only auto-save if there's a current show
        if self._current_show is None:
            return

        try:
            logger.debug("Auto-saving show...")

            # Save the show using proper method
            self._show_repository.save(self._current_show)

            # Update state
            self._is_modified = False
            self._update_window_title()

            logger.debug("Auto-save successful")

            # Optional: Show brief status message in the UI
            # (Could add a status bar message here in the future)

        except Exception as e:
            logger.error(f"Auto-save failed: {e}")
            # Don't show error dialog during auto-save to avoid interrupting user
            # Just log the error

    # Settings and About

    def _on_settings(self) -> None:
        """Handle settings menu action."""
        if self._current_show is None:
            show_warning(
                self._main_window,
                "No Show",
                "Please create or open a show first.\n\n"
                "Settings are saved per-show, so you need to have a show open.",
            )
            return

        logger.info("Settings dialog requested")

        # Get current settings
        current_settings = self._current_show.settings

        # Show settings dialog
        dialog = SettingsDialog(
            skip_increment_seconds=current_settings.skip_increment_seconds,
            marker_nudge_increment_ms=current_settings.marker_nudge_increment_ms,
            parent=self._main_window,
        )

        if dialog.exec():
            # User clicked OK, apply changes
            old_skip = current_settings.skip_increment_seconds
            old_nudge = current_settings.marker_nudge_increment_ms

            new_skip = dialog.get_skip_increment_seconds()
            new_nudge = dialog.get_marker_nudge_increment_ms()

            # Update settings
            current_settings.skip_increment_seconds = new_skip
            current_settings.marker_nudge_increment_ms = new_nudge

            # Trigger auto-save if settings changed
            if old_skip != new_skip or old_nudge != new_nudge:
                # Update UI to reflect new skip increment
                self._main_window.playback_controls.set_skip_increment(new_skip)

                # Trigger auto-save
                self._trigger_auto_save()

                logger.info(f"Settings updated: skip={new_skip}s, nudge={new_nudge}ms")

                show_info(
                    self._main_window,
                    "Settings Updated",
                    "Settings have been updated successfully.",
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
