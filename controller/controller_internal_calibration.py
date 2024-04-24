#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import os
import threading
from functools import partial

import cv2
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel

from controller.controller_base_tab import BaseControllerTab, lists_equal
from model.app import app_model
from server.internal.boardSplit import getBoardPosition
from server.internal.internal_server import *
from server.web.web_server import *

from utils import m_global


class InternalCalibrationController(BaseControllerTab):
    video_map = {}
    internal_data_path = None
    internal_data = None
    work_thread = None
    work_thread_state = False
    # undistorted_bool = False
    screenshot_count = 0
    position_index = 0
    device_type = "FG"
    screenshot_lable_ok = []  # 已成功地截图位置

    show_image_signal = pyqtSignal(str, str)
    show_image_fg_signal = pyqtSignal(int, str)
    work_thread_finish_success_signal = pyqtSignal(str)
    work_thread_finish_failed_signal = pyqtSignal(str)
    show_message_signal = pyqtSignal(bool, str)
    reboot_finish_signal = pyqtSignal(int)
    start_video_fg_once = pyqtSignal()
    signal_reboot_device = pyqtSignal()

    def __init__(self, base_view, base_model=None):
        super().__init__(base_view, base_model)

    def init(self):
        self.screeshot_buttom_timer = QTimer(self)
        self.screeshot_buttom_timer.timeout.connect(partial(self.view.set_screenshot_button_enable, True))

        self.tab_index = 0

        # 控件初始化
        self.view.undistorted_checkBox.setChecked(False)

        # 链接UI事件
        self.view.pushButton_set_internal_file_path.clicked.connect(self.on_choose_file)
        self.view.pushButton_start.clicked.connect(self.on_start)
        self.view.pushButton_screenshot.clicked.connect(self.on_screenshot)
        self.view.undistorted_checkBox.stateChanged.connect(self.undistorted)

        self.view.pushButton_left_play.clicked.connect(self.position_play)
        self.view.pushButton_midleft_play.clicked.connect(self.position_play)
        self.view.pushButton_midright_play.clicked.connect(self.position_play)
        self.view.pushButton_right_play.clicked.connect(self.position_play)

        self.show_image_signal.connect(self.on_show_image)
        self.show_image_fg_signal.connect(self.on_show_image_fg)
        self.work_thread_finish_success_signal.connect(self.on_work_thread_finish_success)
        self.work_thread_finish_failed_signal.connect(self.on_work_thread_finish_failed)

        # 绑定配置文件中的相机与去显示的lable
        # app_model.camera_list
        self.bind_label_and_timer("left", self.view.label_video_fg, 0)  # 270)
        self.view.set_position_type_button_enable(0)
        # self.bind_label_and_timer("middle_left", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("middle_right", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("right", self.view.label_video_fg, 270)

        self.direction_list = ["left", "middle_left", "middle_right", "right"]

    # 切换设备类型
    def on_change_device_type(self, device_type):
        self.device_type = device_type
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
        self.view.set_start_button_enable(False)
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

    # 截图相机位置切换槽函数
    def on_position_type_changed(self, index):
        self.view.set_screenshot_button_text(index * 2)
        self.position_index = index
        # 发出显示信号
        self.show_message_signal.emit(True, self.view.position_type_text[self.position_index] + "相机截图")
        # 更改显示视频
        self.start_video_unique(self.direction_list[index], self.view.label_video_fg, 0)
        # self.start_video_fg_once.emit()
        # 如果视频还没连接上，使截图按钮不可使
        # if app_model.video_server.camera_state(self.direction_list[index]):
        #     self.view.set_screenshot_button_enable(False)

    # 截图按钮槽函数
    def on_screenshot(self):
        self.view.set_screenshot_button_enable(False)
        # self.screeshot_buttom_timer.start(3000)

        # 获取实时文件夹路径
        self.internal_data_path = self.view.get_choose_file_lineedit()
        if not self.internal_data_path:
            # 创建目录
            sn = app_model.device_model.sn
            if not sn:
                self.log.log_err("sn获取失败")
                return

            internal_data_path = os.path.join(app_model.work_path_internal, sn)
            # 第一次截图之前已经存在，则删除文件夹
            if self.screenshot_count == 0:
                self.create_path_new(internal_data_path)
            self.internal_data_path = internal_data_path

        if not self.internal_data_path:
            return

        if self.work_thread_state:
            return

        self.work_thread_state = True
        # 创建线程执行任务
        self.view.undistorted_checkBox.setChecked(False)
        self.work_thread = threading.Thread(target=self.save_screenshot, daemon=True)
        self.work_thread.start()

    # 去畸变按钮槽函数
    def undistorted(self, state):
        app_model.video_server.set_undistorted_bool(state)

    def update_frame(self, camera, video):
        # print(f" update_frame in : {self.undistorted_bool}")
        # print(f"{camera.rtsp_url} update_frame\n")
        if camera is None or camera.frame is None:
            # self.log.log_err(f"Tab({self.tab_index}), Invalid camera or frame")
            return
        frame = camera.frame

        if video is None or video.label is None:
            self.log.log_err(f"Tab({self.tab_index}), Invalid video or label")
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

    # 实时显示图像
    def on_show_image(self, direction, filepath):
        if direction == "left":
            self.view.set_image_left(filepath)
        if direction == "middle":
            self.view.set_image_middle(filepath)
        if direction == "right":
            self.view.set_image_right(filepath)

    # 实时显示截图图像(fg)
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
        getBoardPosition(left_pic_path, (11, 8), internal_data_path_l)
        getBoardPosition(middle_pic_path, (11, 8), internal_data_path_m)
        getBoardPosition(right_pic_path, (11, 8), internal_data_path_r)

    # 保存帧(fg)
    def save_screenshot(self):
        path_name_list = ["L", "ML", "MR", "R"]
        position = self.view.position_type_text[self.position_index]
        # 使按钮处于失效状态
        # self.view.set_screenshot_button_enable(False)
        # 创建截图保存路径，存在则清空并重新创建
        internal_data_path = os.path.join(self.internal_data_path, path_name_list[self.position_index])
        print(f"\n{internal_data_path}\n")
        self.create_path_new(internal_data_path)

        filename = f"ispPlayer_{int(time.time())}.jpg"
        pic_path = os.path.join(internal_data_path, filename)
        # 读取文件并保存
        if m_global.m_connect_local:
            if self.position_index == 0:
                frame = cv2.imread("m_data/hqtest/in_L.jpg")
            elif self.position_index == 1:
                frame = cv2.imread("m_data/hqtest/in_ML.jpg")
            elif self.position_index == 2:
                frame = cv2.imread("m_data/hqtest/in_MR.jpg")
            else:
                frame = cv2.imread("m_data/hqtest/in_R.jpg")
            cv2.imwrite(pic_path, frame)
        else:
            ret = app_model.video_server.save_frame(self.direction_list[self.position_index], pic_path, False)
            if ret != 0:
                self.work_thread_state = False
                self.view.set_screenshot_button_enable(True)
                return

        # frame = cv2.imread("m_data/" + path_name_list[self.position_index] + ".jpg")  # hq301test
        # cv2.imwrite(pic_path, frame)  # hq301test

        # 将截图在lable中进行显示
        self.show_image_fg_signal.emit(self.position_index * 2, pic_path)
        ## 图像分割
        getBoardPosition(pic_path, (11, 8), internal_data_path)
        if path_name_list[self.position_index] not in self.screenshot_lable_ok:
            self.screenshot_count += 1
            self.screenshot_lable_ok.append(path_name_list[self.position_index])
            # print(f"\n{self.screenshot_count}\n")
            if self.screenshot_count == 4:
                self.view.set_start_button_enable(True)
        self.view.set_screenshot_button_enable(True)
        self.work_thread_state = False

    # 自动保存帧(fg)
    def save_screenshot_auto(self):
        path_name_list = ["L", "ML", "MR", "R"]
        direction_type = self.screenshot_count // 2

        if self.screenshot_count == 0:
            self.show_message_signal.emit(True, "左相机截图")
        elif self.screenshot_count == 8:
            self.screeshot_buttom_timer.stop()
            self.view.set_screenshot_button_enable(False)
            # self.screenshot_count = 0
            self.start_video_unique("left", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.view.set_screenshot_button_text(self.screenshot_count)
            self.get_inter_stitch()
            return
        internal_data_path = os.path.join(self.internal_data_path, path_name_list[direction_type])
        if not os.path.exists(internal_data_path):
            os.makedirs(internal_data_path)
        filename = f"ispPlayer_{int(time.time())}.jpg"
        ## 截图
        pic_path = os.path.join(internal_data_path, filename)
        # if True:
        if m_global.m_connect_local:
            if direction_type == 0:
                frame = cv2.imread("m_data/hqtest/in_L.jpg")
            elif direction_type == 1:
                frame = cv2.imread("m_data/hqtest/in_ML.jpg")
            elif direction_type == 2:
                frame = cv2.imread("m_data/hqtest/in_MR.jpg")
            else:
                frame = cv2.imread("m_data/hqtest/in_R.jpg")
            cv2.imwrite(pic_path, frame)
            # app_model.video_server.save_frame(self.direction_list[direction_type], None)
        else:
            app_model.video_server.save_frame(self.direction_list[direction_type], pic_path)
        self.show_image_fg_signal.emit(self.screenshot_count, pic_path)
        self.view.set_screenshot_button_text(self.screenshot_count + 1)
        ## 图像分割
        getBoardPosition(pic_path, (11, 8), internal_data_path, self.screenshot_count % 2)
        if self.screenshot_count == 1:
            self.start_video_unique("middle_left", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "最左相机截图")

        elif self.screenshot_count == 3:
            self.start_video_unique("middle_right", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "最右相机截图")

        elif self.screenshot_count == 5:
            self.start_video_unique("right", self.view.label_video_fg, 0)
            self.start_video_fg_once.emit()
            self.show_message_signal.emit(True, "右相机截图")
        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        self.screenshot_count += 1

    # 进行内参拼接
    def get_inter_stitch(self):
        # if not self.check_device_factory_mode():
        #     self.work_thread_state = False
        #     return
        if self.device_type != "FG":
            self.save_frame()

        self.show_message_signal.emit(True, "开始计算相机内参")
        get_stitch(self.internal_data_path, self.work_thread_finish_success_signal,
                   self.work_thread_finish_failed_signal)

    # # 进行内参拼接(fg)
    # def get_inter_stitch_fg(self):
    #     # if not self.check_device_factory_mode():
    #     #     self.work_thread_state = False
    #     #     return
    #
    #     self.show_message_signal.emit(True, "开始计算相机内参")
    #     get_stitch(self.internal_data_path, self.work_thread_finish_success_signal,
    #                self.work_thread_finish_failed_signal)

    # 内参计算成功则上传参数到目标相机
    def on_work_thread_finish_success(self, result):
        self.view.close_loading()
        self.work_thread = None
        if not result:
            self.show_message_signal.emit(False, "内参计算失败")
            self.work_thread_state = False
            return
        self.screenshot_count = 0
        self.screenshot_lable_ok = []
        self.show_message_signal.emit(True, "内参计算完成")
        self.internal_data = result
        # self.view.set_internal_result(result)

        device_ip = app_model.device_model.ip
        internal_file = self.save_internal_file(result, self.internal_data_path)

        # 生成漫游拼接所需内参
        # ex_result = json.loads(result)
        # ex_right_calib = ex_result['right_calib']
        # ex_right_calib[4] = ex_right_calib[0] - ex_right_calib[4]
        # ex_right_calib[7] = ex_right_calib[1] - ex_right_calib[7]
        # ex_result['right_calib'] = ex_right_calib
        # ex_result_str = json.dumps(ex_result, indent=4)
        ex_internal_file = self.save_internal_file(result, os.path.dirname(internal_file), "external_cfg.json")
        # 应用在设备上
        app_model.video_server.fisheye_internal_init(ex_internal_file)
        app_model.config_ex_internal_path = ex_internal_file

        # if m_global.m_global_debug:
        #     self.show_message_signal.emit(True, "参数结果保存成功")
        # else:
        self.show_message_signal.emit(True, "上传参数结果到相机")
        self.work_thread = threading.Thread(target=self.upload_file, args=(device_ip, internal_file), daemon=True)
        self.work_thread.start()

        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        self.show_image_fg_signal.emit(-1, "")

    # 内参计算失败
    def on_work_thread_finish_failed(self, error_msg):
        # self.view.close_loading()
        self.show_message_signal.emit(False, f"内参处理" + error_msg)
        if error_msg.startswith('内参获取失败：L'):
            self.screenshot_lable_ok.remove('内参获取失败：L')
            self.view.set_position_type_button_enable(0)
            self.on_position_type_changed(0)
        elif error_msg.startswith('内参获取失败：ML'):
            self.screenshot_lable_ok.remove('ML')
            self.view.set_position_type_button_enable(1)
            self.on_position_type_changed(1)
        elif error_msg.startswith('内参获取失败：MR'):
            self.screenshot_lable_ok.remove('MR')
            self.view.set_position_type_button_enable(2)
            self.on_position_type_changed(2)
        elif error_msg.startswith('内参获取失败：R'):
            self.screenshot_lable_ok.remove('R')
            self.view.set_position_type_button_enable(3)
            self.on_position_type_changed(3)
        self.screenshot_count -= 1

        self.work_thread_state = False
        self.view.set_screenshot_button_enable(True)
        # self.show_image_fg_signal.emit(-1, "")

    # 保存内参参数到本地
    @staticmethod
    def save_internal_file(result=None, internal_file_path=None, file_name="inter_cfg.json"):
        if not result:
            return
        if internal_file_path is None:
            internal_file_path = os.path.join(os.getcwd(), "result", str(int(time.time())))
        if not os.path.exists(internal_file_path):
            os.makedirs(internal_file_path)
        internal_file = os.path.join(internal_file_path, file_name)
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
            if self.check_internal_cfg(internal_file):
                self.show_message_signal.emit(True, "数据上传成功")
                self.reset_factory()
                return

        self.show_message_signal.emit(False, "数据上传失败")
        server.logout()

    def check_internal_cfg(self, local_internal_cfg_path):
        return True
        local_internal_cfg_name = local_internal_cfg_path.replace('\\', '/')
        with open(local_internal_cfg_name, 'r') as file:
            local_internal_cfg = json.load(file)

        if not local_internal_cfg:
            self.show_message_signal.emit(False, "获取设备本地内参文件失败:body")
            return False

        internal_cfg_info = server.get_internal_cfg()
        if not internal_cfg_info:
            self.show_message_signal.emit(False, "获取设备内参文件失败")
            return False
        internal_cfg = internal_cfg_info.get("body")
        if not internal_cfg:
            self.show_message_signal.emit(False, "获取设备内参文件失败:body")
            return False

        # 检查字典长度是否相等
        if len(local_internal_cfg) != len(internal_cfg):
            return False
        # 逐一比较字典中的键和值
        for key in local_internal_cfg.keys():
            if key not in internal_cfg:
                return False
            if not lists_equal(local_internal_cfg[key], internal_cfg[key]):
                return False

        return True

    # 重启设备
    def reset_factory(self):
        # self.reset_factory_mode()
        # self.reboot_device()
        # self.signal_reboot_device.emit()
        self.work_thread_state = False
        # hqtest self.show_message_signal.emit(True, "标定完成，等待设备重启后查看结果")
        self.show_message_signal.emit(True, "标定完成")
        # self.reboot_finish_signal.emit(2)
