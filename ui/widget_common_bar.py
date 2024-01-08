#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ui.ui_base import BaseView
from ui.ui_widget_common_bar import Ui_WidgetCommonBar


class WidgetCommonBar(BaseView, Ui_WidgetCommonBar):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def device_combo_box_add_items(self, items):
        self.comboBox_choise_device_type.addItems(items)

    def set_log_btn_text(self, msg):
        self.pushButton_show_log_view.setText(msg)

    def set_connect_device_btn_text(self, msg):
        self.pushButton_connect_device.setText(msg)

    def set_reboot_device_btn_text(self, msg):
        self.pushButton_reboot_device.setText(msg)

    def set_ok_ng_msg(self, msg):
        self.label_time_status.setText(msg)

    def set_ok_ng_status(self, status=True):
        if status:
            self.label_time_status.setStyleSheet("background-color:green;")
        else:
            self.label_time_status.setStyleSheet("background-color:red;")

    def get_device_ip(self):
        return self.lineEdit_device_ip.text()
