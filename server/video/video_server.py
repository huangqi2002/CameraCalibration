#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import threading
from functools import partial

import cv2
import time
from PyQt5.QtCore import pyqtSignal

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel

from model.camera import Camera
from utils.m_global import m_connect_local
from PyQt5.QtCore import QObject


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
        # self.bool_stop_get_frame = False

    # def stop_get_frame(self):
    #     if not self.camera_cnt:
    #         return
    #     self.frame_stop_cond.acquire()
    #     self.bool_stop_get_frame = True
    #     while len(self.work_threads) != 0:
    #         self.frame_stop_cond.wait()
    #     self.frame_stop_cond.release()

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
            play_thread = threading.Thread(target=self.get_frame, args=(direction, camera,))
            play_thread.start()
            self.work_threads.append(play_thread)
            print(f"{direction} Thread craete successful")
        self.work_threads_mutex.release()

    def get_cameras(self):
        return self.cameras

    def save_frame(self, direction, filename):
        if self.cameras is None:
            return
        camera = self.cameras.get(direction)
        frame = camera.frame
        if frame is not None:
            cv2.imwrite(filename, frame)

    def pause(self, direction: str = None):
        if not self.play_thread_mutex:
            return
        if direction in self.play_thread_mutex:
            if self.play_thread_mutex[direction][0]:
                return
            with self.play_thread_mutex[direction][1]:
                self.play_thread_mutex[direction][0] = True
            print(f"{direction} is pause")

    def pause_all(self):
        for direction, camera in self.cameras.items():
            self.pause(direction)

    def resume(self, direction: str = None):
        if not self.play_thread_mutex:
            return
        if not self.play_thread_mutex[direction][0]:
            return
        if direction in self.play_thread_mutex:
            with self.play_thread_mutex[direction][1]:
                self.play_thread_mutex[direction][0] = False
                self.play_thread_mutex[direction][1].notify()  # 唤醒线程
                print(f"{direction} is resume notify")

    def resume_all(self):
        for direction, camera in self.cameras.items():
            self.resume(direction)

    # @staticmethod
    def get_frame(self, direction, camera: Camera):
        if camera is None or camera.rtsp_url is None:
            print("get_frame, Invalid camera or rtsp_url")

        else:
            try:
                print(f"start play:{camera.rtsp_url}")
                open_ret = 0
                open_count = 0
                while not open_ret:
                    if m_connect_local:
                        camera.cap = cv2.VideoCapture("111.mp4")
                    else:
                        camera.cap = cv2.VideoCapture(camera.rtsp_url)
                    open_ret = camera.cap.isOpened()
                    open_count += 1
                    if open_count == 20:
                        break
                if open_ret:
                    # print(f"start play:{camera.rtsp_url} OK")
                    self.camera_cnt += 1
                    print(f"{camera.rtsp_url} is connected")
                    self.signal_cameraconnect_num.emit(self.camera_cnt)

                else:
                    print(f"start play:{camera.rtsp_url} failed")
                # camera.cap = cv2.VideoCapture("111.jpg")
                while camera.cap.isOpened() and camera.is_open:
                    # print(f"{direction} 0")
                    # if threading.currentThread().getName()=='Thread-9':
                    #     print("Thread-9")
                    with self.play_thread_mutex[direction][1]:
                        # print(f"{direction} 1 {self.play_thread_mutex[direction][0]}")
                        while self.play_thread_mutex[direction][0]:
                            self.play_thread_mutex[direction][1].wait()  # 等待被唤醒
                            print(f"{direction} is resume")

                    # fps = cap.get(cv2.CAP_PROP_FPS)
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

                    print(threading.currentThread().getName(), "Get Frame", camera.rtsp_url)
                    camera.frame = frame
                    camera.frame_error_count = 0
                    time.sleep(camera.frame_time / 1000)

                self.camera_cnt -= 1
                print(f"{camera.rtsp_url} is disconnected")
                self.signal_cameraconnect_num.emit(self.camera_cnt)
                if camera.is_open:
                    camera.cap.release()
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
        self.resume_all()
        for key, camera in self.cameras.items():
            camera.is_open = False
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
