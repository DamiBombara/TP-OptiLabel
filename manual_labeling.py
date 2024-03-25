from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter


from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,QSizePolicy)

import cv2

from PyQt5.QtGui import QImage
import PyQt5.QtGui  as QtGui


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.window_width = 700
        self.window_height = 700

        self.printer = QPrinter()
        self.zoom_factor = 1.0

        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)

        #Temporary buttons
        open_button = QPushButton("Open Image")
        open_button.clicked.connect(self.open_image)
        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.zoom_out)
        reset_button = QPushButton("Reset Zoom")
        reset_button.clicked.connect(self.reset_zoom)

        layout = QVBoxLayout()
        layout.addWidget(self.image_label)
        button_layout = QHBoxLayout()
        button_layout.addWidget(open_button)
        button_layout.addWidget(zoom_in_button)
        button_layout.addWidget(zoom_out_button)
        button_layout.addWidget(reset_button)
        layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        self.setFixedSize(self.window_width, self.window_height)


    def open_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        #filename = "vbg2.png"
        img = cv2.imread(filename)
        img = self.convert_cv_qt(img)
        self.image_label.setPixmap(img)
        # if filename:
        #     self.pixmap = QPixmap(filename)
        #     self.display_image()

    def zoom_in(self):
        self.zoom_factor *= 1.25
        self.display_image()

    def zoom_out(self):
        self.zoom_factor /= 1.25
        self.zoom_factor = max(self.zoom_factor, 0.25)  # Minimum zoom level

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.display_image()

    def display_image(self):
        self.image_label.resize(self.zoom_factor * self.image_label.pixmap().size())

    def convert_cv_qt(self,cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.window_width, self.window_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea

    app = QApplication(sys.argv)
    mainWindow = ImageViewer()
    mainWindow.show()
    sys.exit(app.exec_())