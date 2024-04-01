#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from PyQt5 import QtWidgets
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QFileDialog, QSizePolicy

from ui.ui_base import BaseView
from ui.ui_tab_internal_calibration import Ui_TabInternalCalibration


class TabInternalCalibration(BaseView, Ui_TabInternalCalibration):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.set_choose_file_visible(False)

        self.screen_lable_list = [self.label_img_left_fg_1, self.label_img_left_fg_2,
                                  self.label_img_middle_left_fg_1, self.label_img_middle_left_fg_2,
                                  self.label_img_middle_right_fg_1, self.label_img_middle_right_fg_2,
                                  self.label_img_right_fg_1, self.label_img_right_fg_2]
        for i in range(len(self.screen_lable_list)):
            if i % 2 == 1:
                self.screen_lable_list[i].hide()

        self.pushbotton_text = ["截图（左）", "截图（左）",
                                "截图（最左）", "截图（最左）",
                                "截图（最右）", "截图（最右）",
                                "截图（右）", "截图（右）", "标定"]

        self.pushButton_screenshot.setStyleSheet("QPushButton:pressed { background-color: #666; }"
                                                 "QPushButton:disabled { background-color: #444; color: #999; }")

        self.pushButton_start.setStyleSheet("QPushButton:pressed { background-color: #666; }"
                                            "QPushButton:disabled { background-color: #444; color: #999; }")
        self.pushButton_play_list = [self.pushButton_left_play, self.pushButton_midleft_play,
                                     self.pushButton_midright_play, self.pushButton_right_play]
        self.position_type_text = ["左", "最左", "最右", "右"]
        for pushButton_play, type_text in zip(self.pushButton_play_list, self.position_type_text):
            pushButton_play.setStyleSheet("QPushButton{ background-color: #444; color: #999; }"
                                          "QPushButton:pressed { background-color: #666; }"
                                          "QPushButton:disabled  { background-color: #FFF; color: #000; }")

            pushButton_play.setText(type_text)

        self.start_ok = False
        self.update()

    def set_choose_file_visible(self, visible=True):
        self.label.setVisible(visible)
        self.lineEdit_internal_file_path.setVisible(visible)
        self.pushButton_set_internal_file_path.setVisible(visible)

    def set_video_left(self, video_data):
        self.label_video_left.setPixmap(video_data)

    def get_video_left_size(self):
        size = self.label_video_left.size()
        return size.width(), size.height()

    def set_video_left_visible(self, visible):
        self.label_video_left.setVisible(visible)

    def set_video_middle(self, video_data):
        self.label_video_middle.setPixmap(video_data)

    def set_video_middle_visible(self, visible):
        self.label_video_middle.setVisible(visible)

    def set_video_right(self, video_data):
        # self.label_video_right.setScaledContents(True)
        self.label_video_right.setPixmap(video_data)

    def set_video_right_visible(self, visible):
        self.label_video_right.setVisible(visible)

    def set_video_fg(self, video_data):
        self.label_video_fg.setPixmap(video_data)

    def set_video_fg_visible(self, visible):
        self.label_video_fg.setVisible(visible)

    def set_choose_file_lineedit(self, msg):
        self.lineEdit_internal_file_path.setText(msg)

    def get_choose_file_lineedit(self):
        return self.lineEdit_internal_file_path.text()

    def on_choose_file(self):
        root_path = QFileDialog.getExistingDirectory(self, '选择数据文件夹', os.getcwd())
        if root_path == '':
            return None
        self.set_choose_file_lineedit(root_path)
        return root_path

    def set_image_left(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_left)
        self.label_img_left.setPixmap(pixmap)

    def set_image_middle(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_middle)
        self.label_img_middle.setPixmap(pixmap)

    def set_image_right(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_right)
        self.label_img_right.setPixmap(pixmap)

    def set_image_fg(self, screen_label_count, img_path):
        if screen_label_count == -1:
            for label in self.screen_lable_list:
                label.clear()
            return
        if not os.path.exists(img_path):
            return
        elif screen_label_count < -1 or screen_label_count > 7:
            print("label_count out of index\n")
            return
        label = self.screen_lable_list[screen_label_count]
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_right)
        label.setPixmap(pixmap)

    def set_screenshot_button_text(self, set_screenshot_button_text_count):
        self.pushButton_screenshot.setText(self.pushbotton_text[set_screenshot_button_text_count])

    def set_screenshot_button_enable(self, enable):
        self.pushButton_screenshot.setEnabled(enable)
        # self.pushButton_screenshot.setVisible(enable)

    def set_position_type_button_enable(self, index):
        for i in range(len(self.pushButton_play_list)):
            if i == index:
                self.pushButton_play_list[i].setEnabled(False)
            else:
                self.pushButton_play_list[i].setEnabled(True)
        # self.pushButton_screenshot.setVisible(enable)

    def set_start_button_enable(self, enable):
        self.start_ok = enable
        self.pushButton_start.setEnabled(enable)

    def set_layout_middle_visible(self, visible):
        self.set_video_middle_visible(visible)
        self.label_img_middle.setVisible(visible)
        self.label_img_spacer.setVisible(visible)

    def set_layout_fg(self, visible):
        self.hide_layout_widgets(self.horizontalLayout_fg, visible)
        self.pushButton_screenshot.setEnabled(visible)
        if visible:
            self.pushButton_start.setEnabled(self.start_ok)

    def set_layout_rx5(self, visible):
        self.hide_layout_widgets(self.horizontalLayout_rx5, visible)
        if visible:
            self.pushButton_start.setEnabled(True)

    def hide_layout_widgets(self, layout, visible):
        # 遍历布局内所有元素
        for i in range(layout.count()):
            item = layout.itemAt(i)
            # 如果是小部件（widget），隐藏它
            if isinstance(item, QtWidgets.QWidgetItem):
                widget = item.widget()
                if widget:
                    widget.setVisible(visible)
            elif isinstance(item, QtWidgets.QSpacerItem):
                self.set_spacer_visible(item, visible)
            # 如果是子布局（sub-layout），递归调用隐藏函数
            elif isinstance(item, QtWidgets.QLayoutItem):
                self.hide_layout_widgets(item.layout(), visible)

        for i in range(len(self.screen_lable_list)):
            if i % 2 == 1:
                self.screen_lable_list[i].hide()

    @staticmethod
    def set_spacer_visible(spacer, visible):
        # 设置Spacer 的大小，以达到显示/隐藏的效果
        if visible:
            spacer.changeSize(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        else:
            spacer.changeSize(0, 0, QSizePolicy.Fixed, QSizePolicy.Fixed)

    @staticmethod
    def scale_pixmap_in_label(img_path, label):
        if not img_path or not label:
            return None
        pixmap = QPixmap(img_path)
        proportion_h = pixmap.height() / label.height()
        proportion_w = pixmap.width() / label.width()
        if proportion_w > proportion_h:
            proportion = proportion_h
        else:
            proportion = proportion_w
        pixmap = pixmap.scaled(int(pixmap.width() / proportion), int(pixmap.height() / proportion))
        # pixmap.setDevicePixelRatio(proportion)
        return pixmap
