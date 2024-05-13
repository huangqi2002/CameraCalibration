#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import threading
from functools import partial
import ctypes as C
import cv2
import time
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel

from model.camera import Camera
from utils import m_global
from PyQt5.QtCore import QObject
from multiprocessing import Process
import numpy as np
from model.app import app_model
import time
import os
import json
from server.aruco_vz import aruco_tool

path_root = os.getcwd()
path_fisheye_dll = os.path.join(path_root, "lib3rd", "fisheye", "video_fuse.dll")


class VideoServer(QObject):
    signal_cameraconnect_num = pyqtSignal(int)
    frame_stop_cond = threading.Condition()
    work_threads_mutex = threading.Lock()
    camera_connect_mutex = threading.Lock()

    def __init__(self):
        super().__init__()
        self.cameras = None
        self.work_threads = None
        self.play_thread_mutex = None
        self.camera_cnt = 0
        self.undistorted_bool = False  # 内参展示界面是否去畸变

        self.four_img_flag = {'middle_left': 0, 'left': 0, 'right': 0, 'middle_right': 0}
        # self.camera_L_inter = app_model.config_internal.get("left_calib")
        # self.camera_ML_inter = app_model.config_internal.get("mid_left_calib")
        # self.camera_MR_inter = app_model.config_internal.get("mid_right_calib")
        # self.camera_R_inter = app_model.config_internal.get("right_calib")

        self.winpos = -1
        self.depth = 1.0
        self.tab_index = None
        self.mapx = {}
        self.mapy = {}
        self.internal_data = None

        self.fisheye_dll = ctypes.CDLL(path_fisheye_dll)

        ex_internal_data_path = app_model.config_ex_internal_path
        if ex_internal_data_path is None:
            ex_internal_data_path = os.path.join(os.getcwd(), "configs\\internal\\external_cfg.json")
        print(ex_internal_data_path)
        # ex_internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_internal_init(ex_internal_data_path)
        self.fisheye_external_init(ex_internal_data_path)
        app_model.config_ex_internal_path = ex_internal_data_path
        # self.bool_stop_get_frame = False

        aruco_tool.set_aruco_dictionary(5, 1000)
        aruco_tool.set_charuco_board((12, 9))

    # 将YUV420P转成cv::Mat格式
    def set_external(self, external_cfg):
        print(external_cfg)
        external_cfg_str = json.dumps(external_cfg)
        external_cfg_str = external_cfg_str.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_init_network(external_cfg_str)

    def fisheye_ctrl(self, winpos):
        self.fisheye_dll.fisheye_set_winpos(winpos)

    def set_undistorted_bool(self, var):
        self.undistorted_bool = var

    def fisheye_depth_set(self, depth):
        self.depth = depth

        move = 1.0
        if depth == 10:
            move = 0.0
        self.fisheye_dll.set_deep_tvec_multiple(ctypes.c_double(depth), ctypes.c_double(move))
        self.fisheye_dll.fisheye_set_winpos(20)

    def fisheye_internal_init(self, path):
        internal_data_path = path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_initialize(internal_data_path)
        with open(path, encoding="utf-8", errors="ignore") as f:
            self.internal_data = json.load(f)
        self.mapx = {}
        self.mapy = {}
        self.fisheye_ctrl(22)

    def fisheye_external_init(self, path):
        external_data_path = path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_external_initialize(external_data_path)
        self.fisheye_ctrl(22)


    def four_img_stitch(self, frame_1, frame_2):
        if frame_1 is None or frame_2 is None:
            # print("frame is None")
            time.sleep(0.01)
            return

        # cv2.imshow("1", cv2.resize(frame_1, (400, 300)))
        # cv2.imshow("2", cv2.resize(frame_2, (400, 300)))
        # cv2.imshow("3", cv2.resize(frame_3, (400, 300)))
        # cv2.imshow("4", cv2.resize(frame_4, (400, 300)))
        # cv2.waitKey(0)
        if m_global.m_connect_local:
            frame_1 = cv2.imread("m_data/hqtest/ex_L.jpg")
            frame_2 = cv2.imread("m_data/hqtest/ex_R.jpg")

        height = 1200
        width = 1600

        self.fisheye_dll.fisheye_run_yuv.restype = ctypes.c_char_p

        stitch_image = np.zeros(dtype=np.uint8, shape=(height, width, 3))

        self.fisheye_dll.fisheye_run_yuv(frame_1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                         , frame_2.ctypes.data_as(C.POINTER(C.c_ubyte))
                                         , stitch_image.ctypes.data_as(C.POINTER(C.c_ubyte)))
        if m_global.m_global_debug:
            if int(time.time()) % 3 == 0:
                cv2.imwrite('output_image.jpg', stitch_image)
                print("保存成功")
        #
        # stitch_image = cv2.rotate(stitch_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # stitch_image = self.stitch_crop(stitch_image)

        return stitch_image

    def stitch_crop(self, image):
        # 将图像转换为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 二值化图像
        ret, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        # 寻找轮廓
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 找到最大的轮廓
        max_contour = max(contours, key=cv2.contourArea)

        # 计算最小边界框
        rect = cv2.minAreaRect(max_contour)
        box = cv2.boxPoints(rect)
        box = np.int0(box)
        # 提取最小边界框的坐标
        x, y, w, h = cv2.boundingRect(box)
        # print(x, y, w, h)
        # 截取图像
        cropped_image = image[y:y + h, x:x + w]
        return cropped_image

    def create(self, cameras: dict):
        # self.stop_get_frame()
        self.release()
        print("release OK")
        self.cameras = cameras
        if not self.cameras:
            return

        self.work_threads = []
        self.play_thread_mutex = {}

        self.work_threads_mutex.acquire()
        for direction, camera in self.cameras.items():
            paused = True
            # pause_cond = threading.Condition(threading.Lock())
            self.play_thread_mutex[direction] = [paused, threading.Condition(threading.Lock())]
            camera.is_open = True
            if direction == "stitch":
                play_thread = threading.Thread(target=self.get_frame_stitch, args=(direction, camera,))
            else:
                play_thread = threading.Thread(target=self.get_frame, args=(direction, camera,))
            play_thread.start()
            self.work_threads.append(play_thread)
            print(f"{direction} Thread create successful")
        self.work_threads_mutex.release()

    def get_cameras(self):
        return self.cameras

    def save_frame(self, direction, filename, rotate=False):
        if self.cameras is None:
            return -1
        camera = self.cameras.get(direction)
        frame = camera.frame
        if filename is None:
            return -1
        if frame is not None:
            if rotate:
                rotated_frame = cv2.rotate(frame, cv2.ROTATE_180)
                cv2.imwrite(filename, rotated_frame)
            else:
                cv2.imwrite(filename, frame)
            return 0
        return -1

    def camera_state(self, direction):
        if self.cameras is None:
            return False
        camera = self.cameras.get(direction)
        if not (camera.cap.isOpened() and camera.is_open):
            return False
        return True

    def pause(self, direction: str = None):
        if not self.play_thread_mutex:
            return
        if direction in self.play_thread_mutex:
            if self.play_thread_mutex[direction][0]:
                return
            with self.play_thread_mutex[direction][1]:
                self.play_thread_mutex[direction][0] = True
            # print(f"{direction} is pause")

    def pause_all(self):
        for direction, camera in self.cameras.items():
            self.pause(direction)

    def resume(self, direction: str = None):
        if not self.play_thread_mutex:
            return
        if direction in self.play_thread_mutex:
            if not self.play_thread_mutex[direction][0]:
                return
            with self.play_thread_mutex[direction][1]:
                self.play_thread_mutex[direction][0] = False
                self.play_thread_mutex[direction][1].notify()  # 唤醒线程
                print(f"{direction} is resume notify")

    def resume_all(self):
        for direction, camera in self.cameras.items():
            self.resume(direction)

    def camera_connect(self, camera: Camera, num):
        open_count = 0
        open_ret = False
        while not open_ret:
            camera.cap = cv2.VideoCapture(camera.rtsp_url)
            open_ret = camera.cap.isOpened()
            open_count += 1
            if open_count == num:
                break
        return open_ret

    # @staticmethod
    def get_frame(self, direction, camera: Camera):
        if camera is None or camera.rtsp_url is None:
            print("get_frame, Invalid camera or rtsp_url")

        else:
            try:
                cap_can_release = False
                print(f"start play:{camera.rtsp_url}\n")
                open_ret = self.camera_connect(camera, 20)
                if open_ret:
                    cap_can_release = True
                    self.camera_cnt += 1
                    print(f"{camera.rtsp_url} is connected")
                    self.signal_cameraconnect_num.emit(self.camera_cnt)

                else:
                    print(f"start play:{camera.rtsp_url} failed")

                while camera.cap.isOpened() and camera.is_open:
                    # 判断线程是否被终止
                    with self.play_thread_mutex[direction][1]:
                        while self.play_thread_mutex[direction][0]:
                            print(f"{direction} is stop\n")
                            if camera.is_open:
                                camera.cap.release()
                                cap_can_release = False
                            self.play_thread_mutex[direction][1].wait()  # 等待被唤醒
                            print(f"{direction} is resumeing")
                            open_ret = False
                            if camera.is_open and not self.play_thread_mutex[direction][0]:  # 如果不是因为要终止线程而发出的唤醒信号
                                open_ret = self.camera_connect(camera, 20)
                                if open_ret:
                                    cap_can_release = True
                                    print(f"{direction} is resume")

                        if not open_ret:
                            print(f"start play:{camera.rtsp_url} failed")
                            break
                    ret, frame = camera.cap.read()
                    if not ret:
                        print(f"{direction} Failed to retrieve frame")
                        camera.frame_error_count += 1
                        if camera.frame_error_count >= camera.frame_time * 5:
                            print("Exceeded frame error count, exiting")
                            camera.frame_error_count = 0
                            break
                        time.sleep(camera.frame_time / 1000)
                        continue

                    # 判断是否需要去畸变
                    if not self.tab_index:
                        # objPoints, imgPoints = aruco_tool.charuco_detect(frame, True)
                        # print(f"objPoints : {objPoints}\nimgPoints : {imgPoints}")
                        if self.undistorted_bool:
                            frame = self.undistorted_frame(frame, direction)

                    camera.frame = frame
                    camera.frame_error_count = 0
                    camera.frame_is_ok = True
                    self.four_img_flag[direction] = 1

                self.camera_cnt -= 1
                self.signal_cameraconnect_num.emit(self.camera_cnt)
                if cap_can_release:
                    camera.cap.release()
                print(f"{camera.rtsp_url} is disconnected")
            except Exception as e:
                print(f"VideoCapture exception: {e}")

        current_thread = threading.current_thread()
        self.work_threads_mutex.acquire()
        if current_thread in self.work_threads:
            self.work_threads.remove(current_thread)
        self.work_threads_mutex.release()
        if len(self.work_threads) == 0:
            print(f"finnal")
            self.frame_stop_cond.acquire()
            print("self.frame_stop_cond.notify_all()")
            self.frame_stop_cond.notify_all()
            self.frame_stop_cond.release()

    def undistorted_frame(self, frame, direction):
        direction_str = direction.replace("middle", "mid")
        if self.internal_data is None:
            return frame
        # ret_frame = frame
        # direct_dict = {"left": "L", "right": "R", "mid_left": "ML", "mid_right": "MR"}
        # frame = cv2.imread("m_data/hqtest/bf_1/in_" + direct_dict[direction_str] + ".jpg")
        if direction_str not in self.mapx:

            camera_inter = self.internal_data.get(direction_str + "_calib")
            # 内参和畸变参数
            intrinsics = camera_inter[2:11]
            dist_coeffs = np.array(camera_inter[11:])
            # 获取图像尺寸
            h, w = frame.shape[:2]
            # 相机矩阵
            camera_matrix = np.reshape(intrinsics[:9], (3, 3))

            if direction_str == "left" or direction_str == "right":
                # 生成图像尺寸
                new_size = (w * 2, h * 2)
                # 生成相机矩阵
                new_camera_matrix = np.multiply(camera_matrix, [[1, 1, 2], [1, 1, 2], [1, 1, 1]])

                # 畸变校正
                self.mapx[direction_str], self.mapy[direction_str] = cv2.fisheye.initUndistortRectifyMap(camera_matrix,
                                                                                                         dist_coeffs,
                                                                                                         np.eye(3),
                                                                                                         new_camera_matrix,
                                                                                                         new_size,
                                                                                                         cv2.CV_32FC1)

            else:
                # 生成图像尺寸
                new_size = (w, h)
                # 生成相机矩阵
                new_camera_matrix = np.multiply(camera_matrix, [[1, 1, 1], [1, 1, 1], [1, 1, 1]])

                # 畸变校正
                self.mapx[direction_str], self.mapy[direction_str] = cv2.initUndistortRectifyMap(camera_matrix,
                                                                                                 dist_coeffs,
                                                                                                 np.eye(3),
                                                                                                 new_camera_matrix,
                                                                                                 new_size,
                                                                                                 cv2.CV_32FC1)
        ret_frame = cv2.remap(frame, self.mapx[direction_str], self.mapy[direction_str], cv2.INTER_LINEAR)
        return ret_frame

    def get_frame_stitch(self, direction, camera: Camera):
        # 输出连接信息
        print(f"start play:{camera.rtsp_url}\n")
        self.camera_cnt += 1
        print(f"{camera.rtsp_url} is connected")
        self.signal_cameraconnect_num.emit(self.camera_cnt)
        # direction_list = ["middle_left", "left", "right", "middle_right"]
        direction_list = ["left", "right"]

        while camera.is_open:

            # 判断线程是否被终止
            with self.play_thread_mutex[direction][1]:
                # print(f"{direction} 1 {self.play_thread_mutex[direction][0]}")
                while self.play_thread_mutex[direction][0]:
                    print(f"{direction} fg is stop\n")
                    self.play_thread_mutex[direction][1].wait()  # 等待被唤醒
                    print(f"{direction} fg is resumeing")

            # 判断四张待拼接图像是否准备好
            four_img_ready = True
            for sig_direction in direction_list:
                if self.four_img_flag[sig_direction] == 0:
                    four_img_ready = False
                    break
            if four_img_ready is False:
                # print(f"{direction} fg Failed to get frame")
                camera.frame_error_count += 1
                if camera.frame_error_count >= camera.frame_time * 5:
                    print("Exceeded frame error count, exiting")
                    camera.frame_error_count = 0
                    break
                time.sleep(camera.frame_time / 1000)
                continue

            frame = self.four_img_stitch(self.cameras[direction_list[0]].frame,
                                         self.cameras[direction_list[1]].frame)
            camera.frame = frame
            camera.frame_error_count = 0
            camera.frame_is_ok = True

        print(f"{camera.rtsp_url} is disconnected")

        current_thread = threading.current_thread()
        self.work_threads_mutex.acquire()
        if current_thread in self.work_threads:
            self.work_threads.remove(current_thread)
        self.work_threads_mutex.release()
        self.camera_cnt -= 1
        self.signal_cameraconnect_num.emit(self.camera_cnt)
        if len(self.work_threads) == 0:
            print(f"finnal")
            self.frame_stop_cond.acquire()
            print("self.frame_stop_cond.notify_all()")
            self.frame_stop_cond.notify_all()
            self.frame_stop_cond.release()

    # def camera_bind_label_and_timer(self, direction: str, rotate: int, label: QLabel, timer: QTimer):
    #     if not label or not direction:
    #         return
    #     if not label.isVisible():
    #         return
    #     if self.cameras is None:
    #         return
    #     camera = self.cameras.get(direction)
    #     if not camera:
    #         return
    #     camera.rotate = rotate
    #     camera.label = label
    #
    #     if camera.timer is not None:
    #         camera.timer.stop()
    #     camera.timer = timer
    #     camera.timer.timeout.connect(partial(self.update_frame, camera))

    @staticmethod
    def update_frame(camera):
        if camera is None or camera.frame is None:
            # print("update_frame, Invalid camera or frame")
            return
        label_size = camera.label.size()
        # print("update_frame, label_size", label_size)
        frame_rotated = None
        if camera.rotate == 0:
            frame_resized = cv2.resize(camera.frame, (label_size.width(), label_size.height() - 1))
            frame_rotated = frame_resized
        else:
            frame_resized = cv2.resize(camera.frame, (label_size.height() - 1, label_size.width()))
            # print("update_frame, frame_resized", frame_resized.shape)
            if camera.rotate == 90:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_90_CLOCKWISE)
            elif camera.rotate == 180:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_180)
            elif camera.rotate == 270:
                frame_rotated = cv2.rotate(frame_resized, cv2.ROTATE_90_COUNTERCLOCKWISE)

        frame_rgb = cv2.cvtColor(frame_rotated, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        q_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        camera.label.setPixmap(pixmap)

    def parse(self, direction: str = None):
        if not self.cameras:
            return
        if direction is None:
            for key, camera in self.cameras.items():
                if camera.timer:
                    camera.timer.stop()
            return
        camera = self.cameras.get(direction)
        if not camera:
            return
        camera.timer.stop()

    def start(self, direction: str = None):
        if not self.cameras:
            return
        if direction is None:
            for key, camera in self.cameras.items():
                if camera.timer:
                    camera.timer.start(camera.frame_time)
            return
        camera = self.cameras.get(direction)
        if not camera:
            return
        camera.timer.start(camera.frame_time)

    def release(self):
        if not self.cameras:
            return
        if not self.work_threads:
            return
        for key, camera in self.cameras.items():
            camera.is_open = False
        self.resume_all()
        self.frame_stop_cond.acquire()
        while len(self.work_threads) != 0:
            self.frame_stop_cond.wait()
        self.frame_stop_cond.release()
        self.cameras.clear()
        self.cameras = None

        # if not self.work_threads:
        #     return
        # for work_thread in self.work_threads:
        #     if work_thread.isRunning():
        #         work_thread.quit()
        self.work_threads_mutex.acquire()
        self.work_threads.clear()
        self.work_threads = None
        self.work_threads_mutex.release()
        self.camera_cnt = 0
        for direction in self.four_img_flag.keys():
            self.four_img_flag[direction] = 0
        self.signal_cameraconnect_num.emit(self.camera_cnt)
