#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import pyqtSignal


class DoubleClickLabel(QtWidgets.QLabel):
    mouseDoubleClickSignal = pyqtSignal(object)
    resizeSignal = pyqtSignal(object)

    def __init__(self, *__args):
        super().__init__(*__args)

    def mouseDoubleClickEvent(self, event: QtGui.QMouseEvent):
        self.mouseDoubleClickSignal.emit(self)

    def resizeEvent(self, event: QtGui.QResizeEvent):
        self.resizeSignal.emit(self)
