import sys
import subprocess
import re
import locale
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QPoint, QRect
from PySide6.QtGui import QPainter, QColor, QBrush

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# --- تنظیمات اصلی ---
PING_TARGET = "8.8.8.8"
UPDATE_INTERVAL_MS = 1000
MAX_DATA_POINTS = 100
PING_EXECUTABLE = 'C:\\Windows\\System32\\ping.exe'

# مختصات و اندازه نقطه جابجایی
DRAG_HANDLE_X = 5
DRAG_HANDLE_Y = 5
DRAG_HANDLE_SIZE = 14

class MatplotlibCanvas(FigureCanvas):
    """کلاس ویجت برای نمایش نمودار Matplotlib."""
    def __init__(self, parent=None, dpi=100):
        self.fig = Figure(dpi=dpi, facecolor='none')
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)

        # تنظیمات ظاهری نمودار
        self.fig.patch.set_alpha(0.0)
        self.axes.patch.set_alpha(0.0)
        self.axes.axis('off')
        self.axes.set_xlim(0, MAX_DATA_POINTS)
        self.axes.set_ylim(0, 50) # مقدار اولیه
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)

class PingWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        # --- تنظیمات پنجره ---
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setGeometry(100, 100, 400, 100)

        # --- ساختار ویجت‌ها ---
        # یک کانتینر برای قرار دادن نمودار
        container = QWidget()
        layout = QVBoxLayout(container)
        # ایجاد فاصله از بالا برای نقطه جابجایی
        layout.setContentsMargins(0, DRAG_HANDLE_Y + DRAG_HANDLE_SIZE, 0, 0)

        # ساخت و اضافه کردن نمودار به کانتینر
        self.canvas = MatplotlibCanvas(self)
        layout.addWidget(self.canvas)
        self.setCentralWidget(container)

        # داده‌های نمودار
        self.x_data = np.arange(MAX_DATA_POINTS)
        self.y_data = np.zeros(MAX_DATA_POINTS)
        self.max_ping_so_far = 50

        # رسم اولیه خطوط
        self.line, = self.canvas.axes.plot(self.x_data, self.y_data, color='#00aaff', lw=2)
        self.error_points, = self.canvas.axes.plot([], [], 'o', color='red', markersize=5)

        # تایمر برای به‌روزرسانی
        self.timer = QTimer()
        self.timer.setInterval(UPDATE_INTERVAL_MS)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start()

        # متغیرهای جابجایی
        self.dragging = False
        self.drag_start_position = QPoint()
        self.drag_handle_rect = QRect(DRAG_HANDLE_X, DRAG_HANDLE_Y, DRAG_HANDLE_SIZE, DRAG_HANDLE_SIZE)

    def get_ping_time(self, host):
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
        ping_time = self.get_ping_time(PING_TARGET)
        self.y_data = np.roll(self.y_data, -1)
        self.y_data[-1] = ping_time if ping_time is not None else 0
        if ping_time and ping_time > self.max_ping_so_far:
            self.max_ping_so_far = ping_time
        self.canvas.axes.set_ylim(-self.max_ping_so_far * 0.05, self.max_ping_so_far * 1.1)
        self.line.set_ydata(self.y_data)
        error_indices = np.where(self.y_data == 0)[0]
        self.error_points.set_data(self.x_data[error_indices], self.y_data[error_indices])
        self.canvas.draw()
        self.update() # درخواست آپدیت برای کشیدن نقطه

    # --- این بخش دقیقاً از کد تست سالم آمده است ---
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QBrush(QColor(120, 120, 120, 200)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.drag_handle_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.drag_handle_rect.contains(event.pos()):
                self.dragging = True
                self.drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_start_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = PingWidget()
    widget.show()
    sys.exit(app.exec())