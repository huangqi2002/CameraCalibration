#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import sys
import os
import threading

import cv2
from PyQt5.QtCore import pyqtSignal

import shutil
from controller.controller_base_tab import BaseControllerTab
from model.app import app_model
from server.external.lib3rd.load_lib import sdk
from server.web.web_server import server

from utils.m_global import m_connect_local


class VideoCalibrationController(BaseControllerTab):
    video_map = {}
    external_data_path = None
    work_thread = None
    work_thread_state = False

    show_image_signal = pyqtSignal(str, str)
    show_loading_signal = pyqtSignal(bool, str)
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)

    def init(self):
        # sys.stdout.reconfigure(encoding='utf-8')
        self.tab_index = 1

        # 链接UI事件
        self.view.pushButton_img_left_middle.clicked.connect(self.on_img_left_middle)
        self.view.pushButton_img_middle_right.clicked.connect(self.on_img_middle_right)
        self.view.pushButton_start.clicked.connect(self.on_start)

        self.show_image_signal.connect(self.on_show_image)
        self.show_loading_signal.connect(self.on_show_loading_dialog)

        # 绑定配置文件中的相机与去显示的lable
        self.bind_label_and_timer("left", self.view.label_video_left, 0)  # 270)
        # self.bind_label_and_timer("middle_left", self.view.label_video_middle, 270)
        self.bind_label_and_timer("right", self.view.label_video_right, 0)  # 270)

    def on_show_loading_dialog(self, show, msg):
        # if show:
        #     self.view.show_loading(msg)
        # else:
        #     self.view.close_loading()
        pass

    # 改变设备类型
    def on_change_device_type(self, device_type):
        self.view.set_layout_middle_visible(False)
        # if device_type in ["FG"]:
        #     self.view.set_layout_middle_visible(True)
        # else:
        #     self.view.set_layout_middle_visible(False)

    # 开始标定槽函数
    def on_start(self):
        # 获取实时文件夹路径
        # self.external_data_path = self.view.get_choose_file_lineedit()
        if not self.external_data_path:
            # 截图到指定目录进行计算
            sn = app_model.device_model.sn
            if not sn:
                self.log.log_err("sn获取失败")
                return

            ## 创建目录
            external_data_path = os.path.join(app_model.work_path_external, sn)
            if os.path.exists(external_data_path):
                shutil.rmtree(external_data_path)
            if not os.path.exists(external_data_path):
                os.makedirs(external_data_path)
            self.external_data_path = external_data_path

        if not self.external_data_path:
            return

        if self.work_thread_state:
            return

        self.work_thread_state = True
        # 创建线程执行任务
        self.work_thread = threading.Thread(target=self.get_calibration, daemon=True)
        self.work_thread.start()
        # self.show_loading_signal.emit(True, "正在处理拼接参数配置...")

    # 显示图像
    def on_show_image(self, direction, filepath):
        if direction == "left":
            self.view.set_image_left(filepath)
        # if direction == "middle":
        #     self.view.set_image_middle(filepath)
        if direction == "right":
            self.view.set_image_right(filepath)

    # 保存帧
    def save_frame(self):
        ## 截图
        left_image_path = os.path.join(self.external_data_path, "camera0.jpg")
        # middle_image_path = os.path.join(self.external_data_path, "camera1.jpg")
        right_image_path = os.path.join(self.external_data_path, "camera1.jpg")
        #if True:
        if m_connect_local:
            frame = cv2.imread("m_data/camera0.jpg")
            cv2.imwrite(left_image_path, frame)
        else:
            app_model.video_server.save_frame("left", left_image_path)
        self.show_image_signal.emit("left", left_image_path)

        # app_model.video_server.save_frame("middle", middle_image_path)
        # self.show_image_signal.emit("middle", middle_image_path)

        #if True:
        if m_connect_local:
            frame = cv2.imread("m_data/camera1.jpg")
            cv2.imwrite(right_image_path, frame)
        else:
            app_model.video_server.save_frame("right", right_image_path)
        self.show_image_signal.emit("right", right_image_path)

        ## 复制配置文件
        fg_external_path = os.path.join(app_model.work_path_configs, "fg")
        for filename in os.listdir(fg_external_path):
            src_file = os.path.join(fg_external_path, filename)
            dst_file = os.path.join(self.external_data_path, filename)
            cmd = f"copy {src_file} {dst_file}"
            self.log.log_debug(cmd)
            os.system(cmd)

    # 进行拼接参数计算
    def get_calibration(self):
        if not self.check_device_factory_mode():
            self.work_thread_state = False
            return

        self.save_frame()

        self.show_message_signal.emit(True, "数据预处理")
        print("befor rotate_and_resize_images")
        result_rotate_and_resize_images = sdk.rotate_and_resize_images(self.external_data_path)
        self.log.log_debug(f"result_rotate_and_resize_images: {result_rotate_and_resize_images}")

        self.show_message_signal.emit(True, "读取配置文件")
        yml_path = os.path.join(self.external_data_path, "temp_chessboard.yml")
        self.log.log_debug(f"yml_path: {yml_path}")
        if not os.path.exists(yml_path):
            self.show_message_signal.emit(False, "配置文件未找到")
            self.work_thread_state = False
            return
        with open(yml_path, "r", encoding="utf-8") as f:
            yml_lines = f.readlines()

        with open(yml_path, "w", encoding="utf-8") as f:
            for index, line in enumerate(yml_lines):
                if line.startswith("base_directory"):
                    yml_lines[index] = f"base_directory: '{self.external_data_path}'\n".replace("\\", "\\\\")
                elif line.startswith("input_filename"):
                    yml_lines[
                        index] = f"input_filename: '{os.path.join(self.external_data_path, 'stitch.cal')}'\n".replace(
                        "\\", "\\\\")
                elif line.startswith("output_filename"):
                    yml_lines[
                        index] = f"output_filename: '{os.path.join(self.external_data_path, 'model.cal')}'\n".replace(
                        "\\", "\\\\")
            f.writelines(yml_lines)

        self.show_message_signal.emit(True, "执行拼接算法")
        result_model_calibration = sdk.model_calibration(yml_path)
        self.log.log_debug(f"result_model_calibration: {result_model_calibration}")
        if result_model_calibration != 0:
            self.show_message_signal.emit(False, "拼接失败")
            self.work_thread_state = False
            return
        cal_path = os.path.join(self.external_data_path, "model.cal")
        result_fg_lut_generate = sdk.fg_lut_generate(cal_path, self.external_data_path)
        self.log.log_debug(f"result_fg_lut_generate: {result_fg_lut_generate}")
        self.show_message_signal.emit(True, "拼接成功")

        # 上传文件
        self.show_message_signal.emit(True, "上传拼接结果")
        result = self.upload_stitch_fg(app_model.device_model.ip, self.external_data_path)
        if not result:
            self.show_message_signal.emit(False, "上传拼接文件失败")
            server.logout()
        else:
            self.show_message_signal.emit(True, "上传拼接文件成功")
            self.reset_factory_mode()
            self.show_message_signal.emit(True, "标定完成，等待设备重启后查看结果")
            self.reboot_finish_signal.emit(2)

        self.work_thread_state = False

    # 上传拼接参数（fg）
    def upload_stitch_fg(self, device_ip, file_path):
        if not device_ip or not file_path:
            return
        for filename in os.listdir(file_path):
            if filename.startswith("stitch_lut"):
                result = self.upload_file(device_ip, os.path.join(file_path, filename),
                                          f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")
                if not result:
                    return False

        filename = "stitch_cfg.json"
        result = self.upload_file(device_ip, os.path.join(file_path, filename),
                                  f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")
        if not result:
            return False
        return True

    # 上传拼接参数
    def upload_file(self, device_ip, filepath, upload_path):
        if not device_ip:
            self.show_message_signal.emit(False, "数据上传:设备IP异常")
            return False

        if not server or not server.login(device_ip):
            self.show_message_signal.emit(False, "数据上传:设备登录失败")
            return False

        file_name = filepath.replace('\\', '/').split("/")[-1]
        if server.upload_file(filename=filepath, upload_path=upload_path):
            self.show_message_signal.emit(True, f"{file_name}, 数据上传成功")
            return True
        else:
            self.show_message_signal.emit(False, "数据上传失败")
            return False

    def on_img_left_middle(self):
        pass

    def on_img_middle_right(self):
        pass
