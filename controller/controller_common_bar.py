#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
import time

from PyQt5.QtCore import pyqtSignal, QTimer

from controller.controller_base import BaseController
from model.app import app_model
from server.video.video_server import VideoServer
from model.camera import Camera
from server.web.web_server import *
from utils.run_para import m_global


class CommonBarController(BaseController):
    signal_show_log_view = pyqtSignal(bool)
    signal_change_device_type = pyqtSignal(str)
    signal_connect_device = pyqtSignal(bool)
    signal_reboot_device = pyqtSignal()

    signal_start_video_server = pyqtSignal()
    show_message_signal = pyqtSignal(bool, str)

    device_type = None

    def init(self):
        app_model.device_model.ip = self.view.get_device_ip()

        self.view.set_ok_ng_status(False)
        self.view.set_ok_ng_msg("设备未连接")

        self.view.pushButton_show_log_view.clicked.connect(self.on_show_log_view)
        self.view.pushButton_show_log_view.setVisible(False)
        self.view.pushButton_connect_device.clicked.connect(self.on_connect_device)
        self.view.pushButton_reboot_device.clicked.connect(self.on_reboot_device)

        self.view.comboBox_choise_device_type.currentTextChanged.connect(self.on_choose_device_type)
        self.view.device_combo_box_add_items(["FG", "RX5"])

        self.signal_start_video_server.connect(self.start_video_server)

        self.login_now = 0 # 2:运行，1：暂停中，0：暂停成功

    # 在message栏里实时显示连接数
    def cameraconnect_num_show(self, cnt):
        self.show_message_signal.emit(True, f"连接摄像头:{cnt}")

    # 选择设备类型
    def on_choose_device_type(self, device_type):
        self.log.log_debug(f"on_choose_device_type: {device_type}")
        if self.device_type == device_type:
            return

        self.view.pushButton_connect_device.setEnabled(False)  # 禁用按钮
        QTimer.singleShot(1000, lambda: self.view.pushButton_connect_device.setEnabled(True))
        if app_model.is_connected:
            self.disconnect_device()

        self.device_type = device_type
        self.signal_change_device_type.emit(device_type)

    def on_show_log_view(self):
        if app_model.show_log_view:
            self.signal_show_log_view.emit(False)
            self.view.set_log_btn_text(self.tr("显示日志"))
        else:
            self.signal_show_log_view.emit(True)
            self.view.set_log_btn_text(self.tr("关闭日志"))

    def set_ok_ng_msg_status(self, msg, status=True):
        self.view.set_ok_ng_msg(msg)
        self.view.set_ok_ng_status(status)

    # 连接设备按钮槽函数
    def on_connect_device(self):
        self.view.pushButton_connect_device.setEnabled(False)  # 禁用按钮
        QTimer.singleShot(1000, lambda: self.view.pushButton_connect_device.setEnabled(True))
        if app_model.is_connected:
            self.disconnect_device()
        else:
            self.connect_device()
            # server.ctrl_osd(0)

    # 连接设备
    def connect_device(self, connect_type=0):
        device_ip = self.view.get_device_ip()
        app_model.device_model.ip = device_ip
        if not device_ip:
            return
        # print(server.login(device_ip))
        if self.login_now != 0:
            self.login_now = 1
            return
        self.login_now = 2
        threading.Thread(target=self.device_login, args=(connect_type, m_global.connect_timeout), daemon=True).start()
        # self.signal_state_device.emit(1, "login success")

    # 登录设备
    def device_login(self, connect_type, timeout=50):
        self.view.set_connect_device_btn_text("停止登录")
        # 设备登陆获取设备信息(并设置为工厂模式，设置工厂模式后设备会重启)
        for time_index in range(app_model.login_retry_max_count):
            self.show_message_signal.emit(True, f"设备登录中...{time_index}")
            if not server.login(app_model.device_model.ip, timeout=timeout):
                if self.login_now == 1 or time_index == app_model.login_retry_max_count - 1:
                    self.show_message_signal.emit(False, f"设备登录失败")
                    self.login_now = 0
                    self.view.set_connect_device_btn_text("连接设备")
                    return
                time.sleep(1)
                continue
            device_info = server.get_device_info()
            if not device_info:
                self.show_message_signal.emit(False, "获取设备信息失败")
                self.login_now = 0
                self.view.set_connect_device_btn_text("连接设备")
                return
            body = device_info.get("body")
            if not body:
                self.show_message_signal.emit(False, "获取设备信息失败:body")
                self.login_now = 0
                self.view.set_connect_device_btn_text("连接设备")
                return
            app_model.device_model.sn = body.get("serial_num")
            app_model.device_model.board_version = body.get("board_version")
            break

        if connect_type == 0:
            self.show_message_signal.emit(True, "登录成功")
            server.ctrl_osd(0)
        elif connect_type == 1:
            self.show_message_signal.emit(True, "标定完成，确认标定结果")
        else:
            self.show_message_signal.emit(True, "设备重启完成")
        self.signal_start_video_server.emit()
        self.login_now = 0

    # 根据配置文件初始化相机与地址的配对关系
    def start_video_server(self):
        app_model.is_connected = True
        self.view.set_connect_device_btn_text("断开连接")
        # 等待设备重启后获取rtsp视频流

        video_config_list = app_model.config_video.get(self.device_type)
        if not video_config_list:
            self.log.log_err(f"{self.device_type} type not in config_video.json")
            return

        for config_item in video_config_list:
            camera = Camera()
            camera.rtsp_url = f"{config_item.get('shame')}://{app_model.device_model.ip}:{config_item.get('port')}{config_item.get('url')}"
            direction = config_item.get("direction")
            app_model.camera_list[direction] = camera
        camera = Camera()
        app_model.camera_list["all"] = camera
        camera = Camera()
        app_model.camera_list["stitch"] = camera

        # camera = Camera()
        # camera.rtsp_url = f"rtsp://{device_ip}:8557/left_main_0_1"
        # app_model.camera_list["left"] = camera
        app_model.video_server.create(app_model.camera_list)
        app_model.video_server.signal_cameraconnect_num.connect(self.cameraconnect_num_show)
        # 播放视频流
        self.signal_connect_device.emit(True)

    # 断开与设备的连接
    def disconnect_device(self):
        # 关闭视频流
        self.signal_connect_device.emit(False)
        app_model.video_server.release()
        self.view.set_connect_device_btn_text("连接设备")
        app_model.is_connected = False

    # 重启设备
    def on_reboot_device(self):
        # 关闭视频流，通知重启设备
        self.signal_reboot_device.emit()

    # 重启设备完成
    def on_reboot_finish(self, reboot_type=1):
        self.connect_device(reboot_type)
