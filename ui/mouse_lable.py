import sys
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt


class MyLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            print("Left mouse button pressed")

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            print("Left mouse button released")

    def mouseMoveEvent(self, event):
        print("Mouse moved: ({}, {})".format(event.x(), event.y()))
