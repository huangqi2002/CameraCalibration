#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import ctypes as C
import json
import os
import threading
import time

import cv2
import numpy as np
from PyQt5.QtCore import QObject
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from model.app import app_model
from model.camera import Camera
from server.aruco_vz import aruco_tool
from utils.run_para import m_global
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

        # 控制播放线程
        self.work_threads = None
        self.play_thread_mutex = None

        # 控制进程结束
        self.end_thread = False
        self.end_thread_event = threading.Event()

        # 展示连接相机个数
        self.camera_cnt = 0
        self.camera_cnt_lock = threading.Lock()  # 锁，用于保护计数器camera_cnt

        # 进行线程个数
        self.thread_cnt = 0
        self.thread_cnt_lock = threading.Lock()  # 锁，用于保护线程计数器thread_cnt

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
        # print(ex_internal_data_path)
        # ex_internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_internal_init(ex_internal_data_path)
        self.fisheye_external_init(ex_internal_data_path)
        app_model.config_ex_internal_path = ex_internal_data_path
        # self.bool_stop_get_frame = False

        aruco_tool.set_aruco_dictionary(5, 1000)
        aruco_tool.set_charuco_board((12, 9))

    # 将YUV420P转成cv::Mat格式
    def set_external(self, external_cfg):
        # print(external_cfg)
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
        app_model.config_ex_internal_path = path

    def fisheye_external_init(self, path):
        external_data_path = path.encode(encoding="utf-8", errors="ignore")
        self.fisheye_dll.fisheye_external_initialize(external_data_path)
        self.fisheye_ctrl(22)
        app_model.config_ex_internal_path = path

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

    def create(self, cameras: dict):
        # self.stop_get_frame()
        self.release()
        print("release OK")
        self.cameras = cameras
        # print(self.cameras)
        if not self.cameras:
            return

        self.work_threads = []
        self.play_thread_mutex = {}

        with self.thread_cnt_lock:
            self.thread_cnt = len(self.cameras)
        for direction, camera in self.cameras.items():
            pause = False
            # pause_cond = threading.Condition(threading.Lock())
            self.play_thread_mutex[direction] = [pause, threading.Condition(threading.Lock())]
            if direction == "stitch":
                play_thread = threading.Thread(target=self.get_frame_stitch, args=(direction, camera,))
            elif direction == "all":
                play_thread = threading.Thread(target=self.get_frame_all, args=(direction, camera,))
            else:
                play_thread = threading.Thread(target=self.get_frame, args=(direction, camera,))

            play_thread.start()
            self.work_threads.append(play_thread)
            print(f"{direction} Thread create successful")

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
        read_now = True
        # 判断传入的camera是否有效
        if camera is None or camera.rtsp_url is None:
            print("get_frame, Invalid camera or rtsp_url")
        else:
            try:
                connect = True
                # 连接成功开始拉视频流
                while True:
                    if connect:
                        # 连接 url 20次
                        print(f"start play:{camera.rtsp_url}\n")
                        open_ret = self.camera_connect(camera, 20)
                        if open_ret:
                            with self.camera_cnt_lock:
                                self.camera_cnt += 1
                                print(f"{camera.rtsp_url} is connected")
                                self.signal_cameraconnect_num.emit(self.camera_cnt)
                        else:
                            print(f"start play:{camera.rtsp_url} failed")
                            # with self.thread_cnt_lock:
                            #     self.thread_cnt -= 1
                            #     if self.thread_cnt == 0:
                            #         self.end_thread_event.set()
                            return

                        connect = False

                    # m_time = time.time()

                    # 是否暂停
                    if self.play_thread_mutex[direction][0]:
                        with self.play_thread_mutex[direction][1]:
                            # print(f"{direction} is wait {bool(self.play_thread_mutex[direction][0])}")
                            camera.cap.release()
                            with self.camera_cnt_lock:
                                self.camera_cnt -= 1
                                self.signal_cameraconnect_num.emit(self.camera_cnt)
                            while self.play_thread_mutex[direction][0]:
                                print(f"{direction} is wait {bool(self.play_thread_mutex[direction][0])}")
                                self.play_thread_mutex[direction][1].wait()
                            connect = True
                            print(f"{direction} is resume {not bool(self.play_thread_mutex[direction][0])}")

                    if self.end_thread:
                        print(f"{direction} is finished")
                        break

                    # 读取图片
                    # wait_time = time.time()
                    camera.cap.grab()
                    if read_now:
                        ret, frame = camera.cap.retrieve()
                        if self.camera_cnt != 1:
                            read_now = not read_now
                    else:
                        read_now = not read_now
                        time.sleep(0.05)
                        continue
                    # if direction == "left":
                    #     print(f"wait time 1 : {time.time() - wait_time}")
                    # wait_time = time.time()
                    # ret, frame = camera.cap.read()
                    # if direction == "left":
                    #     print(f"wait time 2 : {time.time() - wait_time}")

                    if not ret:
                        print(f"{direction} Failed to retrieve frame")
                        camera.frame_error_count += 1
                        if camera.frame_error_count >= camera.frame_time * 2:
                            print("Exceeded frame error count, exiting")
                            camera.frame_error_count = 0
                            break
                        time.sleep(camera.frame_time / 1000)
                        continue
                    camera.frame_error_count = 0

                    # 将读取到的frame写入相机中
                    # print(f"{direction} is read one frame {camera.frame_is_ok}")
                    if not camera.frame_is_ok:
                        # 判断是否需要去畸变
                        if not self.tab_index:
                            if self.undistorted_bool:
                                frame = self.undistorted_frame(frame, direction)
                        camera.frame = frame
                        camera.frame_is_ok = True
                        self.four_img_flag[direction] = 1

                    # if direction == "left":
                    #     print(f"total total total time : {time.time() - m_time}")
                    #     cacle_time += time.time() - m_time
                    #     cacle_count += 1
                    #     print(f"total time : {cacle_time / cacle_count}")
                    # time.sleep(0.05)

                if not connect:
                    with self.camera_cnt_lock:
                        self.camera_cnt -= 1
                        self.signal_cameraconnect_num.emit(self.camera_cnt)

                camera.cap.release()
                print(f"{camera.rtsp_url} is disconnected")

            except Exception as e:
                print(f"VideoCapture exception: {e}")

            with self.thread_cnt_lock:
                self.thread_cnt -= 1
                if self.thread_cnt == 0:
                    self.end_thread_event.set()

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

                rvecs_mat = np.eye(3)
                # if direction_str == "mid_left":
                #     rvecs_mat, _ = cv2.Rodrigues(
                #         np.array([[-0.013123657366832932], [-0.06304606961859559], [-0.014584278444963508]]))
                # else:
                #     rvecs_mat, _ = cv2.Rodrigues(
                #         np.array([[-0.05616745847617942], [0.399548833222927], [3.104362435588186]]))
                #     new_camera_matrix = np.multiply(camera_matrix, [[1, 1, 1], [1, 1, 1], [1, 1, 1]])
                # cv2.invert(rvecs_mat, rvecs_mat)

                # 畸变校正
                self.mapx[direction_str], self.mapy[direction_str] = cv2.initUndistortRectifyMap(camera_matrix,
                                                                                                 dist_coeffs,
                                                                                                 # np.eye(3),
                                                                                                 rvecs_mat,
                                                                                                 new_camera_matrix,
                                                                                                 new_size,
                                                                                                 cv2.CV_32FC1)
        ret_frame = cv2.remap(frame, self.mapx[direction_str], self.mapy[direction_str], cv2.INTER_LINEAR)
        return ret_frame

    def get_frame_stitch(self, direction, camera: Camera):
        # 输出连接信息
        print(f"start play:{direction}")
        with self.camera_cnt_lock:
            self.camera_cnt += 1
            self.signal_cameraconnect_num.emit(self.camera_cnt)
        print(f"{direction} is connected")

        # direction_list = ["middle_left", "left", "right", "middle_right"]
        direction_list = ["left", "right"]

        try:
            while True:
                # 是否暂停
                if self.play_thread_mutex[direction][0]:
                    with self.play_thread_mutex[direction][1]:
                        with self.camera_cnt_lock:
                            self.camera_cnt -= 1
                            self.signal_cameraconnect_num.emit(self.camera_cnt)
                        while self.play_thread_mutex[direction][0]:
                            self.play_thread_mutex[direction][1].wait()
                        with self.camera_cnt_lock:
                            self.camera_cnt += 1
                            self.signal_cameraconnect_num.emit(self.camera_cnt)
                # 是否终结
                if self.end_thread:
                    print(f"{direction} is finished")
                    break

                # 判断四张待拼接图像是否准备好
                four_img_ready = True
                for sig_direction in direction_list:
                    if self.four_img_flag[sig_direction] == 0:
                        four_img_ready = False
                        # print(f"start play:{sig_direction} {self.four_img_flag[sig_direction]}\n")
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
                camera.frame_error_count = 0

                # 拼接图片
                frame = self.four_img_stitch(self.cameras[direction_list[0]].frame,
                                             self.cameras[direction_list[1]].frame)
                self.cameras[direction_list[0]].frame_is_ok = False
                self.cameras[direction_list[1]].frame_is_ok = False

                # 将读取到的frame写入相机中
                if not camera.frame_is_ok:
                    camera.frame = frame.copy()
                    # print(f"camera.frame is {camera.frame is None}")
                    camera.frame_is_ok = True
                    self.four_img_flag[direction] = 1

                time.sleep(0.11)

            with self.camera_cnt_lock:
                self.camera_cnt -= 1
                self.signal_cameraconnect_num.emit(self.camera_cnt)
            # camera.cap.release()
            print(f"{camera.rtsp_url} is disconnected")

        except Exception as e:
            print(f"VideoCapture exception: {e}")

        with self.thread_cnt_lock:
            self.thread_cnt -= 1
            if self.thread_cnt == 0:
                self.end_thread_event.set()

    def four_img_all(self, frame_0, frame_1, frame_2, frame_3):
        width = 1200
        height = 800

        # img_0 = frame_0.copy()
        img_0 = cv2.rotate(frame_0, cv2.ROTATE_90_COUNTERCLOCKWISE)
        img_0 = cv2.resize(img_0, (width, height))

        # img_1 = frame_1.copy()
        img_1 = cv2.rotate(frame_1, cv2.ROTATE_90_COUNTERCLOCKWISE)
        img_1 = cv2.resize(img_1, (width, height))

        # img_2 = frame_2.copy()
        img_2 = cv2.rotate(frame_2, cv2.ROTATE_90_CLOCKWISE)
        img_2 = cv2.resize(img_2, (width, height))

        # img_3 = frame_3.copy()
        img_3 = cv2.rotate(frame_3, cv2.ROTATE_90_CLOCKWISE)
        img_3 = cv2.resize(img_3, (width, height))

        img_separate = np.ones((height, 10, 3), dtype=np.uint8)
        img_separate[:, :, 0] = 74
        img_separate[:, :, 1] = 67
        img_separate[:, :, 2] = 64

        # 合成一张大图像
        # top_row = np.hstack((img_0, img_1))
        # bottom_row = np.hstack((img_2, img_3))
        # result_image = np.vstack((top_row, bottom_row))
        result_image = np.hstack((img_0, img_separate, img_1, img_separate, img_2, img_separate, img_3))
        # left_col = np.vstack((img_0, img_1))
        # right_col = np.vstack((img_3, img_2))
        # result_image = np.hstack((left_col, right_col))

        return result_image

    def get_frame_all(self, direction, camera: Camera):
        # 输出连接信息
        print(f"start play:{direction}")
        with self.camera_cnt_lock:
            self.camera_cnt += 1
            self.signal_cameraconnect_num.emit(self.camera_cnt)
        print(f"{direction} is connected")

        direction_list = ["middle_left", "left", "right", "middle_right"]

        try:
            while True:
                # 是否暂停
                if self.play_thread_mutex[direction][0]:
                    with self.play_thread_mutex[direction][1]:
                        with self.camera_cnt_lock:
                            self.camera_cnt -= 1
                            self.signal_cameraconnect_num.emit(self.camera_cnt)
                        while self.play_thread_mutex[direction][0]:
                            self.play_thread_mutex[direction][1].wait()
                        with self.camera_cnt_lock:
                            self.camera_cnt += 1
                            self.signal_cameraconnect_num.emit(self.camera_cnt)
                # 是否终结
                if self.end_thread:
                    print(f"{direction} is finished")
                    break
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
                camera.frame_error_count = 0
                # 拼接图片
                frame = self.four_img_all(self.cameras[direction_list[0]].frame,
                                          self.cameras[direction_list[1]].frame,
                                          self.cameras[direction_list[2]].frame,
                                          self.cameras[direction_list[3]].frame)
                self.cameras[direction_list[0]].frame_is_ok = False
                self.cameras[direction_list[1]].frame_is_ok = False
                self.cameras[direction_list[2]].frame_is_ok = False
                self.cameras[direction_list[3]].frame_is_ok = False

                # 将读取到的frame写入相机中
                if not camera.frame_is_ok:
                    camera.frame = frame.copy()
                    # print(f"{camera}camera.frame is {camera.frame is None}")
                    camera.frame_is_ok = True
                    self.four_img_flag[direction] = 1

                time.sleep(0.11)

            with self.camera_cnt_lock:
                self.camera_cnt -= 1
                self.signal_cameraconnect_num.emit(self.camera_cnt)
            # camera.cap.release()
            print(f"{camera.rtsp_url} is disconnected")

        except Exception as e:
            print(f"VideoCapture exception: {e}")

        with self.thread_cnt_lock:
            self.thread_cnt -= 1
            if self.thread_cnt == 0:
                self.end_thread_event.set()

    @staticmethod
    def update_frame(camera):
        print("update_frame")
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

        self.resume_all()
        self.end_thread = True
        if self.thread_cnt != 0:
            self.end_thread_event.wait()
            self.end_thread_event.clear()
        self.end_thread = False
        for direction in self.four_img_flag.keys():
            self.four_img_flag[direction] = 0
        self.signal_cameraconnect_num.emit(self.camera_cnt)
