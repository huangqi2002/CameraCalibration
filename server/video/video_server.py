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

        self.four_img_flag = {'middle_left': 0, 'left': 0, 'right': 0, 'middle_right': 0}
        self.camera_L_inter = app_model.config_internal.get("left_calib")
        self.camera_ML_inter = app_model.config_internal.get("mid_left_calib")
        self.camera_MR_inter = app_model.config_internal.get("mid_right_calib")
        self.camera_R_inter = app_model.config_internal.get("right_calib")

        self.winpos = -1

        self.fisheye_dll = ctypes.CDLL(path_fisheye_dll)

        ex_internal_data_path = app_model.config_ex_internal_path
        if ex_internal_data_path is None:
            ex_internal_data_path = os.path.join(os.getcwd(), "configs\\internal\\external_cfg.json")
        print(ex_internal_data_path)
        ex_internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_initialize(ex_internal_data_path)
        self.fisheye_dll.fisheye_external_initialize(ex_internal_data_path)
        app_model.config_ex_internal_path = ex_internal_data_path
        # self.bool_stop_get_frame = False

    # 将YUV420P转成cv::Mat格式

    def fisheye_ctrl(self, winpos):
        self.fisheye_dll.fisheye_set_winpos(winpos)

    def fisheye_internal_init(self, path):
        internal_data_path = path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_initialize(internal_data_path)

    def fisheye_external_init(self, path):
        external_data_path = path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_external_initialize(external_data_path)

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
        if m_global.m_connect_local:
            if int(time.time()) % 3 == 0:
                cv2.imwrite('output_image.jpg', stitch_image)
                print("保存成功")
        return stitch_image

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

                    camera.frame = frame
                    camera.frame_error_count = 0
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
            print("update_frame, Invalid camera or frame")
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
