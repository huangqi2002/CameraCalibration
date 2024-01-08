#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QProgressDialog, QMessageBox


class BaseView(QWidget):
    progressDialog = None

    def show_message_dialog(self, title, msg):
        QMessageBox.warning(self, title, msg)

    def show_loading(self, title="", msg="", btn=None, start_value=0, process_value=0):
        self.progressDialog = QProgressDialog(msg, btn, start_value, process_value)
        # 禁用右上角所有按钮，但最小化按钮可用
        self.progressDialog.setWindowFlags(Qt.CustomizeWindowHint | Qt.WindowMinimizeButtonHint)
        # 对本程序模态
        self.progressDialog.setWindowModality(Qt.ApplicationModal)
        self.progressDialog.setWindowTitle(title)
        self.progressDialog.show()

    def update_loading(self, msg="", process_value=0):
        if not self.progressDialog:
            return
        self.progressDialog.setLabelText(msg)
        if process_value != 0:
            self.progressDialog.setValue(process_value)

    def close_loading(self):
        if not self.progressDialog:
            return
        self.progressDialog.close()
        self.progressDialog = None
