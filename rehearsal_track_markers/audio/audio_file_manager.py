"""Audio file management utilities."""

import shutil
from pathlib import Path

from ..models import Track
from ..persistence.file_manager import FileManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class AudioFileManager:
    """
    Manages audio file operations including copying and validation.

    Handles copying audio files to app storage and ensuring file integrity.
    """

    # Supported audio formats (common formats supported by Qt Multimedia)
    SUPPORTED_FORMATS = {
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".opus",
        ".wma",
        ".aiff",
        ".aif",
    }

    def __init__(self, file_manager: FileManager | None = None):
        """
        Initialize the audio file manager.

        Args:
            file_manager: Optional FileManager instance. If None, creates a new one.
        """
        self.file_manager = file_manager or FileManager()

    def is_supported_format(self, file_path: Path) -> bool:
        """
        Check if a file format is supported.

        Args:
            file_path: Path to the audio file

        Returns:
            True if format is supported, False otherwise
        """
        suffix = file_path.suffix.lower()
        return suffix in self.SUPPORTED_FORMATS

    def copy_audio_file(self, source_path: Path, show_name: str) -> Path:
        """
        Copy an audio file to the show's audio directory.

        Args:
            source_path: Path to the source audio file
            show_name: Name of the show

        Returns:
            Path to the copied audio file in app storage

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If file format is not supported
            OSError: If file copy fails
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Source audio file not found: {source_path}")

        if not self.is_supported_format(source_path):
            raise ValueError(
                f"Unsupported audio format: {source_path.suffix}. "
                f"Supported formats: {', '.join(sorted(self.SUPPORTED_FORMATS))}"
            )

        # Get destination directory
        audio_dir = self.file_manager.get_show_audio_directory(show_name)
        audio_dir.mkdir(parents=True, exist_ok=True)

        # Destination path (keep original filename)
        dest_path = audio_dir / source_path.name

        # Handle filename conflicts
        if dest_path.exists():
            # If file with same name exists, check if it's the same file
            if self._files_are_identical(source_path, dest_path):
                logger.info(
                    f"Audio file already exists and is identical: {dest_path.name}"
                )
                return dest_path

            # Generate unique filename
            dest_path = self._get_unique_filename(audio_dir, source_path.name)
            logger.warning(
                f"Filename conflict resolved. Using: {dest_path.name} instead of {source_path.name}"
            )

        # Copy file
        logger.info(f"Copying audio file: {source_path.name} -> {dest_path}")
        shutil.copy2(source_path, dest_path)

        # Verify copy
        if not dest_path.exists():
            raise OSError(f"Failed to copy audio file to: {dest_path}")

        logger.info(f"Successfully copied audio file to: {dest_path}")

        return dest_path

    def add_audio_file_to_show(self, source_path: Path, show_name: str) -> Track:
        """
        Copy an audio file and create a Track instance.

        Args:
            source_path: Path to the source audio file
            show_name: Name of the show

        Returns:
            A new Track instance with the copied audio file

        Raises:
            FileNotFoundError: If source file doesn't exist
            ValueError: If file format is not supported
            OSError: If file copy fails
        """
        dest_path = self.copy_audio_file(source_path, show_name)

        # Create Track instance
        track = Track(filename=source_path.name, audio_path=dest_path)

        logger.info(f"Created track for audio file: {source_path.name}")

        return track

    def delete_audio_file(self, audio_path: Path) -> bool:
        """
        Delete an audio file from app storage.

        Args:
            audio_path: Path to the audio file to delete

        Returns:
            True if file was deleted, False if not found

        Raises:
            OSError: If deletion fails
        """
        if not audio_path.exists():
            logger.warning(f"Cannot delete audio file: not found at {audio_path}")
            return False

        logger.info(f"Deleting audio file: {audio_path}")
        audio_path.unlink()

        return True

    @staticmethod
    def _files_are_identical(path1: Path, path2: Path) -> bool:
        """
        Check if two files are identical by comparing size and content.

        Args:
            path1: First file path
            path2: Second file path

        Returns:
            True if files are identical, False otherwise
        """
        # Quick check: compare file sizes
        if path1.stat().st_size != path2.stat().st_size:
            return False

        # Compare content (in chunks for memory efficiency)
        chunk_size = 8192
        with open(path1, "rb") as f1, open(path2, "rb") as f2:
            while True:
                chunk1 = f1.read(chunk_size)
                chunk2 = f2.read(chunk_size)

                if chunk1 != chunk2:
                    return False

                if not chunk1:  # End of file
                    return True

    @staticmethod
    def _get_unique_filename(directory: Path, filename: str) -> Path:
        """
        Generate a unique filename by appending a number.

        Args:
            directory: Directory where file will be saved
            filename: Original filename

        Returns:
            Unique file path
        """
        stem = Path(filename).stem
        suffix = Path(filename).suffix

        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = directory / new_name

            if not new_path.exists():
                return new_path

            counter += 1

            # Safety check to prevent infinite loop
            if counter > 10000:
                raise ValueError(f"Could not generate unique filename for: {filename}")
