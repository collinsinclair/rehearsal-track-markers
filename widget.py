# This Python file uses the following encoding: utf-8
"""Entry point for the Rehearsal Track Marker application."""
import sys

from PySide6.QtWidgets import QApplication

from rehearsal_track_markers.ui import MainWindow


def main() -> int:
    """
    Run the application.

    Returns:
        Exit code
    """
    app = QApplication(sys.argv)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
