#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from model.app import app_model
from model.config import Config
from model.device import Device
from server.video.video_server import VideoServer

from controller.controller_base import BaseController
from controller.controller_common_bar import CommonBarController
from controller.controller_internal_calibration import InternalCalibrationController
from controller.controller_video_calibration import VideoCalibrationController
from controller.controller_video_result import VideoResultController
from controller.controller_log_view import LogViewController
from utils import m_global


class MainController(BaseController):
    device_model = None

    # 界面上方控制栏
    common_bar_controller = None
    # 内参标定界面
    internal_calibration_controller = None
    # 外参标定界面
    video_calibration_controller = None
    # 拼接结果显示界面
    video_result_controller = None
    log_view_controller = None

    def init(self):
        self.init_model()  # 读取配置文件，初始化model
        self.init_controller()  # 初始化界面控制器
        self.init_server()  # 初始化视频服务器
        self.init_parameter() # 初始化参数

        # 初始化选择标定拼接Tab以及FG类型
        self.view.switch_tab_index(1)
        self.on_change_device_type("FG")

    # 读取配置文件，初始化model
    def init_model(self):
        app_model.work_path_root = os.getcwd()
        # 配置文件
        app_model.work_path_configs = os.path.join(app_model.work_path_root, "configs")
        # 内参
        app_model.work_path_internal = os.path.join(app_model.work_path_root, "data", "internal")
        # 外参
        app_model.work_path_external = os.path.join(app_model.work_path_root, "data", "external")

        # 读取配置文件
        app_model.config_model = Config(app_model.work_path_configs)
        app_model.config_stream = app_model.config_model.read_config_file("config_stream.json")
        app_model.config_video = app_model.config_model.read_config_file("config_video.json")
        app_model.config_fg = app_model.config_model.read_config_file("config_fg.json")

        app_model.device_model = Device()
        # 读取配置文件，初始化model

        # 初始化内外参矩阵
        # app_model.config_internal = app_model.config_model.read_config_file("configs/internal/external_cfg.json")
        pass

    # 初始化界面控制器
    def init_controller(self):
        # 界面切换
        self.view.signal_tab_changed.connect(self.on_tab_changed)
        # ip地址
        self.view.widget_common_bar.lineEdit_device_ip.setText(app_model.config_fg.get("ip"))
        # 界面上方控制栏
        self.common_bar_controller = CommonBarController(self.view.widget_common_bar)
        self.common_bar_controller.signal_show_log_view.connect(self.on_show_log_view)
        self.common_bar_controller.signal_change_device_type.connect(self.on_change_device_type)
        self.common_bar_controller.signal_connect_device.connect(self.on_connect_device)
        self.common_bar_controller.signal_reboot_device.connect(self.on_reboot_device)
        self.common_bar_controller.show_message_signal.connect(self.on_show_message)
        # 内参标定界面
        self.internal_calibration_controller = InternalCalibrationController(self.view.tab_internal_calibration)
        self.internal_calibration_controller.show_message_signal.connect(self.on_show_message)
        self.internal_calibration_controller.reboot_finish_signal.connect(self.on_reboot_finish)
        self.internal_calibration_controller.signal_reboot_device.connect(self.on_reboot_device)
        self.internal_calibration_controller.start_video_fg_once.connect(self.start_video_fg_inter_once)
        # 外参标定界面
        self.video_calibration_controller = VideoCalibrationController(self.view.tab_video_calibration)
        self.video_calibration_controller.show_message_signal.connect(self.on_show_message)
        self.video_calibration_controller.reboot_finish_signal.connect(self.on_reboot_finish)
        self.video_calibration_controller.signal_reboot_device.connect(self.on_reboot_device)
        # 拼接结果显示界面
        self.video_result_controller = VideoResultController(self.view.tab_video_result)
        self.video_result_controller.show_message_signal.connect(self.on_show_message)
        self.video_result_controller.reboot_finish_signal.connect(self.on_reboot_finish)

        self.log_view_controller = LogViewController(self.view.widget_log_view)

    # 切换界面
    def on_tab_changed(self, index):
        self.log.log_debug("on_tab_changed", index)
        self.internal_calibration_controller.on_tab_changed(index)
        self.video_calibration_controller.on_tab_changed(index)
        self.video_result_controller.on_tab_changed(index)

    # 切换界面以刷新fg内参界面显示
    def start_video_fg_inter_once(self):
        self.on_tab_changed(1)
        self.on_tab_changed(0)

    # 切换fg,rx5类型
    def on_change_device_type(self, device_type):
        self.internal_calibration_controller.on_change_device_type(device_type)
        self.video_calibration_controller.on_change_device_type(device_type)

    # 显示日志
    def on_show_log_view(self, is_show):
        self.view.on_show_log_view(is_show)

    # 连接设备
    def on_connect_device(self, connect_state):
        self.internal_calibration_controller.on_connect_device(connect_state)
        self.video_calibration_controller.on_connect_device(connect_state)
        self.video_result_controller.on_connect_device(connect_state)

    # 重启设备
    def on_reboot_device(self):
        self.internal_calibration_controller.on_reboot_device()
        self.video_calibration_controller.on_reboot_device()
        self.video_result_controller.on_reboot_device()

    # 初始化视频服务器
    # VideoServer按照配置文件中的内容创建多个线程对配置文件中的相机数据进行读取
    def init_server(self):
        app_model.video_server = VideoServer()

    def init_parameter(self):
        m_global.m_connect_local = app_model.config_fg.get("m_connect_local")
        m_global.m_global_debug = app_model.config_fg.get("m_global_debug")

    # 设置界面上面message栏显示的信息内容
    def on_show_message(self, status, msg):
        self.log.log_debug(f"on_show_msg: status-{status} msg-{msg}")
        self.common_bar_controller.set_ok_ng_msg_status(msg=msg, status=status)

    # 重启结束，转至拼接结果显示界面
    def on_reboot_finish(self, reboot_type):
        self.view.switch_tab_index(2)
        self.common_bar_controller.on_reboot_finish(reboot_type)

    # 界面显示
    def show(self):
        self.view.show()
