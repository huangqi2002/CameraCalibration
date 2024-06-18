#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

import cv2
import numpy as np
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
    frame_dirct = {}
    dirct_list = []
    cfg_json = None
    select_point = {}

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

        # 选点
        self.view.label_img_2.lable_click_signal.connect(self.set_point_left)
        self.view.label_img_3.lable_click_signal.connect(self.set_point_right)

        # 显示当前值的标签
        self.view.changestate_pushButton.clicked.connect(self.button_clicked)  # 连接按钮点击事件到槽函数
        # 定时器
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.depth_set)

        # 开始预览
        self.view.pushButton_begin.clicked.connect(self.on_download)

        self.dirct_list = ["mid_left", "left", "right", "mid_right"]
        self.select_point = {"left": None, "right": None}

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

    def set_point_left(self, x, y):
        self.select_point["left"] = np.array([x * 1.0, y * 1.0])
        self.set_show_screnn_left()

    def set_point_right(self, x, y):
        self.select_point["right"] = np.array([x * 1.0, y * 1.0])
        self.set_show_screnn_right()

    def slider_value_changed(self, value):
        self.view.depth_label.setText(
            "Current Value: {}".format(self.view.depth_horizontalSlider.value() / 100))  # 更新 QLabel 的文本
        self.timer.start(100)  # 设置定时器间隔为100毫秒

    def depth_set(self):
        app_model.video_server.fisheye_depth_set(self.view.depth_horizontalSlider.value() / 100)

    def button_clicked(self):
        self.view.depth_horizontalSlider.setValue(10)

    def on_download(self):
        # 获取参数
        result = server.get_external_cfg()
        if result is None:
            return
        self.cfg_json = result['body']
        cfg = json.dumps(self.cfg_json, indent=4, separators=(', ', ': '), ensure_ascii=False)
        app_model.video_server.fisheye_init(cfg)
        print("获取参数成功")

        for dirct in self.dirct_list:
            self.frame_dirct[dirct] = self.download_img(dirct)
        print("获取图像成功")
        # 获取图像
        # if m_global.m_connect_local:

        self.set_show_screnn()
        return True

    def set_show_screnn(self):
        self.set_show_screnn_left()
        self.set_show_screnn_right()

    def set_show_screnn_left(self):
        if self.cfg_json is None:
            return
        frame_1, frame_3 = self.transformed_point("left", "mid_left", cfg=self.cfg_json, select_point=self.select_point["left"])
        print("left: 点变换成功")
        self.set_screnn_pixmap(frame_3, self.view.label_img_1)
        self.set_screnn_pixmap(frame_1, self.view.label_img_2)
        print("left: 图像设置成功")

    def set_show_screnn_right(self):
        if self.cfg_json is None:
            return
        frame_2, frame_4 = self.transformed_point("right", "mid_right", cfg=self.cfg_json, select_point=self.select_point["right"])
        print("right: 点变换成功")
        self.set_screnn_pixmap(frame_2, self.view.label_img_3)
        self.set_screnn_pixmap(frame_4, self.view.label_img_4)
        print("right: 图像设置成功")

    def set_screnn_pixmap(self, img, label):
        if img is None or not label:
            return False

        h, w, ch = img.shape
        bytes_per_line = ch * w
        q_image = QImage(img.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)

        proportion_h = pixmap.height() / label.height()
        proportion_w = pixmap.width() / label.width()
        # if proportion_w > proportion_h:
        #     proportion = proportion_h
        # else:
        #     proportion = proportion_w
        pixmap = pixmap.scaled(int(pixmap.width() / proportion_w), int(pixmap.height() / proportion_h))
        # QPixmap.save(pixmap, "./left.jpg")
        # pixmap.setDevicePixelRatio(proportion)
        label.setPixmap(pixmap)

        return True

    def transformed_point(self, dirct_1, dirct_2, cfg, select_point=None):
        if select_point is None:
            select_point = np.array([0.5, 0.3])

        # print(select_point)

        frame_1 = self.download_img(dirct_1)  # 鱼眼
        frame_2 = self.download_img(dirct_2)  # 普通

        point = select_point * np.array([frame_1.shape[1], frame_1.shape[0]])
        # print(point)

        # cv2.circle(frame_1, (int(point[0]), int(point[1])), 5, (0, 0, 255), -1)
        self.draw_cross(frame_1, point, (0, 255, 0))

        # 鱼眼相机点转去畸变普通相机
        print("鱼眼相机点转去畸变普通相机…………")
        calib_param = cfg[dirct_1 + "_calib"]
        mtx_1 = np.array(calib_param[2:11]).reshape(3, 3)
        dist_1 = np.array(calib_param[11:])
        M = np.array(cfg[dirct_1 + "_M"]).reshape(3, 3)
        new_camera_matrix_1 = np.multiply(mtx_1, [[0.6, 1, 1], [1, 0.6, 1], [1, 1, 1]])
        point_undistort = cv2.fisheye.undistortPoints(np.array([[point]]), mtx_1, dist_1, R=new_camera_matrix_1)[0][0]
        point_homogeneous = np.insert(point_undistort, 2, 1, 0)
        transformed_points_homogeneous = point_homogeneous @ M.T
        transformed_points = transformed_points_homogeneous[:2] / transformed_points_homogeneous[2]

        # map1, map2 = cv2.fisheye.initUndistortRectifyMap(mtx_1, dist_1, None, new_camera_matrix_1, (frame_2.shape[
        # 1], frame_2.shape[0]), cv2.CV_32FC1)

        # 去畸变普通相机反畸变
        print("去畸变普通相机反畸变…………")
        calib_param = cfg[dirct_2 + "_calib"]
        mtx_2 = np.array(calib_param[2:11]).reshape(3, 3)
        dist_2 = np.array(calib_param[11:])
        new_camera_matrix_2 = np.multiply(mtx_2, [[0.8, 1, 1], [1, 0.8, 1], [1, 1, 1]])
        mapx, mapy = cv2.initUndistortRectifyMap(mtx_2, dist_2, None, new_camera_matrix_2,
                                                 (frame_2.shape[1], frame_2.shape[0]),
                                                 cv2.CV_32FC1)
        x, y = int(transformed_points[1]), int(transformed_points[0])
        if 0 <= x < mapx.shape[0] and 0 <= y < mapx.shape[1] :
            point_2 = [mapx[x, y], mapy[x, y]]
            # print(point_2)

            # cv2.circle(frame_2, (int(point_2[0]), int(point_2[1])), 5, (0, 0, 255), -1)
            self.draw_cross(frame_2, point_2, (0, 255, 0))
            #
            # cv2.imshow("frame_1", frame_1)
            # cv2.imshow("frame_2", frame_2)
            # cv2.waitKey(0)

        return frame_1, frame_2

    def draw_cross(self, image, center, color, size=50, thickness=10):
        x, y = int(center[0]), int(center[1])

        # Check if the horizontal line is within image boundaries
        if (x - size >= 0) and (x + size < image.shape[1]):
            cv2.line(image, (x - size, y), (x + size, y), color, thickness)

        # Check if the vertical line is within image boundaries
        if (y - size >= 0) and (y + size < image.shape[0]):
            cv2.line(image, (x, y - size), (x, y + size), color, thickness)

    def download_img(self, dirct):
        frame = None
        if dirct == "mid_left":
            frame = cv2.imread("m_data/hqtest/in_ML.jpg")
        elif dirct == "left":
            frame = cv2.imread("m_data/hqtest/in_L.jpg")
        elif dirct == "right":
            frame = cv2.imread("m_data/hqtest/in_R.jpg")
        else:
            frame = cv2.imread("m_data/hqtest/in_MR.jpg")

        return frame
