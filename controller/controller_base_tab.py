#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import threading
import time
from enum import Enum
from functools import partial

import cv2
import numpy as np
from PyQt5.QtCore import QTimer, QObject, pyqtSlot
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel

from server.external.ex_Calib import ex_calib
from utils import m_global

from controller.controller_base import BaseController
from model.app import app_model
from model.video import Video
from server.web.web_server import server


def lists_equal(list1, list2):
    # 检查列表长度是否相等
    if len(list1) != len(list2):
        return False

    # 逐一比较列表中的元素
    for i in range(len(list1)):
        if isinstance(list1[i], float) and isinstance(list2[i], float):
            # 如果元素是浮点数，使用 round() 函数四舍五入到指定小数位数
            if round(list1[i], 6) != round(list2[i], 6):
                return False
        else:
            # 检查其他类型的元素是否相等
            if list1[i] != list2[i]:
                return False
    return True


def calibrate_para_gen(direction="left", dic_size=5, dic_num=1000, board_width=m_global.bW,
                       board_height=m_global.bH, board_spacer=m_global.bSpacer, threshold_min=7, threshold_max=200,
                       square_size=m_global.bSize, board_num=m_global.bNum,
                       save_path=None):
    calibrate_para = {"direction": direction, "dic_size": dic_size, "dic_num": dic_num, "board_width": board_width,
                      "board_height": board_height, "board_spacer": board_spacer, "threshold_min": threshold_min,
                      "threshold_max": threshold_max, "square_size": square_size, "board_num": board_num,
                      "save_path": save_path}
    return calibrate_para


class BaseControllerTab(BaseController):
    tab_index = 0
    current_tab_index = 0
    video_map = {}

    show_message_signal = None
    reboot_finish_signal = None
    current_direction = 'left'
    current_cameras = None
    external_data_path = ""

    stitch_mode_right = 0x001
    stitch_mode_fisheye = 0x010
    stitch_mode_left = 0x100

    # 绑定配置文件中的相机与去显示的lable
    def bind_label_and_timer(self, direction: str, label: QLabel, rotate):
        video = Video()
        video.label = label
        video.rotate = rotate
        self.video_map[direction] = video

    # 切换界面
    def on_tab_changed(self, index):
        self.current_tab_index = index
        # 切换界面非本界面则暂停一切显示
        if self.tab_index != index:
            self.parse_video()
            return
        # 切换界面为本界面则开始播放视频
        video_server = app_model.video_server
        if video_server is None:
            return
        app_model.video_server.tab_index = self.tab_index

        cameras = app_model.video_server.get_cameras()
        if cameras is None:
            return
        if app_model.is_connected:
            current_cameras = cameras
            app_model.video_server.pause_all()
            # print(f"{index} pause_all")
            self.start_video(cameras)

    # 连接设备
    def on_connect_device(self, connect_state):
        if self.current_tab_index != self.tab_index:
            return
        if connect_state:
            app_model.video_server.pause_all()
            cameras = app_model.video_server.get_cameras()
            # print(cameras)
            for key, video in self.video_map.items():
                if video.timer is not None:
                    video.timer.stop()
                    video.timer = None
            self.start_video(cameras)
        else:
            self.parse_video()

    # 播放视频
    # cameras是要播放的相机，其属于video_server，可以读到相机不断变换的帧
    # video_map中记录了相机与对应的定时器
    def start_video(self, cameras):
        # print(f"Timer is begin active:")
        if cameras is None:
            return
        for key, video in self.video_map.items():
            camera = cameras.get(key)
            if camera is None:
                continue
            app_model.video_server.resume(key)
            ret_a = None
            if video.label is not None:
                if video.timer is None:
                    video.timer = QTimer(self)
                    ret_a = video.timer.timeout.connect(partial(self.update_frame, camera, video))
                video.timer.start(100)
                # print(f"{key} Timer is active: {ret_a}", video.timer.isActive())
            # print("start_timer")

    # 暂停播放视频
    def parse_video(self):
        for key, video in self.video_map.items():
            # app_model.video_server.pause(key)
            if video.timer:
                video.timer.stop()
                print(f"{key} is pause")

    # 暂停播放视频，并只播放指定视频
    def start_video_unique(self, video_para_list):  # direction: str, label: QLabel, rotate):
        # def start_video_unique(self, direction: str):
        self.parse_video()
        for key, video in self.video_map.items():
            app_model.video_server.pause(key)

        self.video_map = {}
        for para in video_para_list:
            self.bind_label_and_timer(para["direction"], para["label"], para["rotate"])
        cameras = app_model.video_server.get_cameras()
        if cameras is None:
            return
        if app_model.is_connected:
            self.start_video(cameras)
        # print("start_video_unique\n")
        # app_model.video_server.resume_uniq(direction)

    def start_video_all(self, direction_list, label: QLabel, rotate):
        self.parse_video()
        self.video_map = {}

        for direction in direction_list:
            app_model.video_server.resume(direction)
            self.bind_label_and_timer(direction, None, rotate)

        self.bind_label_and_timer("all", label, rotate)
        cameras = app_model.video_server.get_cameras()
        if cameras is None:
            return
        if app_model.is_connected:
            self.start_video(cameras)
        # print("start_video\n")

    # 更新视频帧到lable上
    # camera中可以读到相机当前时刻的帧
    # video中包含了相机对lable的对应关系
    def update_frame(self, camera, video):
        # print(f"{camera.rtsp_url} update_frame\n")
        if camera is None or camera.frame is None:
            # self.log.log_err(f"{camera} Tab({self.tab_index}), Invalid camera or frame")
            return
        if not camera.frame_is_ok:
            return
        frame = camera.frame
        camera.frame_is_ok = False

        if video is None or video.label is None:
            # self.log.log_err(f"Tab({self.tab_index}), Invalid video or label")
            return
        label = video.label

        frame_rotated = None
        rotate = video.rotate
        label_size = label.size()
        if rotate == 0:
            frame_resized = cv2.resize(frame, (label_size.width(), label_size.height() - 1))
            frame_rotated = frame_resized
        else:
            frame_resized = cv2.resize(frame, (label_size.height() - 1, label_size.width()))
            # print("update_frame, frame_resized", frame_resized.shape)
            if rotate == 90:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_90_CLOCKWISE)
            elif rotate == 180:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_180)
            elif rotate == 270:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_90_COUNTERCLOCKWISE)

        if frame_rotated is None:
            return
        frame_rgb = cv2.cvtColor(frame_rotated, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        # new_pixmap = pixmap.scaled(2960, 1664)
        # print(f"before label.size:{label.size()}")
        label.setPixmap(pixmap)
        # print(f"after label.size:{label.size()}")

    # 设置工厂模式
    # 尝试连接设备并设置工厂模式，如果设置工厂模式失败，则等待设备重启，再次尝试设置工厂模式，直到成功设置或达到最大重试次数
    def check_device_factory_mode(self):
        need_wait_device_restart = False
        # 连接设备设置工厂模式
        for time_index in range(app_model.login_retry_max_count):
            if not server.login(app_model.device_model.ip):
                time.sleep(1)
                continue

            result = self.set_factory_mode()
            if result == 0:
                need_wait_device_restart = True
            elif result == 1:
                need_wait_device_restart = False
            break

        if need_wait_device_restart:
            # 等待设备重启
            for time_index in range(app_model.login_retry_max_count):
                if not server.login(app_model.device_model.ip):
                    time.sleep(1)
                    continue

                result = self.set_factory_mode()
                if result == 1:
                    self.show_message_signal.emit(True, "设置工厂模式成功")
                    return True
                else:
                    self.show_message_signal.emit(False, "设置工厂模式失败")
                    return False
        self.show_message_signal.emit(True, "设置工厂模式成功")
        return True

    # 重新设置工厂模式
    def reset_factory_mode(self):
        reset_factory_mode_result = server.set_factory_mode(mode=0)
        self.log.log_debug(f"reset_factory_mode_result: {reset_factory_mode_result}")

    # 设置工厂模式
    def set_factory_mode(self):
        # if m_global.m_global_debug:
        #     factory_mode_result = True
        #     self.log.log_debug(f"factory_mode_result: {factory_mode_result}")
        #     return 1
        # else:
        factory_mode_result = server.set_factory_mode(mode=1)
        self.log.log_debug(f"factory_mode_result: {factory_mode_result}")

        if not factory_mode_result:
            return -1
        try:
            factory_mode_json = json.loads(factory_mode_result)
            if factory_mode_json.get("state") == 200:
                return 0
            elif factory_mode_json.get("state") == 406:
                self.show_message_signal.emit(True, "设备已处于工厂模式")
                return 1
            else:
                return -3
        except Exception as e:
            return -2

    # 重启设备按钮槽函数
    def on_reboot_device(self):
        self.parse_video()
        if self.current_tab_index != self.tab_index:
            return
        threading.Thread(target=self.reboot_device, daemon=True).start()

    # 重启设备
    def reboot_device(self):
        for time_index in range(app_model.login_retry_max_count):
            login_result = server.login(app_model.device_model.ip)
            if not login_result:
                time.sleep(1)
                continue

            self.show_message_signal.emit(True, "设备重启中")
            server.reboot()
            time.sleep(1)
            break

        for time_index in range(app_model.login_retry_max_count):
            if not server.login(app_model.device_model.ip):
                time.sleep(1)
                continue

            self.show_message_signal.emit(True, "设备重启完成")
            server.logout()
            self.reboot_finish_signal.emit(1)
            return
        self.show_message_signal.emit(False, "重新连接设备失败")

    def clear_folder(self, folder_path):
        """
        清空指定文件夹中的所有内容
        """
        try:
            # 遍历文件夹中的所有文件和子文件夹
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                # 如果是文件则直接删除
                if os.path.isfile(file_path):
                    os.remove(file_path)
                # 如果是子文件夹则递归清空
                elif os.path.isdir(file_path):
                    self.clear_folder(file_path)
                    os.rmdir(file_path)
            print(f"文件夹 '{folder_path}' 已成功清空。")
        except Exception as e:
            print(f"清空文件夹 '{folder_path}' 时出现错误：{e}")

    def create_path_new(self, path):
        if os.path.exists(path):
            self.clear_folder(path)
            print("\n")
        else:
            os.makedirs(path)
        # print(f"mkdir {path}")

        # 标定两目相机之间的外参

    def calib_ex_aruco(self, img_0, img_1, mode="", save_path_1=None, save_path_2=None, cfg_params=None):
        check = True
        if cfg_params is None:
            with open(app_model.config_ex_internal_path, 'r') as file:
                cfg_params = json.load(file)
        ex_calib.set_intrinsic_params(cfg_params)

        dirct_1, dirct_2, board_id, prefix = "left", "right", m_global.board_id_fish, ""  # 双鱼眼标定模式
        if mode == "left":  # 左边鱼眼+普通标定模式
            dirct_1, dirct_2, board_id, prefix = "left", "mid_left", m_global.board_id_left, "left_"  # 左边鱼眼+普通标定模式
        elif mode == "right":  # 右边鱼眼+普通标定模式
            dirct_1, dirct_2, board_id, prefix = "right", "mid_right", m_global.board_id_right, "right_"  # 右边鱼眼+普通标定模式

        ex_calib.show_img = np.zeros((3000, 2960, 3))

        ret, rvecs_1, tvecs_1, point_dict_1 = ex_calib.calibrate(dirct_1, img_0, dic_size=5, dic_num=1000,
                                                                 board_width=m_global.bW,
                                                                 board_height=m_global.bH,
                                                                 board_spacer=m_global.bSpacer, board_id=board_id,
                                                                 square_size=m_global.bSize, board_num=m_global.bNum,
                                                                 save_path=save_path_1, check_mode=True)

        if not ret:
            return cfg_params
        print(f"{prefix}{dirct_1} ex calib ok")

        ret, rvecs_2, tvecs_2, point_dict_2 = ex_calib.calibrate(dirct_2, img_1, dic_size=5, dic_num=1000,
                                                                 board_width=m_global.bW,
                                                                 board_height=m_global.bH,
                                                                 board_spacer=m_global.bSpacer, board_id=board_id,
                                                                 square_size=m_global.bSize, board_num=m_global.bNum,
                                                                 save_path=save_path_2,
                                                                 check_mode=True)  # "../m_data/aruco/ex/camera1.jpg")

        if not ret:
            return cfg_params
        print(f"{prefix}{dirct_1} ex calib ok")

        common_keys = set(point_dict_1.keys()) & set(point_dict_2.keys())
        # 输出具有相同键的元素
        distance = 0.0
        distance_count = 0
        for key in common_keys:
            print(np.sqrt(np.sum((point_dict_1[key] - point_dict_2[key]) ** 2)))
            distance += np.sqrt(np.sum((point_dict_1[key] - point_dict_2[key]) ** 2))
            distance_count += 1
        distance /= distance_count
        print(f"distance : {distance}\n")

        cfg_params[prefix + 'rvecs_1'] = rvecs_1.flatten().tolist()
        cfg_params[prefix + 'tvecs_1'] = tvecs_1.flatten().tolist()
        cfg_params[prefix + 'rvecs_2'] = rvecs_2.flatten().tolist()
        cfg_params[prefix + 'tvecs_2'] = tvecs_2.flatten().tolist()
        # print(f"{app_model.config_ex_internal_path} read OK")
        # # print(f" ex_result : {ex_result} ")
        # try:
        #     result_json = json.dumps(cfg_params, indent=4)
        #     print("JSON serialization successful.")
        # except Exception as e:
        #     print(f"An error occurred during JSON serialization: {e}")
        # self.save_external_file(result_json)
        # print("save_external_file success")

        # # 上传文件
        # self.show_message_signal.emit(True, "上传拼接结果")
        # filename = "external_cfg.json"
        # result = self.upload_file(app_model.device_model.ip, os.path.join(self.external_data_path, filename),
        #                           f"/mnt/usr/kvdb/usr_data_kvdb/{filename}")
        # if not result:
        #     self.show_message_signal.emit(False, "上传拼接文件失败")
        #     server.logout()
        # else:
        #     self.show_message_signal.emit(True, "上传拼接文件成功")
        #     # self.reboot_device()
        #     # self.reset_factory_mode()
        #     # self.signal_reboot_device.emit()
        #     # self.show_message_signal.emit(True, "标定完成，等待设备重启后查看结果") hqtest
        #     self.show_message_signal.emit(True, "标定完成")
        #     # self.reboot_finish_signal.emit(2)

        return cfg_params

        # 进行外参计算

    def get_ex_stitch(self, stitch_mode=stitch_mode_fisheye | stitch_mode_left | stitch_mode_right):
        self.show_message_signal.emit(True, "开始计算相机外参")
        cfg_params = None
        if stitch_mode & self.stitch_mode_fisheye:
            img_name_1, img_name_2 = "L", "R"
            img_ex_1 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_1}.jpg")
            img_ex_2 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_2}.jpg")
            cfg_params = self.calib_ex_aruco(img_ex_1, img_ex_2,
                                             save_path_1=f"{self.external_data_path}\\camera{img_name_1}.jpg",
                                             save_path_2=f"{self.external_data_path}\\camera{img_name_2}.jpg",
                                             cfg_params=cfg_params)
        if stitch_mode & self.stitch_mode_left:
            img_name_1, img_name_2 = "L_L", "ML_L"
            img_ex_1 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_1}.jpg")
            img_ex_2 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_2}.jpg")
            cfg_params = self.calib_ex_aruco(img_ex_1, img_ex_2, "left",
                                             save_path_1=f"{self.external_data_path}\\camera{img_name_1}.jpg",
                                             save_path_2=f"{self.external_data_path}\\camera{img_name_2}.jpg",
                                             cfg_params=cfg_params)

        if stitch_mode & self.stitch_mode_right:
            img_name_1, img_name_2 = "R_R", "MR_R"
            img_ex_1 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_1}.jpg")
            img_ex_2 = cv2.imread(f"{self.external_data_path}\\chessboard_{img_name_2}.jpg")
            cfg_params = self.calib_ex_aruco(img_ex_1, img_ex_2, "right",
                                             save_path_1=f"{self.external_data_path}\\camera{img_name_1}.jpg",
                                             save_path_2=f"{self.external_data_path}\\camera{img_name_2}.jpg",
                                             cfg_params=cfg_params)

        return cfg_params

    def save_external_file(self, result=None, file_name="external_cfg.json", external_file_path=None):
        # print(f"save {file_name}")
        if not result:
            return
        if external_file_path is None:
            external_file_path = self.external_data_path
        if not os.path.exists(external_file_path):
            os.makedirs(external_file_path)
        external_file = os.path.join(external_file_path, "external_cfg.json")
        # external_file = external_file.replace('\\', '/')
        print(f"save {external_file}..........")

        with open(external_file, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"save {external_file} OK")
        # 应用在设备上
        app_model.video_server.fisheye_external_init(external_file)
        return external_file

    def check_external_cfg(self, local_external_cfg_path):
        return True
        # local_external_cfg_name = local_external_cfg_path.replace('\\', '/')
        # with open(local_external_cfg_name, 'r') as file:
        #     local_external_cfg = json.load(file)
        #
        # if not local_external_cfg:
        #     self.show_message_signal.emit(False, "获取设备本地外参文件失败:body")
        #     return False
        #
        # external_cfg_info = server.get_external_cfg()
        # if not external_cfg_info:
        #     self.show_message_signal.emit(False, "获取设备外参文件失败")
        #     return False
        # external_cfg = external_cfg_info.get("body")
        # if not external_cfg:
        #     self.show_message_signal.emit(False, "获取设备外参文件失败:body")
        #     return False
        #
        # # 检查字典长度是否相等
        # if len(local_external_cfg) != len(external_cfg):
        #     return False
        # # 逐一比较字典中的键和值
        # for key in local_external_cfg.keys():
        #     if key not in external_cfg:
        #         return False
        #     if not lists_equal(local_external_cfg[key], external_cfg[key]):
        #         return False
        #
        # return True
