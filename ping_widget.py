import sys
import subprocess
import re
import locale
import numpy as np
import json
import os

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QMenu
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QCloseEvent, QAction

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- Main Settings ---
PING_TARGET = "8.8.8.8"
UPDATE_INTERVAL_MS = 1000
MAX_DATA_POINTS = 100
PING_EXECUTABLE = 'C:\\Windows\\System32\\ping.exe'
SETTINGS_FILE = "ping_widget_settings.json"

class SmartHandle(QPushButton):
    """A smart handle button for moving and resizing the main window."""
    def __init__(self, parent=None):
        super().__init__(parent)
        button_size = 4
        self.setFixedSize(button_size, button_size)
        self.setToolTip("Drag to move, Ctrl+Drag to resize")
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 0, 0, 180); border: none; border-radius: {button_size // 1}px;
            }}
            QPushButton:hover {{ background-color: rgba(255, 0, 0, 220); }}
        """)

        # State variables for dragging and resizing
        self.current_action = None
        self.drag_start_position = QPoint()
        self.window_start_geometry = QRect()

    def mousePressEvent(self, event):
        """Initiates move or resize action based on Ctrl key state."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position = event.globalPosition().toPoint()
            self.window_start_geometry = self.parent().geometry()

            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.KeyboardModifier.ControlModifier:
                self.current_action = 'resize'
                self.setCursor(Qt.CursorShape.SizeFDiagCursor)
            else:
                self.current_action = 'move'
                self.setCursor(Qt.CursorShape.SizeAllCursor)
            event.accept()

    def mouseMoveEvent(self, event):
        """Handles the window movement or resizing."""
        if not self.current_action or not event.buttons() == Qt.MouseButton.LeftButton:
            return

        delta = event.globalPosition().toPoint() - self.drag_start_position

        if self.current_action == 'move':
            new_pos = self.window_start_geometry.topLeft() + delta
            self.parent().move(new_pos)

        elif self.current_action == 'resize':
            start_size = self.window_start_geometry.size()
            new_width = start_size.width() + delta.x()
            new_height = start_size.height() + delta.y()

            min_w, min_h = 100, 20
            if new_width < min_w: new_width = min_w
            if new_height < min_h: new_height = min_h

            self.parent().resize(new_width, new_height)

        event.accept()

    def mouseReleaseEvent(self, event):
        """Finalizes the action and saves the new settings."""
        if self.current_action:
            self.parent().save_settings()

        self.current_action = None
        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.accept()

class MatplotlibCanvas(FigureCanvas):
    """A custom widget to display the Matplotlib chart."""
    def __init__(self, parent=None, dpi=100):
        self.fig = Figure(dpi=dpi, facecolor='none')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        # Make the chart background transparent
        self.fig.patch.set_alpha(0.0)
        self.axes.patch.set_alpha(0.0)

        # Configure the chart appearance
        self.axes.axis('off')
        self.axes.set_xlim(0, MAX_DATA_POINTS)
        self.axes.set_ylim(0, 50) # Initial Y-axis limit
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

class PingWidget(QMainWindow):
    """The main widget window."""
    def __init__(self):
        super().__init__()

        # Set window flags for a frameless, always-on-top tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet("background:transparent;")

        # Load previous geometry or set a default
        self.load_settings()

        # Set up the main chart canvas
        self.canvas = MatplotlibCanvas(self)
        self.setCentralWidget(self.canvas)

        # Create the smart handle as a floating child widget
        self.smart_handle = SmartHandle(self)

        # Initialize chart data
        self.x_data = np.arange(MAX_DATA_POINTS)
        self.y_data = np.zeros(MAX_DATA_POINTS)
        self.max_ping_so_far = 50

        # Create plot lines
        self.line, = self.canvas.axes.plot(self.x_data, self.y_data, color='#00aaff', lw=1)
        self.error_points, = self.canvas.axes.plot([], [], 'o', color='red', markersize=5)

        # Timer for updating the plot
        self.plot_timer = QTimer(self)
        self.plot_timer.setInterval(UPDATE_INTERVAL_MS)
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start()

        # Enable a context menu for exiting
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_exit_menu)

    def get_ping_time(self, host):
        """Pings a host and returns the latency in ms, or None on failure."""
        try:
            result_bytes = subprocess.check_output(
                [PING_EXECUTABLE, '-n', '1', '-w', '1000', host],
                stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW
            )
            encoding = locale.getpreferredencoding()
            raw_output = result_bytes.decode(encoding, errors='ignore')
            pattern = r"(?:time|زمان)[=<](\d+)ms"
            match = re.search(pattern, raw_output, re.IGNORECASE)
            return int(match.group(1)) if match else None
        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None

    def update_plot(self):
        """Fetches new ping data and updates the chart."""
        ping_time = self.get_ping_time(PING_TARGET)

        # Roll the data array to the left
        self.y_data = np.roll(self.y_data, -1)
        self.y_data[-1] = ping_time if ping_time is not None else 0

        # Update the dynamic Y-axis limit
        if ping_time and ping_time > self.max_ping_so_far:
            self.max_ping_so_far = ping_time
        self.canvas.axes.set_ylim(-self.max_ping_so_far * 0.05, self.max_ping_so_far * 1.1)

        # Update plot data
        self.line.set_ydata(self.y_data)
        error_indices = np.where(self.y_data == 0)[0]
        self.error_points.set_data(self.x_data[error_indices], self.y_data[error_indices])

        # Redraw the canvas
        self.canvas.draw()

    def resizeEvent(self, event):
        """Moves the smart handle to the bottom-right corner when the window is resized."""
        super().resizeEvent(event)
        btn_x = self.width() - self.smart_handle.width() - 5
        btn_y = self.height() - self.smart_handle.height() - 5
        self.smart_handle.move(btn_x, btn_y)

    def get_settings_path(self):
        """Returns the full path for the settings file."""
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        return os.path.join(base_path, SETTINGS_FILE)

    def load_settings(self):
        """Loads window geometry from the settings file."""
        try:
            with open(self.get_settings_path(), 'r') as f:
                settings = json.load(f)
                self.setGeometry(
                    settings.get('x', 100), settings.get('y', 100),
                    settings.get('width', 400), settings.get('height', 100)
                )
        except (FileNotFoundError, json.JSONDecodeError):
            self.setGeometry(100, 100, 400, 100)

    def save_settings(self):
        """Saves the current window geometry to the settings file."""
        settings = {'x': self.x(), 'y': self.y(), 'width': self.width(), 'height': self.height()}
        with open(self.get_settings_path(), 'w') as f:
            json.dump(settings, f, indent=4)

    def show_exit_menu(self, pos):
        """Shows a context menu with an 'Exit' option."""
        menu = QMenu()
        menu.addAction("Exit", self.close)
        menu.exec(self.mapToGlobal(pos))

    def closeEvent(self, event: QCloseEvent):
        """Ensures settings are saved before the application quits."""
        self.save_settings()
        QApplication.quit()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = PingWidget()
    widget.show()
    sys.exit(app.exec())