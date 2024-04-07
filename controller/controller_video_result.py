#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt5.QtCore import pyqtSignal, QTimer

from controller.controller_base_tab import BaseControllerTab
from model.app import app_model
from server.web.web_server import server


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

        self.view.depth_horizontalSlider.setMinimum(10)
        self.view.depth_horizontalSlider.setMaximum(100)
        self.view.depth_horizontalSlider.setSingleStep(1)
        self.view.depth_horizontalSlider.setValue(10)  # 设置初始值
        self.view.depth_horizontalSlider.valueChanged.connect(self.slider_value_changed)  # 连接值变化的信号到槽函数
        self.view.depth_label.setText("Current Value: {}".format(self.view.depth_horizontalSlider.value() / 10))  #
        # 显示当前值的标签
        self.view.changestate_pushButton.clicked.connect(self.button_clicked)  # 连接按钮点击事件到槽函数
        # 定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.depth_set)


    def on_tab_changed(self, index):
        if index == 2:
            try:
                external_cfg_info = server.get_external_cfg()
                if not external_cfg_info:
                    self.show_message_signal.emit(False, "获取设备外参文件失败")
                    return False
                external_cfg = external_cfg_info.get("body")
                if not external_cfg:
                    self.show_message_signal.emit(False, "获取设备外参文件失败:body")
                    return False
                app_model.video_server.set_external(external_cfg)
            except Exception as e:
                print(f"{e}")
        super().on_tab_changed(index)  # 调用父类的函数


    def lable_click_ctrl(self, click_pos):
        # print("emit lable_click_ctrl:", click_pos)
        app_model.video_server.fisheye_ctrl(click_pos)

    def slider_value_changed(self, value):
        self.view.depth_label.setText("Current Value: {}".format(self.view.depth_horizontalSlider.value() / 10))  # 更新 QLabel 的文本
        self.timer.start(100)  # 设置定时器间隔为100毫秒

    def depth_set(self):
        app_model.video_server.fisheye_depth_set(self.view.depth_horizontalSlider.value() / 10)

    def button_clicked(self):
        self.view.depth_horizontalSlider.setValue(10)
