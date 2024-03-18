#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from ui.ui_base import BaseView
from ui.ui_tab_video_result import Ui_TabVideoResult


class TabVideoResult(BaseView, Ui_TabVideoResult):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

    def set_video_result(self, video_data):
        self.label_video_result.setPixmap(video_data)