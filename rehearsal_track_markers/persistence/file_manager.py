"""File system utilities for managing app directories and files."""

import platform
from pathlib import Path

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class FileManager:
    """
    Manages file system operations for the application.

    Handles creation of app directory structure, path resolution,
    and cross-platform compatibility.
    """

    APP_NAME = "RehearsalTrackMarker"

    def __init__(self, base_path: Path | None = None):
        """
        Initialize the file manager.

        Args:
            base_path: Optional custom base path. If None, uses platform-specific default.
        """
        if base_path:
            self.base_path = Path(base_path)
        else:
            self.base_path = self._get_default_base_path()

        logger.info(f"FileManager initialized with base path: {self.base_path}")

    @staticmethod
    def _get_default_base_path() -> Path:
        """
        Get the default base path for app data based on platform.

        Returns:
            Platform-specific base path for application data
        """
        system = platform.system()

        if system == "Windows":
            # Windows: %APPDATA%
            app_data = Path.home() / "AppData" / "Roaming"
        elif system == "Darwin":
            # macOS: ~/Library/Application Support
            app_data = Path.home() / "Library" / "Application Support"
        else:
            # Linux and others: ~/.local/share
            app_data = Path.home() / ".local" / "share"

        return app_data / FileManager.APP_NAME

    def get_shows_directory(self) -> Path:
        """
        Get the path to the shows directory.

        Returns:
            Path to the shows directory
        """
        return self.base_path / "shows"

    def get_show_directory(self, show_name: str) -> Path:
        """
        Get the path to a specific show's directory.

        Args:
            show_name: Name of the show

        Returns:
            Path to the show's directory
        """
        return self.get_shows_directory() / show_name

    def get_show_audio_directory(self, show_name: str) -> Path:
        """
        Get the path to a show's audio directory.

        Args:
            show_name: Name of the show

        Returns:
            Path to the show's audio directory
        """
        return self.get_show_directory(show_name) / "audio"

    def get_show_file_path(self, show_name: str) -> Path:
        """
        Get the path to a show's JSON file.

        Args:
            show_name: Name of the show

        Returns:
            Path to the show's JSON file
        """
        return self.get_show_directory(show_name) / f"{show_name}.json"

    def create_show_directories(self, show_name: str) -> None:
        """
        Create the directory structure for a new show.

        Args:
            show_name: Name of the show

        Raises:
            OSError: If directory creation fails
        """
        show_dir = self.get_show_directory(show_name)
        audio_dir = self.get_show_audio_directory(show_name)

        logger.info(f"Creating directories for show: {show_name}")

        show_dir.mkdir(parents=True, exist_ok=True)
        audio_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Created show directory: {show_dir}")
        logger.info(f"Created audio directory: {audio_dir}")

    def show_exists(self, show_name: str) -> bool:
        """
        Check if a show exists.

        Args:
            show_name: Name of the show

        Returns:
            True if the show directory and JSON file exist, False otherwise
        """
        show_file = self.get_show_file_path(show_name)
        return show_file.exists()

    def list_shows(self) -> list[str]:
        """
        List all shows in the shows directory.

        Returns:
            List of show names
        """
        shows_dir = self.get_shows_directory()

        if not shows_dir.exists():
            return []

        show_names = []
        for item in shows_dir.iterdir():
            if item.is_dir():
                # Check if the directory has a corresponding JSON file
                json_file = item / f"{item.name}.json"
                if json_file.exists():
                    show_names.append(item.name)

        return sorted(show_names)

    def delete_show(self, show_name: str) -> bool:
        """
        Delete a show and all its associated files.

        Args:
            show_name: Name of the show to delete

        Returns:
            True if show was deleted, False if not found

        Raises:
            OSError: If deletion fails
        """
        show_dir = self.get_show_directory(show_name)

        if not show_dir.exists():
            logger.warning(f"Cannot delete show '{show_name}': not found")
            return False

        import shutil

        logger.info(f"Deleting show: {show_name}")
        shutil.rmtree(show_dir)
        logger.info(f"Deleted show directory: {show_dir}")

        return True

    def ensure_base_directories(self) -> None:
        """
        Ensure base application directories exist.

        Creates the base path and shows directory if they don't exist.
        """
        shows_dir = self.get_shows_directory()
        shows_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured base directories exist: {shows_dir}")
