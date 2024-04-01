#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal

from controller.controller_base_tab import BaseControllerTab
from model.app import app_model


class VideoResultController(BaseControllerTab):
    video_map = {}
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)

    def init(self):
        self.tab_index = 2
        # 绑定配置文件中的相机与去显示的lable
        self.bind_label_and_timer("left", None, 0)  # 270)
        # self.bind_label_and_timer("middle_left", None, 270)
        # self.bind_label_and_timer("middle_right", None, 270)
        self.bind_label_and_timer("right", None, 270)
        self.bind_label_and_timer("stitch", self.view.label_video_result, 0)
        self.view.label_video_result.lable_click_signal.connect(self.lable_click_ctrl)

    def lable_click_ctrl(self, click_pos):
        # print("emit lable_click_ctrl:", click_pos)
        app_model.video_server.fisheye_ctrl(click_pos)
