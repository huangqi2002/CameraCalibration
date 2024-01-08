#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys

import qdarkstyle
from PyQt5 import QtWidgets

from ui.mainwindow import MainWindow
from controller.controller_main import MainController
from qt_material import apply_stylesheet
from utils.m_global import m_connect_local

class QSSLoader:
    @staticmethod
    def read_qss_file(qss_file_name):
        with open(qss_file_name, 'r',  encoding='UTF-8') as file:
            return file.read()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    window = MainWindow()
    window.showMaximized()

    # setup stylesheet
    style_sheet = QSSLoader.read_qss_file("./ui/styles/dark.qss")
    window.setStyleSheet(style_sheet)

    controller = MainController(window)
    controller.show()

    sys.exit(app.exec_())

