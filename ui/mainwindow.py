#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtWidgets import QTabWidget, QDockWidget

from model.app import app_model
from ui.ui_base import BaseView
from ui.ui_mainwindow import Ui_MainWindow
from ui.widget_common_bar import WidgetCommonBar
from ui.tab_internal_calibration import TabInternalCalibration
from ui.tab_video_calibration import TabVideoCalibration
from ui.tab_video_result import TabVideoResult
from ui.widget_log_view import WidgetLogView

from utils.run_para import m_global


class MainWindow(QtWidgets.QMainWindow, BaseView, Ui_MainWindow):
    signal_tab_changed = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.setWindowTitle(f"{self.windowTitle}({app_model.version_app})")

        self.widget_common_bar = WidgetCommonBar()
        self.widget_common_bar.lineEdit_device_ip.setText("192.168.1.100")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.12.235")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.111.10")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.12.131")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.113.101")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.12.110")
        # self.widget_common_bar.lineEdit_device_ip.setText("192.168.113.102")

        self.verticalLayout.addWidget(self.widget_common_bar)

        self.tab_internal_calibration = TabInternalCalibration()
        self.tab_video_calibration = TabVideoCalibration()
        self.tab_video_result = TabVideoResult()
        self.main_tab_widget = QTabWidget(self)
        self.main_tab_widget.addTab(self.tab_internal_calibration, self.tr("内参标定"))
        self.main_tab_widget.addTab(self.tab_video_calibration, self.tr("标定拼接"))
        self.main_tab_widget.addTab(self.tab_video_result, self.tr("内参拼接结果"))
        self.main_tab_widget.currentChanged.connect(self.signal_tab_changed)
        self.verticalLayout.addWidget(self.main_tab_widget, stretch=1)


        self.widget_log_view = WidgetLogView()
        self.dock_log_view = QDockWidget(self.tr("日志"), self)
        self.dock_log_view.setWidget(self.widget_log_view)
        self.dock_log_view.setFeatures(QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable |
                                       QDockWidget.DockWidgetFloatable)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_log_view)

        self.init_view()

    def init_view(self):
        # 默认关闭日志显示
        self.dock_log_view.close()

    def on_show_log_view(self, is_show):
        if is_show:
            self.dock_log_view.show()
        else:
            self.dock_log_view.close()
        app_model.show_log_view = is_show

    def switch_tab_index(self, index):
        self.main_tab_widget.setCurrentIndex(index)

    def switch_type_index(self, index):
        self.widget_common_bar.comboBox_choise_device_type.setCurrentIndex(index)

    def get_tab_index(self):
        return self.main_tab_widget.currentIndex()

    def show_msg_dialog(self):
        self.show_message_dialog("测试", "测试内容")
