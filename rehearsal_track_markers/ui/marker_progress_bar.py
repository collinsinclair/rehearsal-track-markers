"""Custom progress bar with marker visualization."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPen
from PySide6.QtWidgets import QSlider, QStyleOptionSlider

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class MarkerProgressBar(QSlider):
    """
    Custom progress bar slider that displays marker positions as vertical ticks.

    Extends QSlider to add visual marker indicators.
    """

    def __init__(self, orientation: Qt.Orientation = Qt.Orientation.Horizontal):
        """
        Initialize the marker progress bar.

        Args:
            orientation: Slider orientation (horizontal or vertical)
        """
        super().__init__(orientation)

        self._marker_positions: list[int] = []  # List of marker timestamps in ms

    def set_markers(self, marker_positions: list[int]) -> None:
        """
        Set the marker positions to display.

        Args:
            marker_positions: List of marker timestamps in milliseconds
        """
        self._marker_positions = sorted(marker_positions)
        self.update()  # Trigger repaint

    def clear_markers(self) -> None:
        """Clear all marker positions."""
        self._marker_positions = []
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore
        """
        Paint the slider with marker ticks.

        Args:
            event: Paint event
        """
        # First, paint the normal slider
        super().paintEvent(event)

        # Then paint marker ticks
        if not self._marker_positions:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set up pen for marker ticks
        pen = QPen(Qt.GlobalColor.red, 2)
        painter.setPen(pen)

        # Get slider geometry
        option = QStyleOptionSlider()
        self.initStyleOption(option)
        groove_rect = self.style().subControlRect(
            self.style().ComplexControl.CC_Slider,
            option,
            self.style().SubControl.SC_SliderGroove,
            self,
        )

        # Calculate slider range
        slider_min = self.minimum()
        slider_max = self.maximum()
        slider_range = slider_max - slider_min

        if slider_range == 0:
            return

        # Draw a tick for each marker
        for marker_pos in self._marker_positions:
            # Calculate position along the groove
            if slider_min <= marker_pos <= slider_max:
                # Normalize position to 0-1 range
                normalized_pos = (marker_pos - slider_min) / slider_range

                # Calculate pixel position
                if self.orientation() == Qt.Orientation.Horizontal:
                    x = int(groove_rect.left() + normalized_pos * groove_rect.width())
                    y_top = groove_rect.top() - 5
                    y_bottom = groove_rect.bottom() + 5

                    # Draw vertical tick
                    painter.drawLine(x, y_top, x, y_bottom)
                else:
                    # Vertical slider (less common, but supported)
                    y = int(
                        groove_rect.top() + (1 - normalized_pos) * groove_rect.height()
                    )
                    x_left = groove_rect.left() - 5
                    x_right = groove_rect.right() + 5

                    # Draw horizontal tick
                    painter.drawLine(x_left, y, x_right, y)

        painter.end()
