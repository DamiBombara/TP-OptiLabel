from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel)
import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import pyqtSignal

class PaintableLabel(QLabel):
    finishedDrawing = pyqtSignal(QPoint, QPoint)
    def __init__(self, parent=None):
        super(PaintableLabel, self).__init__(parent)
        self.begin = QPoint()
        self.end = QPoint()
        self.drawing = False
        self.setMouseTracking(True)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.drawing:
            painter = QPainter(self)
            painter.setPen(QColor(255, 0, 0, 128))  # Semi-transparent red pen
            painter.drawRect(QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.begin = event.pos()
            self.end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self.end = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.update()
            self.finishedDrawing.emit(self.begin, self.end)


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Image Viewer with Masking")
        self.setGeometry(100, 100, 800, 600)
        self.imageLabel = PaintableLabel(self)
        self.imageLabel.finishedDrawing.connect(self.drawMask)
        self.originalImage = None
        self.maskImage = None
        self.zoom_factor = 1.0

        self.window_width = 700
        self.window_height = 700
        
        
        open_button = QPushButton("Open Image")
        open_button.clicked.connect(self.openImage)
        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.zoom_out)
        reset_button = QPushButton("Reset Zoom")
        reset_button.clicked.connect(self.reset_zoom)
        saveButton = QPushButton('Save Mask')
        saveButton.clicked.connect(self.saveMaskAsPng)

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        button_layout = QHBoxLayout()
        button_layout.addWidget(open_button)
        button_layout.addWidget(zoom_in_button)
        button_layout.addWidget(zoom_out_button)
        button_layout.addWidget(reset_button)
        button_layout.addWidget(saveButton)
        layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        

    def openImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.originalImage = cv2.imread(filename)
            self.maskImage = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.updateDisplay()

    def drawMask(self, begin, end):
        if self.originalImage is not None:
            x_start, y_start = begin.x(), begin.y()
            x_end, y_end = end.x(), end.y()
            x1, x2 = min(x_start, x_end), max(x_start, x_end)
            y1, y2 = min(y_start, y_end), max(y_start, y_end)
            self.maskImage[y1:y2, x1:x2] = 255  
            self.updateDisplay()

    def saveMaskAsPng(self):
        if self.maskImage is not None:
            Image.fromarray(self.maskImage).save("mask.png")
            print("Mask saved as mask.png")

    def updateDisplay(self):
        if self.originalImage is not None:
            imageToShow = cv2.cvtColor(self.originalImage, cv2.COLOR_BGR2RGB)
            height, width, _ = imageToShow.shape
            bytesPerLine = 3 * width
            qImage = QImage(imageToShow.data, width, height, bytesPerLine, QImage.Format_RGB888)

            if self.maskImage is not None:
                mask = cv2.cvtColor(self.maskImage, cv2.COLOR_GRAY2BGR)
                coloredMask = np.zeros_like(mask, dtype=np.uint8)
                coloredMask[self.maskImage > 0] = [255, 0, 0]  
                imageToShow = cv2.addWeighted(imageToShow, 1, coloredMask, 0.4, 0)
                qImage = QImage(imageToShow.data, width, height, bytesPerLine, QImage.Format_RGB888)

            self.imageLabel.setPixmap(QPixmap.fromImage(qImage))
            self.imageLabel.resize(self.zoom_factor * self.imageLabel.pixmap().size())
            self.imageLabel.setPixmap(QPixmap.fromImage(qImage))
            

    def zoom_in(self):
        self.zoom_factor *= 1.25
        self.updateDisplay()

    def zoom_out(self):
        self.zoom_factor /= 1.25
        self.zoom_factor = max(self.zoom_factor, 0.25)  
        self.updateDisplay()

    def reset_zoom(self):
        self.zoom_factor = 1.0
        self.updateDisplay()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    mainWindow = ImageViewer()
    mainWindow.show()
    sys.exit(app.exec_())
