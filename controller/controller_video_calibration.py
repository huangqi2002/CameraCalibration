#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import sys
import json
import os
import threading
import time

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSignal

import shutil
from controller.controller_base_tab import BaseControllerTab
from model.app import app_model
from server.external.lib3rd.load_lib import sdk
from server.web.web_server import server

from utils.m_global import m_connect_local
from utils.global_debug import m_global_debug

import ctypes as C


class VideoCalibrationController(BaseControllerTab):
    video_map = {}
    external_data_path = None
    work_thread = None
    work_thread_state = False

    show_image_signal = pyqtSignal(str, str)
    show_loading_signal = pyqtSignal(bool, str)
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)
    signal_reboot_device = pyqtSignal()

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
        # if True:
        if m_connect_local:
            frame = cv2.imread("m_data/hqtest/ex_L.jpg")
            cv2.imwrite(left_image_path, frame)
            # app_model.video_server.save_frame("left", None)
        else:
            app_model.video_server.save_frame("left", left_image_path)
        self.upload_stitch_fg_img(app_model.device_model.ip, left_image_path)
        self.show_image_signal.emit("left", left_image_path)

        # app_model.video_server.save_frame("middle", middle_image_path)
        # self.show_image_signal.emit("middle", middle_image_path)

        # if True:
        if m_connect_local:
            frame = cv2.imread("m_data/hqtest/ex_R.jpg")
            cv2.imwrite(right_image_path, frame)
            # app_model.video_server.save_frame("right", None)
        else:
            app_model.video_server.save_frame("right", right_image_path)
        self.upload_stitch_fg_img(app_model.device_model.ip, right_image_path)
        self.show_image_signal.emit("right", right_image_path)

        ## 复制配置文件
        fg_external_path = os.path.join(app_model.work_path_configs, "fg")
        for filename in os.listdir(fg_external_path):
            src_file = os.path.join(fg_external_path, filename)
            dst_file = os.path.join(self.external_data_path, filename)
            cmd = f"copy {src_file} {dst_file}"
            self.log.log_debug(cmd)
            os.system(cmd)

    # 进行平移旋转矩阵的计算
    def get_rtMatrix(self):
        camera0_files = [file for file in os.listdir(self.external_data_path) if file.startswith('camera0_')]
        camera0_files.sort()
        middle_file_index = len(camera0_files) // 2
        middle_file = os.path.join(self.external_data_path, camera0_files[middle_file_index])
        print(f"get_rtMatrix img : {middle_file}")
        stitch_cacle_img0 = cv2.imread(middle_file)
        stitch_cacle_img0 = cv2.rotate(stitch_cacle_img0, cv2.ROTATE_180)

        camera1_files = [file for file in os.listdir(self.external_data_path) if file.startswith('camera1_')]
        camera1_files.sort()
        middle_file_index = len(camera1_files) // 2
        middle_file = os.path.join(self.external_data_path, camera1_files[middle_file_index])
        print(f"get_rtMatrix img : {middle_file}")
        stitch_cacle_img1 = cv2.imread(middle_file)

        rvecs_1 = np.zeros(dtype=np.float64, shape=(3, 1, 1))
        tvecs_1 = np.zeros(dtype=np.float64, shape=(3, 1, 1))
        rvecs_2 = np.zeros(dtype=np.float64, shape=(3, 1, 1))
        tvecs_2 = np.zeros(dtype=np.float64, shape=(3, 1, 1))
        cv2.imwrite("stitch_cacle_img0.jpg", stitch_cacle_img0)
        cv2.imwrite("stitch_cacle_img1.jpg", stitch_cacle_img1)
        app_model.video_server.fisheye_dll.fisheye_pnp(stitch_cacle_img0.ctypes.data_as(C.POINTER(C.c_ubyte))
                                                       , stitch_cacle_img1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                                       , 11, 8, 25, rvecs_1.ctypes.data_as(C.POINTER(C.c_double))
                                                       , tvecs_1.ctypes.data_as(C.POINTER(C.c_double))
                                                       , rvecs_2.ctypes.data_as(C.POINTER(C.c_double))
                                                       , tvecs_2.ctypes.data_as(C.POINTER(C.c_double)))
        # 将矩阵展平为向量
        rvecs_1_list = rvecs_1.flatten().tolist()
        tvecs_1_list = tvecs_1.flatten().tolist()
        rvecs_2_list = rvecs_2.flatten().tolist()
        tvecs_2_list = tvecs_2.flatten().tolist()

        ex_result = None
        if app_model.config_ex_internal_path is not None:
            with open(app_model.config_ex_internal_path, encoding="utf-8", errors="ignore") as f:
                ex_result = json.load(f)
        ex_result['rvecs_1'] = rvecs_1_list
        ex_result['tvecs_1'] = tvecs_1_list
        ex_result['rvecs_2'] = rvecs_2_list
        ex_result['tvecs_2'] = tvecs_2_list

        result_json = json.dumps(ex_result)

        self.save_external_file(result_json)

    # 进行拼接参数计算
    def get_calibration(self):
        # if m_global_debug:
        #     self.work_thread_state = True
        # elif not self.check_device_factory_mode():
        #     self.work_thread_state = False
        #     return

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

        ###############
        # 求旋转平移矩阵
        ###############
        self.get_rtMatrix()

        # 上传文件
        self.show_message_signal.emit(True, "上传拼接结果")
        result = self.upload_stitch_fg(app_model.device_model.ip, self.external_data_path)
        if not result:
            self.show_message_signal.emit(False, "上传拼接文件失败")
            server.logout()
        else:
            self.show_message_signal.emit(True, "上传拼接文件成功")
            # self.reboot_device()
            # self.reset_factory_mode()
            # self.signal_reboot_device.emit()
            # self.show_message_signal.emit(True, "标定完成，等待设备重启后查看结果") hqtest
            self.show_message_signal.emit(True, "标定完成")
            # self.reboot_finish_signal.emit(2)

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

        filename = "external_cfg.json"
        result = self.upload_file(device_ip, os.path.join(file_path, filename),
                                  f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")

        if not result:
            return False
        return True

    def upload_stitch_fg_img(self, device_ip, filename):
        if not device_ip or not filename:
            return
        result = self.upload_file(device_ip, filename,
                                  f"/mnt/usr/kvdb/usr_data_kvdb/{os.path.basename(filename)}")
        if not result:
            return False

    # 上传拼接参数
    def upload_file(self, device_ip, filepath, upload_path):
        if m_global_debug:
            self.show_message_signal.emit(True, "参数结果保存成功")
            return True
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

    # 保存外参参数到本地
    def save_external_file(self, result=None, file_name="external_cfg.json", external_file_path=None):
        if not result:
            return
        if external_file_path is None:
            external_file_path = self.external_data_path
        if not os.path.exists(external_file_path):
            os.makedirs(external_file_path)
        external_file = os.path.join(external_file_path, "external_cfg.json")
        with open(external_file, "w", encoding="utf-8") as f:
            f.write(result)
        # 应用在设备上
        app_model.video_server.fisheye_external_init(external_file)
        return external_file

    def on_img_left_middle(self):
        pass

    def on_img_middle_right(self):
        pass
