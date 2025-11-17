"""Repository for loading and saving show data."""

import json
from pathlib import Path

from .file_manager import FileManager
from ..models import Show
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ShowRepository:
    """
    Handles loading and saving show data to/from JSON files.

    Uses FileManager for path resolution and directory management.
    """

    def __init__(self, file_manager: FileManager | None = None):
        """
        Initialize the show repository.

        Args:
            file_manager: Optional FileManager instance. If None, creates a new one.
        """
        self.file_manager = file_manager or FileManager()

    def save(self, show: Show) -> None:
        """
        Save a show to disk.

        Args:
            show: The show to save

        Raises:
            OSError: If file operations fail
            ValueError: If show data is invalid
        """
        logger.info(f"Saving show: {show.name}")

        # Ensure show directories exist
        self.file_manager.create_show_directories(show.name)

        # Get the path to the show's JSON file
        show_file_path = self.file_manager.get_show_file_path(show.name)

        # Convert show to dictionary
        show_data = show.to_dict()

        # Write JSON file
        with open(show_file_path, "w", encoding="utf-8") as f:
            json.dump(show_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved show to: {show_file_path}")

    def load(self, show_name: str) -> Show:
        """
        Load a show from disk.

        Args:
            show_name: Name of the show to load

        Returns:
            The loaded Show instance

        Raises:
            FileNotFoundError: If show file doesn't exist
            json.JSONDecodeError: If JSON is malformed
            KeyError: If required JSON fields are missing
            ValueError: If show data is invalid
        """
        logger.info(f"Loading show: {show_name}")

        show_file_path = self.file_manager.get_show_file_path(show_name)

        if not show_file_path.exists():
            raise FileNotFoundError(f"Show file not found: {show_file_path}")

        # Read JSON file
        with open(show_file_path, "r", encoding="utf-8") as f:
            show_data = json.load(f)

        # Get the audio directory for this show
        audio_dir = self.file_manager.get_show_audio_directory(show_name)

        # Create Show instance from dictionary
        show = Show.from_dict(show_data, audio_dir)

        logger.info(f"Loaded show: {show.name} with {len(show.tracks)} tracks")

        return show

    def exists(self, show_name: str) -> bool:
        """
        Check if a show exists.

        Args:
            show_name: Name of the show

        Returns:
            True if show exists, False otherwise
        """
        return self.file_manager.show_exists(show_name)

    def delete(self, show_name: str) -> bool:
        """
        Delete a show and all its files.

        Args:
            show_name: Name of the show to delete

        Returns:
            True if show was deleted, False if not found

        Raises:
            OSError: If deletion fails
        """
        return self.file_manager.delete_show(show_name)

    def list_shows(self) -> list[str]:
        """
        List all available shows.

        Returns:
            List of show names
        """
        return self.file_manager.list_shows()

    def export_show(self, show: Show, export_path: Path) -> None:
        """
        Export a show to a JSON file at the specified path.

        This creates a standalone JSON file that can be shared.
        Audio files are NOT included in the export.

        Args:
            show: The show to export
            export_path: Path where the JSON file should be saved

        Raises:
            OSError: If file operations fail
        """
        logger.info(f"Exporting show '{show.name}' to: {export_path}")

        # Ensure parent directory exists
        export_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert show to dictionary
        show_data = show.to_dict()

        # Write JSON file
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(show_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported show to: {export_path}")

    def import_show(
        self, import_path: Path, audio_source_dir: Path | None = None
    ) -> Show:
        """
        Import a show from a JSON file.

        Args:
            import_path: Path to the JSON file to import
            audio_source_dir: Optional directory containing audio files.
                            If None, assumes audio files are in same directory as JSON.

        Returns:
            The imported Show instance (not yet saved to disk)

        Raises:
            FileNotFoundError: If import file doesn't exist
            json.JSONDecodeError: If JSON is malformed
            KeyError: If required JSON fields are missing
            ValueError: If show data is invalid
        """
        logger.info(f"Importing show from: {import_path}")

        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")

        # Read JSON file
        with open(import_path, "r", encoding="utf-8") as f:
            show_data = json.load(f)

        # Determine audio source directory
        if audio_source_dir is None:
            audio_source_dir = import_path.parent / "audio"

        # Create Show instance
        # Note: Audio paths will need to be updated when files are copied
        show = Show.from_dict(show_data, audio_source_dir)

        logger.info(f"Imported show: {show.name} with {len(show.tracks)} tracks")

        return show
