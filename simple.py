#Simple Panel v.1 Copyright (c) 2023 JJ Posti <techtimejourney.net> This program comes with ABSOLUTELY NO WARRANTY; for details see: http://www.gnu.org/copyleft/gpl.html.  This is free software, and you are welcome to redistribute it under GPL Version 2, June 1991")

import sys
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QLabel,
    QSpacerItem,
    QSizePolicy,
)
from PySide2.QtCore import Qt, QTimer, QRectF
from PySide2.QtGui import QPainterPath, QRegion
from ewmh import EWMH

# Define the panel dimensions and taskbar item width
PANEL_HEIGHT = 50  # Increase or decrease this value for the panel's height
CORNER_RADIUS = 6  # Adjust the radius to control corner roundness
INITIAL_SPACING = 2  # Initial spacing between taskbar items

# TaskbarItem class represents individual taskbar items for open windows
class TaskbarItem(QWidget):
    def __init__(self, window_name, window_id, panel, parent=None):
        super().__init__(parent)
        self.window_name = window_name
        self.window_id = window_id
        self.panel = panel
        self.setup_ui()

    def setup_ui(self):
        # Create a horizontal layout for the taskbar item
        layout = QHBoxLayout()
        self.setLayout(layout)
        self.label = QLabel(self.window_name)
        labelSizePolicy = self.label.sizePolicy()
        labelSizePolicy.setHorizontalStretch(0)
        labelSizePolicy.setVerticalStretch(0)
        self.label.setSizePolicy(labelSizePolicy)
        self.label.setMinimumSize(100, 30)  # Adjust the minimum size as needed
        self.label.setMaximumSize(200, 30)  # Adjust the maximum size as needed       
        layout.addWidget(self.label)

    def mousePressEvent(self, event):
        # Handle mouse click events on the taskbar item
        if event.button() == Qt.RightButton:
            self.close_window()  # Close the window on right-click
        elif event.button() == Qt.LeftButton:
            self.activate_or_restore_window()  # Activate or restore the window on left-click

    def close_window(self):
        try:
            ewmh = EWMH()
            ewmh.setCloseWindow(self.window_id)  # Close the window using EWMH
            ewmh.display.flush()
            self.panel.remove_taskbar_item(self)  # Remove the taskbar item from the panel
        except Exception as e:
            print(f"Error: {e}")

    def activate_or_restore_window(self):
        try:
            ewmh = EWMH()
            ewmh.setWmDesktop(self.window_id, 0xFFFFFFFF)  # Set window to all desktops
            ewmh.setActiveWindow(self.window_id)  # Activate the window
            ewmh.display.flush()
        except Exception as e:
            print(f"Error: {e}")

# Panel class represents the main panel window
class Panel(QMainWindow):
    def __init__(self):
        super().__init__()

        # Configure the panel window
        self.setWindowTitle("")
        self.setStyleSheet("background-color: #34568B; color: white;")
        self.setWindowFlags(Qt.Tool | Qt.FramelessWindowHint)

        # Create a central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create the taskbar layout and widget
        self.taskbar_layout = QHBoxLayout()
        self.taskbar_layout.setSpacing(2)  # Adjust the spacing value as needed
        self.taskbar_layout.setContentsMargins(0, 0, 0, 0)  # Remove layout margins
        self.taskbar_layout.setAlignment(Qt.AlignLeft)

        self.taskbar_widget = QWidget()
        self.taskbar_widget.setLayout(self.taskbar_layout)

        # Set the central widget to the taskbar_widget
        self.setCentralWidget(self.taskbar_widget)

        # Initialize EWMH and other data
        self.ewmh = EWMH()
        self.window_data = {}

        # Set the initial position and size of the panel to the screen width
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry.x(), 0, screen_geometry.width(), PANEL_HEIGHT)
        self.setMask(self.rounded_mask(self.size()))
        # Get the window ID of the panel itself
        self.panel_window_id = self.winId()

        # Create a timer to periodically update the window list
        self.window_update_timer = QTimer(self)
        self.window_update_timer.timeout.connect(self.update_window_list)
        self.window_update_timer.start(1000)  # Update every 1 second (adjust as needed)

        # Set up the taskbar items based on open windows initially
        self.setup_taskbar_items()

    def rounded_mask(self, size):
        # Create a rounded rectangular mask for the panel
        path = QPainterPath()
        panel_rect = QRectF(0, 0, size.width(), size.height())  # Create a QRectF object
        path.addRoundedRect(panel_rect, CORNER_RADIUS, CORNER_RADIUS)  # Use QRectF with addRoundedRect
        region = QRegion(path.toFillPolygon().toPolygon())
        return region

    def setup_taskbar_items(self):
        # Create taskbar items for open windows and add them to the layout
        open_windows = self.ewmh.getClientListStacking()
        for window in open_windows:
            window_name = window.get_wm_name()
            if window_name and window != self.panel_window_id:
                taskbar_item = TaskbarItem(window_name, window, self)
                self.window_data[window] = taskbar_item  # Store window ID and taskbar item
                self.taskbar_layout.addWidget(taskbar_item)

    def remove_taskbar_item(self, taskbar_item):
        try:
            # Remove the taskbar item widget from the layout and delete it
            self.taskbar_layout.removeWidget(taskbar_item)
            taskbar_item.deleteLater()
        except RuntimeError:
            pass  # Ignore the error

    def update_window_list(self):
        # Get the currently open windows
        open_windows = self.ewmh.getClientListStacking()

        # Remove taskbar items for windows that are no longer open
        for window, taskbar_item in list(self.window_data.items()):
            if window not in open_windows:
                self.remove_taskbar_item(taskbar_item)
                del self.window_data[window]

        # Create taskbar items for new open windows
        for window in open_windows:
            window_name = window.get_wm_name()
            if window_name and window != self.panel_window_id and window not in self.window_data:
                taskbar_item = TaskbarItem(window_name, window, self)
                self.window_data[window] = taskbar_item
                self.taskbar_layout.addWidget(taskbar_item)

if __name__ == "__main__":
    # Create and run the application
    app = QApplication(sys.argv)
    panel = Panel()
    panel.show()
    sys.exit(app.exec_())
