#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import threading
from functools import partial

import shutil
import cv2
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtWidgets import QLabel

from controller.controller_base_tab import BaseControllerTab
from model.app import app_model
from server.internal.boardSplit import getBoardPosition
from server.internal.internal_server import *
from server.web.web_server import *

from utils.m_global import m_connect_local


class InternalCalibrationController(BaseControllerTab):
    video_map = {}
    internal_data_path = None
    work_thread = None
    work_thread_state = False
    screenshot_count = 0

    show_image_signal = pyqtSignal(str, str)
    show_image_fg_signal = pyqtSignal(int, str)
    work_thread_finish_success_signal = pyqtSignal(str)
    work_thread_finish_failed_signal = pyqtSignal(str)
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)
    start_video_fg_once = pyqtSignal()

    def __init__(self, base_view, base_model=None):
        super().__init__(base_view, base_model)

    def init(self):
        self.screeshot_buttom_timer = QTimer(self)
        self.screeshot_buttom_timer.timeout.connect(partial(self.view.set_screenshot_button_enable, True))

        self.tab_index = 0

        # 链接UI事件
        self.view.pushButton_set_internal_file_path.clicked.connect(self.on_choose_file)
        self.view.pushButton_start.clicked.connect(self.on_start)
        self.view.pushButton_screenshot.clicked.connect(self.on_screenshot)

        self.show_image_signal.connect(self.on_show_image)
        self.show_image_fg_signal.connect(self.on_show_image_fg)
        self.work_thread_finish_success_signal.connect(self.on_work_thread_finish_success)
        self.work_thread_finish_failed_signal.connect(self.on_work_thread_finish_failed)

        # 绑定配置文件中的相机与去显示的lable
        # app_model.camera_list
        self.bind_label_and_timer("left", self.view.label_video_fg, 0)  # 270)
        # self.bind_label_and_timer("middle_left", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("middle_right", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("right", self.view.label_video_fg, 270)

    # 切换设备类型
    def on_change_device_type(self, device_type):
        if device_type == "FG":
            self.view.set_layout_fg(True)
            self.view.set_layout_rx5(False)
        else:
            self.view.set_layout_fg(False)
            self.view.set_layout_rx5(True)

    # 选择内参存储文件路径
    def on_choose_file(self):
        self.internal_data_path = self.view.on_choose_file()

    # 开始标定
    def on_start(self):
        # 获取实时文件夹路径
        self.internal_data_path = self.view.get_choose_file_lineedit()
        if not self.internal_data_path:
            ## 创建目录
            sn = app_model.device_model.sn
            if not sn:
                self.log.log_err("sn获取失败")
                return

            internal_data_path = os.path.join(app_model.work_path_internal, sn)
            if not os.path.exists(internal_data_path):
                os.makedirs(internal_data_path)
            self.internal_data_path = internal_data_path

        if not self.internal_data_path:
            return

        if self.work_thread_state:
            return

        self.work_thread_state = True
        # 创建线程执行任务
        self.work_thread = threading.Thread(target=self.get_inter_stitch, daemon=True)
        self.work_thread.start()
        # 弹出对话框，进制界面操作
        # self.view.show_loading(msg="正在处理内参计算...")

    # 截图按钮槽函数
    def on_screenshot(self):
        self.view.set_screenshot_button_enable(False)
        # self.screeshot_buttom_timer.start(3000)

        # 获取实时文件夹路径

        self.internal_data_path = self.view.get_choose_file_lineedit()
        if not self.internal_data_path:
            ## 创建目录
            sn = app_model.device_model.sn
            if not sn:
                self.log.log_err("sn获取失败")
                return

            internal_data_path = os.path.join(app_model.work_path_internal, sn)
            if self.screenshot_count == 0 and os.path.exists(internal_data_path):
                shutil.rmtree(internal_data_path)

            if not os.path.exists(internal_data_path):
                os.makedirs(internal_data_path)
            self.internal_data_path = internal_data_path

        if not self.internal_data_path:
            return

        if self.work_thread_state:
            return

        self.work_thread_state = True
        # 创建线程执行任务
        self.work_thread = threading.Thread(target=self.save_screenshot, daemon=True)
        self.work_thread.start()

    # 实时显示图像
    def on_show_image(self, direction, filepath):
        if direction == "left":
            self.view.set_image_left(filepath)
        if direction == "middle":
            self.view.set_image_middle(filepath)
        if direction == "right":
            self.view.set_image_right(filepath)

    # 实时显示图像(fg)
    def on_show_image_fg(self, screen_label_count, filepath):
        self.view.set_image_fg(screen_label_count, filepath)

    # 保存帧
    def save_frame(self):
        self.show_message_signal.emit(True, "数据预处理")
        # 截图到指定目录进行计算
        internal_data_path_l = os.path.join(self.internal_data_path, "L")
        if not os.path.exists(internal_data_path_l):
            os.makedirs(internal_data_path_l)
        internal_data_path_m = os.path.join(self.internal_data_path, "M")
        if not os.path.exists(internal_data_path_m):
            os.makedirs(internal_data_path_m)
        internal_data_path_r = os.path.join(self.internal_data_path, "R")
        if not os.path.exists(internal_data_path_r):
            os.makedirs(internal_data_path_r)
        filename = f"ispPlayer_{int(time.time())}.jpg"
        ## 截图
        left_pic_path = os.path.join(internal_data_path_l, filename)
        middle_pic_path = os.path.join(internal_data_path_m, filename)
        right_pic_path = os.path.join(internal_data_path_r, filename)
        app_model.video_server.save_frame("left", left_pic_path)
        self.show_image_signal.emit("left", left_pic_path)
        app_model.video_server.save_frame("middle", middle_pic_path)
        self.show_image_signal.emit("middle", middle_pic_path)
        app_model.video_server.save_frame("right", right_pic_path)
        self.show_image_signal.emit("right", right_pic_path)
        ## 图像分割
        getBoardPosition(left_pic_path, (11, 8), 6, internal_data_path_l)
        getBoardPosition(middle_pic_path, (11, 8), 6, internal_data_path_m)
        getBoardPosition(right_pic_path, (11, 8), 6, internal_data_path_r)

    # 保存帧(fg)
    def save_screenshot(self):
        path_name_list = ["L", "ML", "MR", "R"]
        direction_list = ["left", "middle_left", "middle_right", "right"]
        direction_type = self.screenshot_count // 2

        if self.screenshot_count == 0:
            self.show_message_signal.emit(True, "左相机截图")
        elif self.screenshot_count == 8:
            self.screeshot_buttom_timer.stop()
            self.view.set_screenshot_button_enable(False)
            self.screenshot_count = 0
            self.start_video_unique("left", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.view.set_screenshot_button_text(self.screenshot_count)
            self.get_inter_stitch_fg()
            return
        internal_data_path = os.path.join(self.internal_data_path, path_name_list[direction_type])
        if not os.path.exists(internal_data_path):
            os.makedirs(internal_data_path)
        filename = f"ispPlayer_{int(time.time())}.jpg"
        ## 截图
        pic_path = os.path.join(internal_data_path, filename)
        # if True:
        if m_connect_local:
            frame = cv2.imread("m_data/camera.jpg")
            if direction_type == 0 or direction_type == 3:
                frame = cv2.resize(frame, (2960, 1664))
            elif direction_type == 1 or direction_type == 2:
                frame = cv2.resize(frame, (1920, 1080))
            cv2.imwrite(pic_path, frame)
        else:
            app_model.video_server.save_frame(direction_list[direction_type], pic_path)
        self.show_image_fg_signal.emit(self.screenshot_count, pic_path)
        self.view.set_screenshot_button_text(self.screenshot_count + 1)
        ## 图像分割
        getBoardPosition(pic_path, (11, 8), 6, internal_data_path, self.screenshot_count % 2)
        if self.screenshot_count == 1:
            self.start_video_unique("middle_left", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "中左相机截图")

        elif self.screenshot_count == 3:
            self.start_video_unique("middle_right", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "中右相机截图")

        elif self.screenshot_count == 5:
            self.start_video_unique("right", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "右相机截图")
        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        self.screenshot_count += 1

    # 进行内参拼接(rx5)
    def get_inter_stitch(self):
        if not self.check_device_factory_mode():
            self.work_thread_state = False
            return

        self.save_frame()

        self.show_message_signal.emit(True, "开始计算相机内参")
        get_stitch(self.internal_data_path, self.work_thread_finish_success_signal,
                   self.work_thread_finish_failed_signal)

    # 进行内参拼接(fg)
    def get_inter_stitch_fg(self):
        if not self.check_device_factory_mode():
            self.work_thread_state = False
            return

        self.show_message_signal.emit(True, "开始计算相机内参")
        get_stitch(self.internal_data_path, self.work_thread_finish_success_signal,
                   self.work_thread_finish_failed_signal)
        print("asd")

    # 内参计算成功则上传参数到目标相机
    def on_work_thread_finish_success(self, result):
        self.view.close_loading()
        self.work_thread = None
        if not result:
            self.show_message_signal.emit(False, "内参计算失败")
            self.work_thread_state = False
            return
        self.show_message_signal.emit(True, "内参计算完成")
        # self.view.set_internal_result(result)

        device_ip = app_model.device_model.ip
        self.show_message_signal.emit(True, "上传参数结果到相机")
        internal_file = self.save_internal_file(result, self.internal_data_path)
        self.work_thread = threading.Thread(target=self.upload_file, args=(device_ip, internal_file), daemon=True)
        self.work_thread.start()
        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        self.show_image_fg_signal.emit(-1, "")

    # 内参计算失败
    def on_work_thread_finish_failed(self, error_msg):
        # self.view.close_loading()
        self.show_message_signal.emit(False, f"内参处理" + error_msg)
        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        self.show_image_fg_signal.emit(-1, "")

    # 保存内参参数到本地
    @staticmethod
    def save_internal_file(result=None, file_name="inter_cfg.json", internal_file_path=None):
        if not result:
            return
        if internal_file_path is None:
            internal_file_path = os.path.join(os.getcwd(), "result", str(int(time.time())))
        if not os.path.exists(internal_file_path):
            os.makedirs(internal_file_path)
        internal_file = os.path.join(internal_file_path, "inter_cfg.json")
        with open(internal_file, "w", encoding="utf-8") as f:
            f.write(result)
        return internal_file

    def on_btn_upload_internal_file(self):
        self.device_ip = app_model.device_model.ip
        # 检查本地内容
        temp = self.view.get_internal_result()
        if not temp:
            if not self.internal_file:
                self.internal_file = self.save_internal_file(temp)
            else:
                # 更新文件
                self.save_internal_file(temp, os.path.dirname(self.internal_file))
        if not self.internal_file:
            self.show_message_signal.emit(False, "数据上传:数据内容错误")
            return

        self.work_thread = threading.Thread(target=self.upload_file, args=(self.internal_file,))
        self.work_thread.start()

    # 上传内参
    def upload_file(self, device_ip, internal_file):
        if not device_ip:
            self.show_message_signal.emit(False, "数据上传:设备IP异常")
            return

        if not server or not server.login(device_ip):
            self.show_message_signal.emit(False, "数据上传:设备登录失败")
            return

        if server.upload_file(filename=internal_file, upload_path="/mnt/usr/kvdb/usr_data_kvdb/inter_cfg"):
            self.show_message_signal.emit(True, "数据上传成功")
            self.reset_factory()
        else:
            self.show_message_signal.emit(False, "数据上传失败")
            server.logout()

    # 重启设备
    def reset_factory(self):
        self.reset_factory_mode()

        self.work_thread_state = False
        self.show_message_signal.emit(True, "标定完成，等待设备重启后查看结果")
        self.reboot_finish_signal.emit(2)
