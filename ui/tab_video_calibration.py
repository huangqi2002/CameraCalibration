#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QSizePolicy

from ui.ui_base import BaseView
from ui.ui_tab_video_calibration import Ui_TabVideoCalibration


class TabVideoCalibration(BaseView, Ui_TabVideoCalibration):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.pushButton_img_left_middle.setVisible(False)
        self.pushButton_img_middle_right.setVisible(False)
        # 防止界面大小不可调节
        self.label_video_left.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label_video_middle.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label_video_right.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.pushButton_play_list = [self.pushButton_left_play, self.pushButton_middle_play, self.pushButton_right_play]
        self.position_type_text = ["左", "中", "右"]
        for pushButton_play, type_text in zip(self.pushButton_play_list, self.position_type_text):
            pushButton_play.setStyleSheet("QPushButton{ background-color: #444; color: #999; }"
                                          "QPushButton:pressed { background-color: #666; }"
                                          "QPushButton:disabled  { background-color: #FFF; color: #000; }")

    def set_video_left(self, video_data):
        self.label_video_left.setPixmap(video_data)

    def set_video_left_visible(self, visible):
        self.label_video_left.setVisible(visible)

    def get_video_left_size(self):
        size = self.label_video_left.size()
        return size.width(), size.height()

    def set_video_middle(self, video_data):
        self.label_video_middle.setPixmap(video_data)

    def set_video_middle_visible(self, visible):
        self.label_video_middle.setVisible(visible)

    def set_video_right(self, video_data):
        self.label_video_right.setPixmap(video_data)

    def set_video_right_visible(self, visible):
        self.label_video_right.setVisible(visible)

    def set_image_left(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_left)
        self.label_img_left.setPixmap(pixmap)

    def set_image_middle(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_middle)
        self.label_img_middle.setPixmap(pixmap)

    def set_image_right(self, img_path):
        pixmap = self.scale_pixmap_in_label(img_path, self.label_img_right)
        self.label_img_right.setPixmap(pixmap)

    def set_layout_middle_visible(self, visible):
        self.set_video_middle_visible(visible)
        self.label_img_middle.setVisible(visible)
        self.label_img_spacer.setVisible(visible)

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
        pixmap.setDevicePixelRatio(proportion)
        return pixmap

    def set_position_type_button_enable(self, index):
        for i in range(len(self.pushButton_play_list)):
            if i == index:
                self.pushButton_play_list[i].setEnabled(False)
            else:
                self.pushButton_play_list[i].setEnabled(True)

    def set_start_button_enable(self, enable):
        self.pushButton_start.setEnabled(enable)
        # self.pushButton_screenshot.setVisible(enable)