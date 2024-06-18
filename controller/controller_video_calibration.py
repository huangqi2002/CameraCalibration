#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# import sys
import json
import os
import shutil
import threading
import time

import cv2
import numpy as np
from PyQt5.QtCore import pyqtSignal

from controller.controller_base_tab import BaseControllerTab, lists_equal
from model.app import app_model
# from server.external.lib3rd.load_lib import sdk
from server.web.web_server import server
from server.internal.boardSplit import getBoardPosition

from utils.run_para import m_global
import ctypes as C


class VideoCalibrationController(BaseControllerTab):
    video_map = {}
    external_data_path: str = None
    work_thread = None
    work_thread_state = False
    video_para_list = None

    show_image_signal = pyqtSignal(str, str)
    show_loading_signal = pyqtSignal(bool, str)
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)
    signal_reboot_device = pyqtSignal()

    position_index = 1

    def __init__(self, base_view, base_model=None):
        super().__init__(base_view, base_model)

    def init(self):
        # sys.stdout.reconfigure(encoding='utf-8')
        self.tab_index = 1

        # 链接UI事件
        self.view.pushButton_img_left_middle.clicked.connect(self.on_img_left_middle)
        self.view.pushButton_img_middle_right.clicked.connect(self.on_img_middle_right)
        self.view.pushButton_start.clicked.connect(self.on_start)

        self.view.pushButton_left_play.clicked.connect(self.position_play)
        self.view.pushButton_middle_play.clicked.connect(self.position_play)
        self.view.pushButton_right_play.clicked.connect(self.position_play)

        self.show_image_signal.connect(self.on_show_image)
        self.show_loading_signal.connect(self.on_show_loading_dialog)

        # 绑定配置文件中的相机与去显示的lable
        self.bind_label_and_timer("left", self.view.label_video_left, 0)  # 270)
        # self.bind_label_and_timer("middle_left", self.view.label_video_middle, 270)
        self.bind_label_and_timer("right", self.view.label_video_right, 0)  # 270)

        self.view.set_position_type_button_enable(self.position_index)

        self.video_para_list = [
            [
                {"direction": "middle_left", "label": self.view.label_video_left, "rotate": 0},
                {"direction": "left", "label": self.view.label_video_right, "rotate": 0}
            ],
            [
                {"direction": "left", "label": self.view.label_video_left, "rotate": 0},
                {"direction": "right", "label": self.view.label_video_right, "rotate": 0}
            ],
            [
                {"direction": "right", "label": self.view.label_video_left, "rotate": 0},
                {"direction": "middle_right", "label": self.view.label_video_right, "rotate": 0}
            ]
        ]

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

    def remove_dir_sync(directory):
        for root, dirs, files in os.walk(directory, topdown=False):
            for name in files:
                file_path = os.path.join(root, name)
                os.remove(file_path)
            for name in dirs:
                dir_path = os.path.join(root, name)
                os.rmdir(dir_path)
        os.rmdir(directory)

    # 截图相机位置切换槽函数
    def position_play(self):
        if self.work_thread_state:
            return
        sender_button = self.sender()
        button_name = sender_button.text()
        try:
            index = self.view.position_type_text.index(button_name)
            self.view.set_position_type_button_enable(index)
            self.on_position_type_changed(index)
        except ValueError:
            print(f"The element {button_name} is not in the list.")

    # 截图相机位置切换函数
    def on_position_type_changed(self, index):
        self.position_index = index
        # 发出显示信号
        self.show_message_signal.emit(True, self.view.position_type_text[self.position_index] + "拼接")
        # 更改显示视频
        self.start_video_unique(self.video_para_list[index])

    # 开始标定槽函数
    def on_start(self):
        # self.upload_file(app_model.device_model.ip, "D:\\VZ\\camera_calibration\\CameraCalibrationTool\\configs\\internal\\config_fg_90_524.json",
        #                  f"/mnt/usr/kvdb/usr_data_kvdb/external_cfg.json")
        # self.upload_file(app_model.device_model.ip, "D:\VZ\camera_calibration\CameraCalibrationTool\configs\internal\inter_cfg_90",
        #                  f"/mnt/usr/kvdb/usr_data_kvdb/inter_cfg")


        # 获取实时文件夹路径
        # self.external_data_path = self.view.get_choose_file_lineedit()
        self.view.set_start_button_enable(False)

        if not self.external_data_path:
            # 截图到指定目录进行计算
            sn = app_model.device_model.sn
            if not sn:
                self.log.log_err("sn获取失败")
                self.view.set_start_button_enable(True)
                return

            ## 创建目录
            external_data_path = os.path.join(app_model.work_path_external, sn)
            self.create_path_new(external_data_path)
            self.external_data_path = external_data_path

        if not self.external_data_path:
            self.view.set_start_button_enable(True)
            return

        if self.work_thread_state:
            self.view.set_start_button_enable(True)
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
    def save_frame(self, key_index):
        if key_index == 0:
            image_path_1 = os.path.join(self.external_data_path, "chessboard_ML_L.jpg")
            image_path_2 = os.path.join(self.external_data_path, "chessboard_L_L.jpg")
            save_frame_key_1, save_frame_key_2 = "middle_left", "left"
            local_img_1, local_img_2 = "in_ML", "in_L"
        elif key_index == 1:
            image_path_1 = os.path.join(self.external_data_path, "chessboard_L.jpg")
            image_path_2 = os.path.join(self.external_data_path, "chessboard_R.jpg")
            save_frame_key_1, save_frame_key_2 = "left", "right"
            local_img_1, local_img_2 = "in_L", "in_R"
        else:
            image_path_1 = os.path.join(self.external_data_path, "chessboard_R_R.jpg")
            image_path_2 = os.path.join(self.external_data_path, "chessboard_MR_R.jpg")
            save_frame_key_1, save_frame_key_2 = "right", "middle_right"
            local_img_1, local_img_2 = "in_R", "in_MR"

        if not m_global.aruco_flag:
            local_img_1 = local_img_1.replace("in", "ex")
            local_img_2 = local_img_2.replace("in", "ex")

        if m_global.m_connect_local:
            try:
                frame = cv2.imread(f"m_data/hqtest/{local_img_1}.jpg")
                cv2.imwrite(image_path_1, frame)
            except Exception as e:
                print(f"m_data/hqtest/{local_img_1}.jpg读取出现错误：{e}")
                return False
        else:
            app_model.video_server.save_frame(save_frame_key_1, image_path_1)

        self.upload_stitch_fg_img(app_model.device_model.ip, image_path_1)
        self.show_image_signal.emit("left", image_path_1)
        # getBoardPosition(image_path_1, (11, 8), self.external_data_path, 1, True)

        # app_model.video_server.save_frame("middle", middle_image_path)
        # self.show_image_signal.emit("middle", middle_image_path)

        # if True:
        if m_global.m_connect_local:
            try:
                frame = cv2.imread(f"m_data/hqtest/{local_img_2}.jpg")
                cv2.imwrite(image_path_2, frame)
            except Exception as e:
                print(f"m_data/hqtest/{local_img_2}.jpg读取出现错误：{e}")
                return False
        else:
            app_model.video_server.save_frame(save_frame_key_2, image_path_2)

        self.upload_stitch_fg_img(app_model.device_model.ip, image_path_2)
        self.show_image_signal.emit("right", image_path_2)

    def chunked_json_dumps(data, chunk_size=100):
        """
        将数据分块序列化为 JSON 字符串
        """
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
        result_json = ''
        for chunk in chunks:
            result_json += json.dumps(chunk, indent=4)
        return result_json

    # 进行拼接参数计算
    def get_calibration(self):
        key_index = self.position_index

        self.save_frame(key_index)

        self.show_message_signal.emit(True, "执行拼接算法")
        ###############
        # 求旋转平移矩阵
        ###############
        stitch_mode = super().stitch_mode_left
        if key_index == 1:
            stitch_mode = super().stitch_mode_fisheye
        elif key_index == 2:
            stitch_mode = super().stitch_mode_right
        ex_calib_ok, cfg_params = super().get_ex_stitch(stitch_mode)

        if not ex_calib_ok:
            self.show_message_signal.emit(False, "外参标定失败...")
        else:
            # 保存文件
            try:
                result_json = json.dumps(cfg_params, indent=4)
                print("JSON serialization successful.")
            except Exception as e:
                print(f"An error occurred during JSON serialization: {e}")
            self.save_external_file(result_json)
            self.show_message_signal.emit(True, "参数保存本地成功")
            print("save_external_file success")

            # 上传文件
            self.show_message_signal.emit(True, "上传拼接结果")
            filename = "external_cfg.json"
            result = self.upload_file(app_model.device_model.ip, os.path.join(self.external_data_path, filename),
                                      f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")
            if not result:
                self.show_message_signal.emit(False, "上传拼接文件失败")
                server.logout()
            else:
                self.show_message_signal.emit(True, "上传拼接文件成功")
                self.show_message_signal.emit(True, "标定完成")

        self.view.set_start_button_enable(True)
        self.work_thread_state = False

    # 上传拼接参数（fg）
    def upload_stitch_fg(self, device_ip, file_path):
        if not device_ip or not file_path:
            return

        print("uploading")
        filename = "external_cfg.json"
        result = self.upload_file(device_ip, os.path.join(file_path, filename),
                                  f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")
        if not result:
            return False
        if not self.check_external_cfg(os.path.join(file_path, filename)):
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
        print("uploading_file")
        # if m_global.m_global_debug:
        #     self.show_message_signal.emit(True, "参数结果保存成功")
        #     return True
        if not device_ip:
            self.show_message_signal.emit(False, "数据上传:设备IP异常")
            return False

        if not server or not server.login(device_ip):
            self.show_message_signal.emit(False, "数据上传:设备登录失败")
            return False

        file_name = filepath.replace('\\', '/').split("/")[-1]
        print(f"filename={filepath}, upload_path={upload_path}")
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
