import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal

class ScreenClickableLabel(QLabel):
    lable_click_signal = pyqtSignal(float, float)
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        # print(event.pos().x() / self.width(), event.pos().y() / self.height())
        self.lable_click_signal.emit(event.pos().x() / self.width(), event.pos().y() / self.height())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    label = ScreenClickableLabel()
    label.show()
    sys.exit(app.exec_())
