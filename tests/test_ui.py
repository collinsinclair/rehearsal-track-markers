"""Unit tests for UI components."""

from PySide6.QtTest import QSignalSpy
from PySide6.QtWidgets import QApplication

from rehearsal_track_markers.ui import (
    MainWindow,
    MarkerList,
    PlaybackControls,
    TrackSidebar,
)
from rehearsal_track_markers.ui.dialogs import SettingsDialog

# Ensure QApplication exists for Qt tests
app = QApplication.instance() or QApplication([])


class TestTrackSidebar:
    """Tests for the TrackSidebar widget."""

    def test_initialization(self) -> None:
        """Test creating a TrackSidebar instance."""
        sidebar = TrackSidebar()

        assert sidebar is not None
        assert sidebar.get_track_count() == 0
        assert sidebar.get_selected_index() == -1

    def test_add_track(self) -> None:
        """Test adding tracks to the sidebar."""
        sidebar = TrackSidebar()

        sidebar.add_track("Track 1")
        assert sidebar.get_track_count() == 1

        sidebar.add_track("Track 2")
        assert sidebar.get_track_count() == 2

    def test_remove_track(self) -> None:
        """Test removing tracks from the sidebar."""
        sidebar = TrackSidebar()
        sidebar.add_track("Track 1")
        sidebar.add_track("Track 2")

        # Remove first track
        result = sidebar.remove_track(0)
        assert result is True
        assert sidebar.get_track_count() == 1

        # Try to remove invalid index
        result = sidebar.remove_track(10)
        assert result is False

    def test_clear_tracks(self) -> None:
        """Test clearing all tracks."""
        sidebar = TrackSidebar()
        sidebar.add_track("Track 1")
        sidebar.add_track("Track 2")
        sidebar.add_track("Track 3")

        sidebar.clear_tracks()
        assert sidebar.get_track_count() == 0

    def test_set_tracks(self) -> None:
        """Test setting the entire track list."""
        sidebar = TrackSidebar()
        tracks = ["Track 1", "Track 2", "Track 3"]

        sidebar.set_tracks(tracks)

        assert sidebar.get_track_count() == 3
        # First track should be auto-selected
        assert sidebar.get_selected_index() == 0

    def test_track_selection(self) -> None:
        """Test track selection."""
        sidebar = TrackSidebar()
        sidebar.add_track("Track 1")
        sidebar.add_track("Track 2")

        # Set up signal spy
        selection_spy = QSignalSpy(sidebar.track_selected)
        assert selection_spy.isValid()

        # Select track
        sidebar.set_selected_track(1)
        assert sidebar.get_selected_index() == 1

        # Signal should have been emitted
        assert selection_spy.count() == 1

    def test_add_track_button_signal(self) -> None:
        """Test that Add Track button emits signal."""
        sidebar = TrackSidebar()

        # Set up signal spy
        click_spy = QSignalSpy(sidebar.add_track_clicked)
        assert click_spy.isValid()

        # Simulate button click
        sidebar._add_track_button.click()

        # Signal should have been emitted
        assert click_spy.count() == 1


class TestPlaybackControls:
    """Tests for the PlaybackControls widget."""

    def test_initialization(self) -> None:
        """Test creating a PlaybackControls instance."""
        controls = PlaybackControls()

        assert controls is not None

    def test_set_track_title(self) -> None:
        """Test setting the track title."""
        controls = PlaybackControls()

        controls.set_track_title("Test Track")
        assert controls._track_title.text() == "Test Track"

    def test_set_duration(self) -> None:
        """Test setting the track duration."""
        controls = PlaybackControls()

        controls.set_duration(120000)  # 2 minutes
        assert controls._progress_slider.maximum() == 120000

    def test_time_formatting(self) -> None:
        """Test time formatting."""
        # 0 seconds
        assert PlaybackControls._format_time(0) == "0:00"

        # 30 seconds
        assert PlaybackControls._format_time(30000) == "0:30"

        # 2 minutes 15 seconds
        assert PlaybackControls._format_time(135000) == "2:15"

        # 10 minutes 5 seconds
        assert PlaybackControls._format_time(605000) == "10:05"

    def test_set_skip_increment(self) -> None:
        """Test setting skip increment display."""
        controls = PlaybackControls()

        controls.set_skip_increment(10)
        assert controls._skip_back_button.text() == "<<10s"
        assert controls._skip_forward_button.text() == "10s>>"

    def test_play_button_signal(self) -> None:
        """Test that play button emits signal."""
        controls = PlaybackControls()

        # Set up signal spy
        play_spy = QSignalSpy(controls.play_clicked)
        assert play_spy.isValid()

        # Click button
        controls._play_button.click()

        # Signal should have been emitted
        assert play_spy.count() == 1

    def test_pause_button_signal(self) -> None:
        """Test that pause button emits signal."""
        controls = PlaybackControls()

        # Set up signal spy
        pause_spy = QSignalSpy(controls.pause_clicked)
        assert pause_spy.isValid()

        # Click button
        controls._pause_button.click()

        # Signal should have been emitted
        assert pause_spy.count() == 1

    def test_skip_forward_button_signal(self) -> None:
        """Test that skip forward button emits signal."""
        controls = PlaybackControls()

        # Set up signal spy
        skip_spy = QSignalSpy(controls.skip_forward_clicked)
        assert skip_spy.isValid()

        # Click button
        controls._skip_forward_button.click()

        # Signal should have been emitted
        assert skip_spy.count() == 1

    def test_skip_backward_button_signal(self) -> None:
        """Test that skip backward button emits signal."""
        controls = PlaybackControls()

        # Set up signal spy
        skip_spy = QSignalSpy(controls.skip_backward_clicked)
        assert skip_spy.isValid()

        # Click button
        controls._skip_back_button.click()

        # Signal should have been emitted
        assert skip_spy.count() == 1


class TestMarkerList:
    """Tests for the MarkerList widget."""

    def test_initialization(self) -> None:
        """Test creating a MarkerList instance."""
        marker_list = MarkerList()

        assert marker_list is not None
        assert marker_list.get_marker_count() == 0
        assert marker_list.get_selected_index() == -1

    def test_add_marker(self) -> None:
        """Test adding markers to the list."""
        marker_list = MarkerList()

        marker_list.add_marker("Marker 1", 1000)
        assert marker_list.get_marker_count() == 1

        marker_list.add_marker("Marker 2", 2000)
        assert marker_list.get_marker_count() == 2

    def test_remove_marker(self) -> None:
        """Test removing markers from the list."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)
        marker_list.add_marker("Marker 2", 2000)

        # Remove first marker
        result = marker_list.remove_marker(0)
        assert result is True
        assert marker_list.get_marker_count() == 1

        # Try to remove invalid index
        result = marker_list.remove_marker(10)
        assert result is False

    def test_clear_markers(self) -> None:
        """Test clearing all markers."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)
        marker_list.add_marker("Marker 2", 2000)

        marker_list.clear_markers()
        assert marker_list.get_marker_count() == 0

    def test_set_markers(self) -> None:
        """Test setting the entire marker list."""
        marker_list = MarkerList()
        markers = [("Marker 1", 1000), ("Marker 2", 2000), ("Marker 3", 3000)]

        marker_list.set_markers(markers)

        assert marker_list.get_marker_count() == 3

    def test_update_marker(self) -> None:
        """Test updating a marker."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)

        result = marker_list.update_marker(0, "Updated Marker", 1500)
        assert result is True

        # Try to update invalid index
        result = marker_list.update_marker(10, "Invalid", 2000)
        assert result is False

    def test_marker_selection(self) -> None:
        """Test marker selection."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)
        marker_list.add_marker("Marker 2", 2000)

        # Set up signal spy
        selection_spy = QSignalSpy(marker_list.marker_selected)
        assert selection_spy.isValid()

        # Select marker
        marker_list.set_selected_marker(1)
        assert marker_list.get_selected_index() == 1

        # Signal should have been emitted
        assert selection_spy.count() == 1

    def test_add_marker_button_signal(self) -> None:
        """Test that Add Marker button emits signal."""
        marker_list = MarkerList()

        # Set up signal spy
        click_spy = QSignalSpy(marker_list.add_marker_clicked)
        assert click_spy.isValid()

        # Simulate button click
        marker_list._add_marker_button.click()

        # Signal should have been emitted
        assert click_spy.count() == 1

    def test_edit_button_signal(self) -> None:
        """Test that edit button emits signal when marker selected."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)
        marker_list.set_selected_marker(0)

        # Set up signal spy
        edit_spy = QSignalSpy(marker_list.edit_marker_clicked)
        assert edit_spy.isValid()

        # Click edit button
        marker_list._edit_button.click()

        # Signal should have been emitted with index
        assert edit_spy.count() == 1

    def test_delete_button_signal(self) -> None:
        """Test that delete button emits signal when marker selected."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)
        marker_list.set_selected_marker(0)

        # Set up signal spy
        delete_spy = QSignalSpy(marker_list.delete_marker_clicked)
        assert delete_spy.isValid()

        # Click delete button
        marker_list._delete_button.click()

        # Signal should have been emitted with index
        assert delete_spy.count() == 1

    def test_edit_delete_buttons_disabled_without_selection(self) -> None:
        """Test that edit/delete buttons are disabled without selection."""
        marker_list = MarkerList()
        marker_list.add_marker("Marker 1", 1000)

        # Initially no selection, buttons should be disabled
        assert marker_list._edit_button.isEnabled() is False
        assert marker_list._delete_button.isEnabled() is False

        # Select marker
        marker_list.set_selected_marker(0)

        # Buttons should now be enabled
        assert marker_list._edit_button.isEnabled() is True
        assert marker_list._delete_button.isEnabled() is True


class TestMainWindow:
    """Tests for the MainWindow."""

    def test_initialization(self) -> None:
        """Test creating a MainWindow instance."""
        window = MainWindow()

        assert window is not None
        assert window.windowTitle() == "Rehearsal Track Marker"

    def test_window_size(self) -> None:
        """Test window size constraints."""
        window = MainWindow()

        # Check minimum size
        min_size = window.minimumSize()
        assert min_size.width() == 800
        assert min_size.height() == 600

    def test_menu_bar_exists(self) -> None:
        """Test that menu bar is created."""
        window = MainWindow()

        menu_bar = window.menuBar()
        assert menu_bar is not None

        # Check that menus exist
        actions = menu_bar.actions()
        menu_titles = [action.text() for action in actions]

        assert "&File" in menu_titles
        assert "&Edit" in menu_titles
        assert "&Help" in menu_titles

    def test_component_accessors(self) -> None:
        """Test that UI component accessors work."""
        window = MainWindow()

        # Check that components are accessible
        assert window.track_sidebar is not None
        assert window.playback_controls is not None
        assert window.marker_list is not None

        # Check types
        assert isinstance(window.track_sidebar, TrackSidebar)
        assert isinstance(window.playback_controls, PlaybackControls)
        assert isinstance(window.marker_list, MarkerList)

    def test_menu_actions_exist(self) -> None:
        """Test that menu actions are accessible."""
        window = MainWindow()

        # File menu actions
        assert window.new_show_action is not None
        assert window.open_show_action is not None
        assert window.save_show_action is not None
        assert window.save_show_as_action is not None
        assert window.import_show_action is not None
        assert window.export_show_action is not None

        # Edit menu actions
        assert window.settings_action is not None

        # Help menu actions
        assert window.about_action is not None


class TestSettingsDialog:
    """Tests for the SettingsDialog."""

    def test_initialization(self) -> None:
        """Test creating a SettingsDialog instance."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        assert dialog is not None
        assert dialog.windowTitle() == "Settings"

    def test_default_values_displayed(self) -> None:
        """Test that default values are correctly displayed."""
        dialog = SettingsDialog(skip_increment_seconds=7, marker_nudge_increment_ms=150)

        assert dialog.get_skip_increment_seconds() == 7
        assert dialog.get_marker_nudge_increment_ms() == 150

    def test_get_skip_increment(self) -> None:
        """Test getting skip increment value."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        # Default value
        assert dialog.get_skip_increment_seconds() == 5

        # Change value
        dialog._skip_increment_input.setValue(10)
        assert dialog.get_skip_increment_seconds() == 10

    def test_get_marker_nudge_increment(self) -> None:
        """Test getting marker nudge increment value."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        # Default value
        assert dialog.get_marker_nudge_increment_ms() == 100

        # Change value
        dialog._marker_nudge_input.setValue(200)
        assert dialog.get_marker_nudge_increment_ms() == 200

    def test_skip_increment_range(self) -> None:
        """Test that skip increment has proper constraints."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        # Test minimum
        assert dialog._skip_increment_input.minimum() == 1

        # Test maximum
        assert dialog._skip_increment_input.maximum() == 60

    def test_marker_nudge_increment_range(self) -> None:
        """Test that marker nudge increment has proper constraints."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        # Test minimum
        assert dialog._marker_nudge_input.minimum() == 10

        # Test maximum
        assert dialog._marker_nudge_input.maximum() == 1000

    def test_marker_nudge_step(self) -> None:
        """Test that marker nudge increment has 10ms step size."""
        dialog = SettingsDialog(skip_increment_seconds=5, marker_nudge_increment_ms=100)

        assert dialog._marker_nudge_input.singleStep() == 10
