import sys
from PyQt5.QtWidgets import QApplication, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal


class ClickableLabel(QLabel):
    lable_click_signal = pyqtSignal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setText("Click me!")
        self.setAlignment(Qt.AlignCenter)  # 设置文本居中

    def mousePressEvent(self, event):
        width_ratio = event.pos().x() / self.width()  # 计算鼠标点击位置相对于窗口宽度的比例
        height_ratio = event.pos().y() / self.height()  # 计算鼠标点击位置相对于窗口高度的比例
        x = int(width_ratio * 3)  # 将比例转换为行号（0, 1, 2）
        y = int(height_ratio * 3)  # 将比例转换为列号（0, 1, 2）
        position = y * 3 + x  # 计算位置对应的值
        # print("emit Clicked on position:", position)
        self.lable_click_signal.emit(position)

    def wheelEvent(self, event):
        delta = event.angleDelta()
        print('delta=', delta)
        if int(delta.y()) > 0:
            position = 9
        else:
            position = 10
        self.lable_click_signal.emit(position)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    label = ClickableLabel()
    label.show()
    sys.exit(app.exec_())
