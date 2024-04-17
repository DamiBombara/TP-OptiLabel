from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,QGridLayout)
import cv2
import numpy as np
from PIL import Image
from PyQt5.QtCore import pyqtSignal
import PyQt5.QtGui  as QtGui

class ArrowButtonLayout(QVBoxLayout):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.up_button = QPushButton("Up")
        self.down_button = QPushButton("Down")
        self.right_button = QPushButton("Right")
        self.left_button = QPushButton("Left")

        # self.addWidget(self.up_button,1,2)
        # self.addWidget(self.left_button,2,1)
        # self.addWidget(self.right_button,2,3)
        # self.addWidget(self.down_button,3,2)

        self.addWidget(self.up_button)
        self.addWidget(self.left_button)
        self.addWidget(self.right_button)
        self.addWidget(self.down_button)

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
            # print(self.begin)
            # print(self.end)


class ImageWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.imageLabel = PaintableLabel(self)
        self.imageLabel.finishedDrawing.connect(self.drawMask)

        self.label_height = 500
        self.label_width = 500
        self.originalImage = None
        self.image_to_show = None
        self.imageLabel.setFixedSize(self.label_width+5,self.label_height+5)
        self.maskImage = None

        self.left_edge = 0
        self.right_edge = self.label_width
        self.top_edge=self.label_height
        self.bottom_edge = 0
        self.shift = 10

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        self.setLayout(layout)

    def openImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.originalImage = cv2.imread(filename)
            self.maskImage = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.image_to_show = self.originalImage[:self.label_width,:self.label_height,:]
            self.image_to_show_mask = self.maskImage[:self.label_width,:self.label_height]
            self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
        
    def drawMask(self, begin, end):
        if self.originalImage is not None:
            x_start, y_start = begin.x(), begin.y()
            x_end, y_end = end.x(), end.y()
            x1, x2 = min(x_start, x_end), max(x_start, x_end)
            y1, y2 = min(y_start, y_end), max(y_start, y_end)

            y1 += self.bottom_edge
            y2 += self.bottom_edge

            x1 += self.left_edge
            x2 += self.left_edge
            #self.maskImage[y1+self.top_edge:y2+self.top_edge, x1+self.left_edge:x2+self.top_edge] = 255
            self.image_to_show_mask[y1:y2,x1:x2] =255
            # self.originalImage[self.bottom_edge:self.top_edge,self.left_edge:self.right_edge,:] = self.image_to_show
            # self.maskImage[self.bottom_edge:self.top_edge,self.left_edge:self.right_edge] = self.image_to_show_mask#[self.top_edge:self.bottom_edge,self.left_edge:self.right_edge]

            self.updateDisplay()

    def updateDisplay(self):
        if self.originalImage is not None:
            #imageToShow = cv2.cvtColor(self.originalImage, cv2.COLOR_BGR2RGB)
            height, width, _ = self.image_to_show.shape
            bytesPerLine = 3 * width
            #qImage = QImage(imageToShow.data, width, height, bytesPerLine, QImage.Format_RGB888)

            if self.maskImage is not None:
                mask = cv2.cvtColor(self.maskImage, cv2.COLOR_GRAY2BGR)
                coloredMask = np.zeros_like(mask, dtype=np.uint8)
                coloredMask[self.maskImage > 0] = [0, 0, 255]  
                self.originalImage = cv2.addWeighted(self.originalImage, 1, coloredMask, 0.4, 0)
                cv2.imshow("szohi",self.originalImage)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                #qImage = QImage(imageToShow.data, width, height, bytesPerLine, QImage.Format_RGB888)

            self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])

    def show_image(self, image_slice):
        piximage = self.convert_cv_qt(image_slice)
        #self.imageLabel.resize(self.label_height, self.label_width)
        self.imageLabel.setPixmap(piximage)
    
    def right_button_action(self):
        if self.originalImage is not None:
            if self.top_edge + self.shift <= self.originalImage.shape[1]:
                self.top_edge += self.shift
                self.bottom_edge += self.shift
                self.image_to_show = self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:]
                self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
                #self.updateDisplay()

    def left_button_action(self):
        if self.originalImage is not None:
            if self.bottom_edge - self.shift >= 0:
               self.top_edge -= self.shift
               self.bottom_edge -= self.shift
               self.image_to_show = self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:]
               self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
               #self.updateDisplay()
    def down_button_action(self):
        if self.originalImage is not None:
            if self.right_edge + self.shift <= self.originalImage.shape[0]:
               self.right_edge += self.shift
               self.left_edge += self.shift
               self.image_to_show = self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:]
               self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
               #self.updateDisplay()

    def up_button_action(self):
        if self.originalImage is not None:
            if self.left_edge - self.shift >= 0:
               self.right_edge -= self.shift
               self.left_edge -= self.shift
               self.image_to_show = self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:]
               self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
               #self.updateDisplay()

    def convert_cv_qt(self,cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.label_width, self.label_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def saveMaskAsPng(self):
        if self.maskImage is not None:
            Image.fromarray(self.maskImage).save("mask.png")
            print("Mask saved as mask.png")


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Image Viewer with Masking")
       
        self.window_width = 800
        self.window_height = 800

        self.imageWidget = ImageWidget()
        
        self.arrow_buttons_widget = QWidget()
        self.arrow_buttons = ArrowButtonLayout()
        self.arrow_buttons.up_button.clicked.connect(self.imageWidget.up_button_action)
        self.arrow_buttons.down_button.clicked.connect(self.imageWidget.down_button_action)
        self.arrow_buttons.right_button.clicked.connect(self.imageWidget.right_button_action)
        self.arrow_buttons.left_button.clicked.connect(self.imageWidget.left_button_action)
        self.arrow_buttons_widget.setLayout(self.arrow_buttons)
        #self.arrow_buttons_widget.resize(100,100)


        open_button = QPushButton("Open Image")
        open_button.clicked.connect(self.imageWidget.openImage)
        saveButton = QPushButton('Save Mask')
        saveButton.clicked.connect(self.imageWidget.saveMaskAsPng)

        layout = QVBoxLayout()
        layout.addWidget(self.imageWidget)
        button_layout = QHBoxLayout()
        button_layout.addWidget(open_button)
        button_layout.addWidget(saveButton)
        #layout.addLayout(button_layout)
        self.button_widget = QWidget()
        self.button_widget.setLayout(button_layout)
        

        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)
        #main_layout.addWidget(arrow_buttons_widget)
        #arrow_buttons_widget.show()
    

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    mainWindow = ImageViewer()
    mainWindow.show()
    mainWindow.arrow_buttons_widget.show()
    mainWindow.button_widget.show()
    sys.exit(app.exec_())