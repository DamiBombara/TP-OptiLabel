# This Python file uses the following encoding: utf-8
import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QFileDialog, QLabel, QMessageBox
from PySide6.QtCore import QSize
from PySide6.QtGui import QPixmap, QIcon

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.selected_paths = []

        self.ui.load_img_button.clicked.connect(self.load_images)

    def load_images(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setNameFilter("Obrázky (*.png *.jpg *.jpeg *.bmp *.gif *.tif)")

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()

            for path in selected_files:
                if(self.check_duplicate_image(path)):
                    return

                self.selected_paths.append(path)
                image_label = QLabel()
                pixmap = QPixmap(path)

                desired_size = pixmap.scaledToWidth(200)
                image_label.setPixmap(desired_size)

                item = QListWidgetItem()
                item.setSizeHint(QSize(100, 200))
                self.ui.listWidget.addItem(item)
                self.ui.listWidget.setItemWidget(item, image_label)


    def check_duplicate_image(self, path):
        if path in self.selected_paths:
            QMessageBox.warning(self, "Upozornenie", "Tento obrázok sa už v liste nachádza")
            return True

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
