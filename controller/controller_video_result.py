#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal

from controller.controller_base_tab import BaseControllerTab


class VideoResultController(BaseControllerTab):
    video_map = {}
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)

    def init(self):
        self.tab_index = 2
        # 绑定配置文件中的相机与去显示的lable
        self.bind_label_and_timer("stitch", self.view.label_video_result, 0)

