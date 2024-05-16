from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,QGridLayout,QComboBox)
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
    finishedDrawingRect = pyqtSignal(QPoint, QPoint)
    finishedDrawingCirc = pyqtSignal(QPoint,int)
    finishedRubb = pyqtSignal(QPoint,int)

    updateScreen = pyqtSignal()

    
    
    def __init__(self, parent=None):
        super(PaintableLabel, self).__init__(parent)
        self.begin = QPoint()
        self.end = QPoint()
        self.drawing = False
        self.setMouseTracking(True)

        self.pos = None

        self.rectangle = True
        self.rubber = False
        self.circle = False

        self.radius = 1

        self.dropdown = QComboBox()
        values = [1, 3, 5, 7, 10, 15]
        self.dropdown.addItems([str(value) for value in values])
        self.dropdown.currentIndexChanged.connect(self.onIndexChanged)

        self.masks = QComboBox()
        values = ["Vessel network","Macula", "Optical disk"]
        self.masks.addItems([str(value) for value in values])
        self.masks.currentIndexChanged.connect(self.onIndexChangedMask)

        self.currentMask = "Vessel network"
        
    def onIndexChangedMask(self):
        self.currentMask = self.masks.currentText()
        self.updateScreen.emit()


    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if self.drawing and self.rectangle:
            painter.setPen(QColor(255, 0, 0, 128))  
            painter.drawRect(QRect(self.begin, self.end))
        
    
        if self.pos is not None and self.rubber or self.circle:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor("red"))
            painter.drawEllipse(self.pos.x() - (self.radius), self.pos.y() - (self.radius), self.radius*2,self.radius*2)
        


    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.begin = event.pos()
            self.end = event.pos()
            self.update()

    def mouseMoveEvent(self, event):

        adjusted_rect = self.rect().adjusted(0, 0, -self.radius, -self.radius)

        if adjusted_rect.contains(event.pos()):
            if event.buttons() & Qt.LeftButton:
                self.end = event.pos()

            if self.circle and self.drawing:
                    self.finishedDrawingCirc.emit(self.end,self.radius)

            if self.rubber and self.drawing:
                    self.finishedRubb.emit(self.end,self.radius)

        self.pos = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.update()
            if self.rectangle:
                self.finishedDrawingRect.emit(self.begin, self.end)
            
    def onIndexChanged(self):
        self.radius = int(self.dropdown.currentText())
    


    def setRubber(self):
        self.rubber = True
        self.rectangle = False
        self.circle = False

    def setCircle(self):
        self.rubber = False
        self.rectangle = False
        self.circle = True

    def setRectangle(self):
        self.rubber = False
        self.rectangle = True
        self.circle = False

        
class ImageWidget(QWidget):

    def __init__(self):
        super().__init__()
        self.imageLabel = PaintableLabel(self)
        self.imageLabel.finishedDrawingRect.connect(self.drawMaskRect)
        self.imageLabel.finishedDrawingCirc.connect(self.drawMaskCirc)
        self.imageLabel.finishedRubb.connect(self.removeMaskRubb)

        self.imageLabel.updateScreen.connect(self.updateDisplay)
        self.label_height = None
        self.label_width = None
        self.originalImage = None
        self.image_to_show = None
        
        self.maskImage = None

        self.left_edge = 0
        self.right_edge = self.label_width
        self.top_edge=self.label_height
        self.bottom_edge = 0
        self.shift = 10

        self.vsselMask = None
        self.diskMask = None
        self.maculaMask = None


        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        self.setLayout(layout)


    def openImage(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg)")
        if filename:
            self.originalImage = cv2.imread(filename)

            desired_width = 800
            desired_height = 600
            self.originalImage = cv2.resize(self.originalImage, (desired_width, desired_height))
            self.maskImage = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.image_to_show = self.originalImage[:self.label_width,:self.label_height,:]
            self.vsselMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.diskMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.maculaMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            #self.image_to_show_mask = self.maskImage[:self.label_width,:self.label_height]
            h, w, ch = self.originalImage.shape
            self.label_height = h
            self.label_width = w
            self.imageLabel.setFixedSize(w,h)
            self.show_image(self.originalImage[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])
        
     


    def drawMaskCirc(self, center,radius):
        if self.originalImage is not None:
            x_center, y_center = center.x(), center.y()
           

            for y in range(int(y_center - radius), int(y_center + radius) + 1):
                for x in range(int(x_center - radius), int(x_center + radius) + 1):
                    if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius ** 2:
                        
                        if self.imageLabel.currentMask == "Vessel network":
                            self.vsselMask[y, x] = 255
                        elif self.imageLabel.currentMask == "Macula":
                            self.maculaMask[y, x] = 255
                        elif self.imageLabel.currentMask == "Optical disk":
                            self.diskMask[y, x] = 255
        
            self.updateDisplay()
    
    def removeMaskRubb(self, center,radius):
        if self.originalImage is not None:
            x_center, y_center = center.x(), center.y()
           

            for y in range(int(y_center - radius), int(y_center + radius) + 1):
                for x in range(int(x_center - radius), int(x_center + radius) + 1):
                    if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius ** 2:
                        if self.imageLabel.currentMask == "Vessel network":
                            self.vsselMask[y, x] = 0
                        elif self.imageLabel.currentMask == "Macula":
                            self.maculaMask[y, x] = 0
                        elif self.imageLabel.currentMask == "Optical disk":
                            self.diskMask[y, x] = 0

        
            self.updateDisplay()
    
    def drawMaskRect(self, begin, end):
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
            self.maskImage[y1:y2,x1:x2] = 255
            if self.imageLabel.currentMask == "Vessel network":
                self.vsselMask[y1:y2,x1:x2] = 255
            elif self.imageLabel.currentMask == "Macula":
                self.maculaMask[y1:y2,x1:x2] = 255
            elif self.imageLabel.currentMask == "Optical disk":
                self.diskMask[y1:y2,x1:x2] = 255
            # self.originalImage[self.bottom_edge:self.top_edge,self.left_edge:self.right_edge,:] = self.image_to_show
            # self.maskImage[self.bottom_edge:self.top_edge,self.left_edge:self.right_edge] = self.image_to_show_mask#[self.top_edge:self.bottom_edge,self.left_edge:self.right_edge]

            self.updateDisplay()

    def updateDisplay(self):
        if self.originalImage is not None:

            if self.maskImage is not None:
                coloredMask = np.zeros_like(self.originalImage, dtype=np.uint8)
                if self.imageLabel.currentMask == "Vessel network":
                    coloredMask[self.vsselMask > 0] = [0, 0, 255] 
                elif self.imageLabel.currentMask == "Macula":
                    coloredMask[self.maculaMask > 0] = [0, 255, 0] 
                elif self.imageLabel.currentMask == "Optical disk":
                    coloredMask[self.diskMask > 0] = [255, 0, 0]
                 
                self.image_to_show = cv2.addWeighted(self.originalImage, 1, coloredMask, 0.7, 0)

            self.show_image(self.image_to_show[self.left_edge:self.right_edge,self.bottom_edge:self.top_edge,:])

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

    def loadMask(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png)")
        if filename:
            self.mask_image = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
            if self.mask_image is not None:
                self.maskImage = self.mask_image
                print("Mask loaded successfully.")
                self.updateDisplay()
            else:
                print("Failed to load mask.")


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
        loadButton = QPushButton('Load Mask')
        loadButton.clicked.connect(self.imageWidget.loadMask)
 

        layout = QVBoxLayout()
        layout.addWidget(self.imageWidget)
        button_layout = QHBoxLayout()
        button_layout.addWidget(open_button)
        button_layout.addWidget(saveButton)
        button_layout.addWidget(loadButton)
        #layout.addLayout(button_layout)
        self.button_widget = QWidget()
        self.button_widget.setLayout(button_layout)


        mode_layout = QVBoxLayout()
        rectButton = QPushButton("DrawRectangle")
        rectButton.clicked.connect(self.imageWidget.imageLabel.setRectangle)
        circButton = QPushButton('DrawCircle')
        circButton.clicked.connect(self.imageWidget.imageLabel.setCircle)
        rubberButton = QPushButton('Rubber')
        rubberButton.clicked.connect(self.imageWidget.imageLabel.setRubber)

        mode_layout.addWidget(rectButton)
        mode_layout.addWidget(circButton)
        mode_layout.addWidget(rubberButton)

        mode_layout.addWidget(self.imageWidget.imageLabel.dropdown)
        mode_layout.addWidget(self.imageWidget.imageLabel.masks)

        main_layout = QHBoxLayout()
        main_layout.addLayout(layout)
        main_layout.addLayout(mode_layout)
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
