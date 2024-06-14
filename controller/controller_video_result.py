#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

import cv2
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage

from controller.controller_base_tab import BaseControllerTab
from model.app import app_model
from server.web.web_server import server
from utils.run_para import m_global


class VideoResultController(BaseControllerTab):
    video_map = {}
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)

    def init(self):
        self.tab_index = 1
        # 绑定配置文件中的相机与去显示的lable
        self.bind_label_and_timer("left", None, 0)  # 270)
        self.bind_label_and_timer("middle_left", None, 270)
        self.bind_label_and_timer("middle_right", None, 270)
        self.bind_label_and_timer("right", None, 0)
        self.bind_label_and_timer("stitch", self.view.label_video_result, 0)
        # self.view.label_video_result.lable_click_signal.connect(self.lable_click_ctrl)

        self.view.depth_horizontalSlider.setMinimum(1)
        self.view.depth_horizontalSlider.setMaximum(1000)
        self.view.depth_horizontalSlider.setSingleStep(1)
        self.view.depth_horizontalSlider.setValue(100)  # 设置初始值
        self.view.depth_horizontalSlider.valueChanged.connect(self.slider_value_changed)  # 连接值变化的信号到槽函数
        self.view.depth_label.setText("Current Value: {}".format(self.view.depth_horizontalSlider.value() / 100))  #
        self.view.changestate_pushButton.setVisible(False)
        self.view.depth_horizontalSlider.setVisible(False)
        self.view.depth_label.setVisible(False)
        # self.view.pushButton_begin.setVisible(True)

        # 显示当前值的标签
        self.view.changestate_pushButton.clicked.connect(self.button_clicked)  # 连接按钮点击事件到槽函数
        # 定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.depth_set)

        # 开始预览
        self.view.pushButton_begin.clicked.connect(self.on_begin)


    # def on_tab_changed(self, index):
    #     if index == 2:
    #         try:
    #             external_cfg_info = server.get_external_cfg()
    #             if not external_cfg_info:
    #                 self.show_message_signal.emit(False, "获取设备外参文件失败")
    #                 return False
    #             external_cfg = external_cfg_info.get("body")
    #             if not external_cfg:
    #                 self.show_message_signal.emit(False, "获取设备外参文件失败:body")
    #                 return False
    #             app_model.video_server.set_external(external_cfg)
    #         except Exception as e:
    #             print(f"{e}")
    #     super().on_tab_changed(index)  # 调用父类的函数



    # def lable_click_ctrl(self, click_pos):
    #     self.download_screnn()
    #     print("emit lable_click_ctrl:", click_pos)
    #     app_model.video_server.fisheye_ctrl(click_pos)

    def slider_value_changed(self, value):
        self.view.depth_label.setText("Current Value: {}".format(self.view.depth_horizontalSlider.value() / 100))  # 更新 QLabel 的文本
        self.timer.start(100)  # 设置定时器间隔为100毫秒

    def depth_set(self):
        app_model.video_server.fisheye_depth_set(self.view.depth_horizontalSlider.value() / 100)

    def button_clicked(self):
        self.view.depth_horizontalSlider.setValue(10)

    def on_begin(self):
        # 获取参数
        result = server.get_external_cfg()
        cfg = json.dumps(result['body'], indent=4, separators=(', ', ': '), ensure_ascii=False)
        app_model.video_server.fisheye_init(cfg)
        # 获取图像
        # if m_global.m_connect_local:
        frame_1 = cv2.imread("m_data/hqtest/in_L.jpg")
        frame_2 = cv2.imread("m_data/hqtest/in_R.jpg")
        frame_3 = cv2.imread("m_data/hqtest/in_ML.jpg")
        frame_4 = cv2.imread("m_data/hqtest/in_MR.jpg")

        self.set_screnn_pixmap(frame_3, self.view.label_img_1)
        self.set_screnn_pixmap(frame_1, self.view.label_img_2)
        self.set_screnn_pixmap(frame_2, self.view.label_img_3)
        self.set_screnn_pixmap(frame_4, self.view.label_img_4)

        return True

    def set_screnn_pixmap(self, img, label):
        if img is None or not label:
            return False

        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        proportion_h = pixmap.height() / label.height()
        proportion_w = pixmap.width() / label.width()
        if proportion_w > proportion_h:
            proportion = proportion_h
        else:
            proportion = proportion_w
        pixmap = pixmap.scaled(int(pixmap.width() / proportion), int(pixmap.height() / proportion))
        # pixmap.setDevicePixelRatio(proportion)
        label.setPixmap(pixmap)
        return True

