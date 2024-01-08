#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt

from ui.custom.label_double_click import DoubleClickLabel


class DoubleClickWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        layout = QtWidgets.QHBoxLayout(self)

        self.label = DoubleClickLabel()
        self.label.mouseDoubleClickSignal.connect(self.dialog_double_client)

        layout.addWidget(self.label)

        self.setWindowModality(Qt.ApplicationModal)

    def set_img(self, img):
        print("child dialog", img)
        self.label.setPixmap(img)
        self.label.setScaledContents(True)
        self.showFullScreen()

    def dialog_double_client(self):
        self.close()
