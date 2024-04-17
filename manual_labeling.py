from PyQt5.QtCore import Qt, QEvent
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

        self.zoom_factor = 1.0
        self.image_read = False

        self.image_label = QLabel()
        self.image_label.setBackgroundRole(QPalette.Base)
        self.image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image_label.setScaledContents(True)

        self.printer = QPrinter()

        self.scrollArea = QScrollArea()
        self.scrollArea.setBackgroundRole(QPalette.Dark)
        self.scrollArea.setWidget(self.image_label)

        # Temporary buttons
        open_button = QPushButton("Open Image")
        open_button.clicked.connect(self.open_image)
        zoom_in_button = QPushButton("Zoom In")
        zoom_in_button.clicked.connect(self.zoom_in)
        zoom_out_button = QPushButton("Zoom Out")
        zoom_out_button.clicked.connect(self.zoom_out)
        reset_button = QPushButton("Reset Zoom")
        reset_button.clicked.connect(self.reset_zoom)

        button_layout = QHBoxLayout()
        button_layout.addWidget(open_button)
        button_layout.addWidget(zoom_in_button)
        button_layout.addWidget(zoom_out_button)
        button_layout.addWidget(reset_button)
        
        image_widget = QVBoxLayout()
        image_widget.addWidget(self.image_label)
        image_widget.addWidget(self.scrollArea)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.scrollArea)
        main_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.setFixedSize(self.window_width, self.window_height)


    def open_image(self):
        options = QFileDialog.Options()

        fileName, _ = QFileDialog.getOpenFileName(self, 'QFileDialog.getOpenFileName()', '',
                                                  'Images (*.png *.jpeg *.jpg *.bmp *.gif)', options=options)

        if fileName:
            self.image_read = True                    
    
        img = cv2.imread(fileName)
        img = self.convert_cv_qt(img)
        self.image_label.setPixmap(img)
        
        self.scrollArea.setVisible(True)
        

    def zoom_in(self):
        if self.image_read:
            self.zoom_factor *= 1.25
            self.display_image()
            self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), self.zoom_factor)
            self.adjustScrollBar(self.scrollArea.verticalScrollBar(), self.zoom_factor)


    def zoom_out(self):
        if self.image_read:
            self.zoom_factor /= 1.25
            self.zoom_factor = max(self.zoom_factor, 0.25)  # Minimum zoom level
            self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), self.zoom_factor)
            self.adjustScrollBar(self.scrollArea.verticalScrollBar(), self.zoom_factor)


    def reset_zoom(self):
        if self.image_read:
            self.zoom_factor = 1.0
            self.display_image()
            self.adjustScrollBar(self.scrollArea.horizontalScrollBar(), self.zoom_factor)
            self.adjustScrollBar(self.scrollArea.verticalScrollBar(), self.zoom_factor)

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

    def adjustScrollBar(self, scrollBar, factor):
        scrollBar.setValue(int(factor * scrollBar.value()
                               + ((factor - 1) * scrollBar.pageStep() / 2)))

    def mousePressEvent(self, event):
        if self.image_label.pixmap() and event.button() == Qt.LeftButton:
            print("Image Clicked at:", event.pos())
            # Emit a signal or perform any action you want when the image is clicked
            # Example: self.imageClicked.emit(event.pos())



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QScrollArea

    app = QApplication(sys.argv)
    mainWindow = ImageViewer()
    mainWindow.show()
    sys.exit(app.exec_())