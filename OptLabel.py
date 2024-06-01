import sys, os, cv2, numpy as np
from PIL import Image
import PyQt5.QtGui  as QtGui
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPixmap, QPainter, QColor, QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout,QHBoxLayout, QPushButton, QSlider,QFileDialog, QLabel, QComboBox, QMessageBox, QListWidgetItem, QListWidget, QCheckBox, QGridLayout, QSpacerItem, QSizePolicy

class Menu(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('OptiLabel - menu')
        self.setGeometry(100, 100, 700, 500)
        self.selected_paths = []
        self.selected_checkbox = None
        self.light_mode = True  # Pôvodne je aplikácia v svetlom režime

        self.open_image_viewer_button = QPushButton("Open Image Viewer")
        self.open_image_viewer_button.clicked.connect(self.openImageViewer)

        self.load_images_button = QPushButton("Load Images")
        self.load_images_button.clicked.connect(self.load_images)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.item_clicked)

        self.checkboxes = []

        self.light_dark_button = QPushButton(
            "Switch to Dark Mode")  # Tlačidlo na prepínanie medzi svetlým a tmavým režimom
        self.light_dark_button.clicked.connect(self.toggle_mode)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.open_image_viewer_button)
        main_layout.addWidget(self.load_images_button)
        main_layout.addWidget(self.list_widget)
        main_layout.addWidget(self.light_dark_button)  # Pridanie tlačidla na prepínanie režimov

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def toggle_mode(self):
        if self.light_mode:
            self.setStyleSheet("background-color: #333; color: white")  # Nastavenie tmavého režimu
            self.light_dark_button.setText("Switch to Light Mode")
            self.light_mode = False
        else:
            self.setStyleSheet("")  # Nastavenie svetlého režimu
            self.light_dark_button.setText("Switch to Dark Mode")
            self.light_mode = True

    def load_images(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Obrázky (*.png *.jpg *.jpeg *.bmp *.gif *.tif)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()

            for path in selected_files:
                if self.check_duplicate_image(path):
                    return

                file_name = os.path.basename(path)
                self.selected_paths.append(path)

                image_label = QLabel()
                name_label = QLabel(file_name)

                pixmap = QPixmap(path)
                desired_size = pixmap.scaledToWidth(200)
                image_label.setPixmap(desired_size)

                checkbox = QCheckBox("Check")
                checkbox.stateChanged.connect(self.checkbox_state_changed)

                # Check for existing masks and display status
                mask_status_label = QLabel()
                self.update_mask_status_label(mask_status_label, path)

                item_widget = QWidget()
                item_layout = QVBoxLayout(item_widget)
                item_layout.addWidget(image_label)
                item_layout.addWidget(name_label)
                item_layout.addWidget(checkbox)
                item_layout.addWidget(mask_status_label)  # Add the status label

                item = QListWidgetItem()
                item.setSizeHint(QSize(200, 250))  # Adjust size hint to accommodate status label
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, item_widget)

                self.checkboxes.append(checkbox)
                self.update_all_mask_statuses()

    def update_mask_status_label(self, label, image_path):
        # Check if the masks exist and update the label accordingly
        base_path = os.path.dirname(image_path)
        file_name = os.path.splitext(os.path.basename(image_path))[0]

        vessel_mask_path = os.path.join(base_path, "VesselMasks", file_name + "_V.png")
        macula_mask_path = os.path.join(base_path, "Macula", file_name + "_M.png")
        optical_mask_path = os.path.join(base_path, "Optical", file_name + "_O.png")

        status_text = []
        if os.path.exists(vessel_mask_path):
            status_text.append("V")
        if os.path.exists(macula_mask_path):
            status_text.append("M")
        if os.path.exists(optical_mask_path):
            status_text.append("O")

        if status_text:
            label.setText("Masks: " + ", ".join(status_text))
        else:
            label.setText("No masks")

    def check_duplicate_image(self, path):
        if path in self.selected_paths:
            QMessageBox.warning(self, "Upozornenie", "Obrázok " + os.path.basename(path) + " sa už v liste nachádza")
            return True

    def checkbox_state_changed(self):
        if self.selected_checkbox:
            self.selected_checkbox.setChecked(False)

        sender_checkbox = self.sender()

        if sender_checkbox.isChecked():
            self.selected_checkbox = sender_checkbox
        else:
            self.selected_checkbox = None

    def item_clicked(self, item):
        checkbox = self.list_widget.itemWidget(item).findChild(QCheckBox)

        if checkbox.isChecked():
            checkbox.setChecked(False)
        else:
            checkbox.setChecked(True)

    def openImageViewer(self):
        if self.selected_checkbox:
            index = self.checkboxes.index(self.selected_checkbox)
            selected_path = self.selected_paths[index]
            image_viewer = ImageViewer(self, selected_path)
            image_viewer.show()

    def saveMaskAsPng(self):
        if self.imageLabel.currentMask == "Vessel network":
            vessel_folder = os.path.join(self.current_path, "VesselMasks")
            if not os.path.exists(vessel_folder):
                os.makedirs(vessel_folder)
            image_path = os.path.join(vessel_folder, self.file_name + "_" + "V.png")
            Image.fromarray(self.vesselMask).save(image_path)

        elif self.imageLabel.currentMask == "Macula":
            macula_folder = os.path.join(self.current_path, "Macula")
            if not os.path.exists(macula_folder):
                os.makedirs(macula_folder)
            image_path = os.path.join(macula_folder, self.file_name + "_" + "M.png")
            Image.fromarray(self.maculaMask).save(image_path)

        elif self.imageLabel.currentMask == "Optical disk":
            optical_folder = os.path.join(self.current_path, "Optical")
            if not os.path.exists(optical_folder):
                os.makedirs(optical_folder)
            image_path = os.path.join(optical_folder, self.file_name + "_" + "O.png")
            Image.fromarray(self.diskMask).save(image_path)

        # After saving, update the mask status for all images
        self.update_all_mask_statuses()

    def update_all_mask_statuses(self):
        # Iterate through all items in the list widget and update their mask status labels
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_widget = self.list_widget.itemWidget(item)
            image_path = self.selected_paths[i]
            mask_status_label = item_widget.findChildren(QLabel)[
                -1]  # Assuming the status label is the last QLabel added
            self.update_mask_status_label(mask_status_label, image_path)

class ImageViewer(QMainWindow):
    def __init__(self, parent=None, file=None):
        super().__init__(parent)
        self.file = file
        self.setWindowTitle('OptiLabel')
        self.setGeometry(100, 100, 700, 500)

        self.imageWidget = ImageWidget(self.file)

        self.arrow_buttons_layout = ArrowButtonLayout()

        self.top_buttons_layout = QHBoxLayout()
        save_button = QPushButton('Save Mask')
        save_button.clicked.connect(self.imageWidget.saveMaskAsPng)
        load_button = QPushButton('Load Mask')
        load_button.clicked.connect(self.imageWidget.loadMask)
        self.top_buttons_layout.addWidget(save_button)
        self.top_buttons_layout.addWidget(load_button)

        self.mode_buttons_layout = QVBoxLayout()
        rect_button = QPushButton("Draw Rectangle")
        rect_button.clicked.connect(self.imageWidget.imageLabel.setRectangle)
        circ_button = QPushButton('Draw Circle')
        circ_button.clicked.connect(self.imageWidget.imageLabel.setCircle)
        rubber_button = QPushButton('Rubber')
        rubber_button.clicked.connect(self.imageWidget.imageLabel.setRubber)
        deleteMaskButton = QPushButton("Delete current mask")
        deleteMaskButton.clicked.connect(self.imageWidget.removeCurrentMask)
        Alfa = QLabel("Oppacity")
        

        self.mode_buttons_layout.addWidget(rect_button)
        self.mode_buttons_layout.addWidget(circ_button)
        self.mode_buttons_layout.addWidget(rubber_button)
        self.mode_buttons_layout.addWidget(deleteMaskButton)
        self.mode_buttons_layout.addWidget(self.imageWidget.imageLabel.dropdown)
        self.mode_buttons_layout.addWidget(self.imageWidget.imageLabel.masks)
        self.mode_buttons_layout.addWidget(Alfa)
        self.mode_buttons_layout.addWidget(self.imageWidget.sliderAlfa)
       

        screenAndControl = QHBoxLayout()
        screenAndControl.addWidget(self.imageWidget)
        screenAndControl.addLayout(self.mode_buttons_layout)


        main_layout = QVBoxLayout()
        main_layout.addLayout(self.top_buttons_layout)
        main_layout.addLayout(screenAndControl)
        #main_layout.addLayout(self.arrow_buttons_layout)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def update_icons(self, light_mode):
        # Aktualizácia ikoniek tlačidiel pri zmene režimu
        self.arrow_buttons_layout.update_icons(light_mode)
        self.closed.emit()


class ArrowButtonLayout(QVBoxLayout):
    def __init__(self, parent=None, light_mode=True):
        super().__init__(parent)
        self.light_mode = light_mode  # Uloženie informácie o aktuálnom režime
        self.create_buttons()  # Vytvorenie tlačidiel s ikonami

    def create_buttons(self):
        # Inicializácia cesty k ikonám podľa aktuálneho režimu
        up_icon_path = 'icons/up_light.png' if self.light_mode else 'icons/up_dark.png'
        left_icon_path = 'icons/left_light.png' if self.light_mode else 'icons/left_dark.png'
        right_icon_path = 'icons/right_light.png' if self.light_mode else 'icons/right_dark.png'
        down_icon_path = 'icons/down_light.png' if self.light_mode else 'icons/down_dark.png'

        grid_layout = QGridLayout()

        # Vytvorenie tlačidiel s príslušnými ikonami
        self.up_button = QPushButton()
        self.up_button.setIcon(QIcon(up_icon_path))
        self.up_button.setFixedSize(50, 50)
        grid_layout.addWidget(self.up_button, 0, 1)

        self.left_button = QPushButton()
        self.left_button.setIcon(QIcon(left_icon_path))
        self.left_button.setFixedSize(50, 50)
        grid_layout.addWidget(self.left_button, 1, 0)

        self.right_button = QPushButton()
        self.right_button.setIcon(QIcon(right_icon_path))
        self.right_button.setFixedSize(50, 50)
        grid_layout.addWidget(self.right_button, 1, 2)

        self.down_button = QPushButton()
        self.down_button.setIcon(QIcon(down_icon_path))
        self.down_button.setFixedSize(50, 50)
        grid_layout.addWidget(self.down_button, 2, 1)

        self.addLayout(grid_layout)

    def update_icons(self, light_mode):
        self.light_mode = light_mode
        # Aktualizácia ikoniek tlačidiel pri zmene režimu
        self.up_button.setIcon(QIcon('icons/up_light.png' if self.light_mode else 'icons/up_dark.png'))
        self.left_button.setIcon(QIcon('icons/left_light.png' if self.light_mode else 'icons/left_dark.png'))
        self.right_button.setIcon(QIcon('icons/right_light.png' if self.light_mode else 'icons/right_dark.png'))
        self.down_button.setIcon(QIcon('icons/down_light.png' if self.light_mode else 'icons/down_dark.png'))

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

    def __init__(self, fileName=None):
        super().__init__()
        self.imageLabel = PaintableLabel(self)
        self.imageLabel.finishedDrawingRect.connect(self.drawMaskRect)
        self.imageLabel.finishedDrawingCirc.connect(self.drawMaskCirc)
        self.imageLabel.finishedRubb.connect(self.removeMaskRubb)


        self.fileName = fileName

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
        self.shift = 100

        self.vsselMask = None
        self.diskMask = None
        self.maculaMask = None
        
        self.current_path = None
        self.file_name = None #"C:/Users/novypouzivatel/Desktop/skola/TimProjekt/data"

        self.startX = 0
        self.startY = 0

        self.fix_width = 1500
        self.fix_height= 800

        self.zoom_level = 1.0

        self.sliderVer = QSlider(Qt.Horizontal)
        self.sliderHor = QSlider(Qt.Vertical)

        layout = QVBoxLayout()
        layout.addWidget(self.imageLabel)
        layout.addWidget(self.sliderVer)

        alloverLayout = QHBoxLayout()
        alloverLayout.addWidget(self.sliderHor)

        alloverLayout.addLayout(layout)

        

        self.sliderVer.valueChanged.connect(self.updateDisplay)
        self.sliderHor.valueChanged.connect(self.updateDisplay)

 
        self.sliderAlfa = QSlider(Qt.Horizontal) 
        self.sliderAlfa.setMinimum(0)
        self.sliderAlfa.setMaximum(100)  
        self.sliderAlfa.setValue(50)
        self.sliderAlfa.valueChanged.connect(self.updateDisplay)
        
        
        self.setLayout(alloverLayout)

        self.openImage()
       


    def openImage(self):
        if self.fileName:
            self.originalImage = cv2.imread(self.fileName)

            current_path, file_with_extension = os.path.split(self.fileName)

            file_name, file_extension = os.path.splitext(file_with_extension)

            self.current_path = current_path 

            self.file_name = file_name 

            self.maskImage = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.vsselMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.diskMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            self.maculaMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
            #self.image_to_show_mask = self.maskImage[:self.label_width,:self.label_height]
            h, w, ch = self.originalImage.shape
            self.label_height = h
            self.label_width = w
            self.sliderHor.setMinimum(0)
            self.sliderHor.setMaximum(h-self.fix_height)  
            self.sliderHor.setValue(0)
            self.sliderVer.setMinimum(0)
            self.sliderVer.setMaximum(w-self.fix_width)  
            self.sliderVer.setValue(0)
            self.imageLabel.setFixedSize(self.fix_width ,self.fix_height)
            self.updateDisplay()
          
        
     


    def drawMaskCirc(self, center,radius):
        if self.originalImage is not None:
            x_center, y_center = center.x()+self.startX, center.y()+self.startY
           

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
            x_center, y_center = center.x()+self.startX, center.y()+self.startY
           

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
            x_start, y_start = begin.x()+self.startX , begin.y()+ self.startY 
            x_end, y_end = end.x()+self.startX, end.y()+self.startY
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
            self.image_to_show = self.originalImage
            if self.maskImage is not None:
                coloredMask = np.zeros_like(self.originalImage, dtype=np.uint8)
                if self.imageLabel.currentMask == "Vessel network":
                    coloredMask[self.vsselMask > 0] = [255, 255, 0] 
                elif self.imageLabel.currentMask == "Macula":
                    coloredMask[self.maculaMask > 0] = [128, 0, 128] 
                elif self.imageLabel.currentMask == "Optical disk":
                    coloredMask[self.diskMask > 0] = [255, 0, 0]
                 
                alfa = self.sliderAlfa.value()/100
                self.image_to_show = cv2.addWeighted(self.originalImage, 1, coloredMask, alfa, 0)
            

      
            
            self.show_image()

    def show_image(self):
        
        self.startY = self.sliderHor.value()
        self.startX = self.sliderVer.value()

        height, width, _ =  self.image_to_show.shape

        zoomed_image = self.image_to_show[self.startY:self.startY+self.fix_height, self.startX:self.startX+self.fix_width]
        

        piximage = self.convert_cv_qt(zoomed_image)
        self.imageLabel.setPixmap(piximage)
        
    
    def right_button_action(self):
        if self.originalImage is not None:
            if self.startX + self.shift <= self.label_width:
                self.startX += self.shift
                self.updateDisplay()
                

    def left_button_action(self):
        if self.originalImage is not None:
            if self.startX - self.shift >= 0:
                self.startX -= self.shift
                self.updateDisplay()
               
    def down_button_action(self):
        if self.originalImage is not None:
            if self.startY + self.shift <= self.label_height:
                self.startY += self.shift
                self.updateDisplay()

    def up_button_action(self):
        if self.originalImage is not None:
            if self.startY - self.shift >= 0:
                self.startY -= self.shift
                self.updateDisplay()

    def convert_cv_qt(self,cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.fix_width, self.fix_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)
        

    def saveMaskAsPng(self):
        if self.imageLabel.currentMask == "Vessel network":
            vessel_folder = os.path.join(self.current_path, "VesselMasks")
            print(vessel_folder)
            if not os.path.exists(vessel_folder):
                os.makedirs(vessel_folder)
            image_path = os.path.join(vessel_folder, self.file_name + "_" + "V.png")

            Image.fromarray(self.vsselMask).save(image_path)
            
        elif self.imageLabel.currentMask == "Macula":
            macula_folder = os.path.join(self.current_path, "Macula")
            print(macula_folder)
            if not os.path.exists(macula_folder):
                os.makedirs(macula_folder)
            image_path = os.path.join(macula_folder, self.file_name + "_" + "M.png")

            Image.fromarray(self.maculaMask).save(image_path)

        elif self.imageLabel.currentMask == "Optical disk":
            optical_folder = os.path.join(self.current_path, "Optical")
            print(optical_folder)
            if not os.path.exists(optical_folder):
                os.makedirs(optical_folder)
            image_path = os.path.join(optical_folder, self.file_name + "_" + "O.png")

            Image.fromarray(self.diskMask).save(image_path)

      


    def loadMask(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png)")
        if filename:
            
            self.mask_image = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
            if self.mask_image is not None:
                if self.imageLabel.currentMask == "Vessel network":
                    self.vsselMask = self.mask_image
                elif self.imageLabel.currentMask == "Macula":
                    self.maculaMask = self.mask_image
                elif self.imageLabel.currentMask == "Optical disk":
                    self.diskMask = self.mask_image
                print("Mask loaded successfully.")
                self.updateDisplay()
            else:
                print("Failed to load mask.")
    
    def removeCurrentMask(self):
        reply = QMessageBox.question(None, 'Confirmation', 'Naozaj chces vymazat aktualnu masku?',
                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
                if self.imageLabel.currentMask == "Vessel network":
                    self.vsselMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
                elif self.imageLabel.currentMask == "Macula":
                    self.maculaMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)
                elif self.imageLabel.currentMask == "Optical disk":
                    self.diskMask = np.zeros(self.originalImage.shape[:2], dtype=np.uint8)

        self.updateDisplay()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Menu()
    window.show()
    sys.exit(app.exec_())