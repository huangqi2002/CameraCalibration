#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import json
import os
import shutil
import threading
from functools import partial

import cv2
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel

from controller.controller_base_tab import BaseControllerTab, lists_equal, calibrate_para_gen
from model.app import app_model
from server.aruco_vz import aruco_tool
from server.camera_calib import Camera_Cali
from server.external.ex_Calib import ex_calib
from server.internal.boardSplit import getBoardPosition
from server.internal.internal_server import *
from server.web.web_server import *

from utils.run_para import m_global


class InternalCalibrationController(BaseControllerTab):
    video_map = {}
    internal_data_path: str = None
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
    one_click_thread_event = None
    one_click_thread = None
    direction_list = None
    chessboard = None
    calib_parameter = None
    camera_cali = None

    def __init__(self, base_view, base_model=None):
        super().__init__(base_view, base_model)

    def init(self):
        self.tab_index = 0

        # 一键标定
        self.view.pushButton_start.clicked.connect(self.on_start)

        # 控件初始化
        self.view.undistorted_checkBox.setChecked(False)
        self.view.clarity_checkBox.setChecked(False)

        # 链接UI事件
        self.view.undistorted_checkBox.stateChanged.connect(self.undistorted)
        self.view.clarity_checkBox.stateChanged.connect(self.clarity_test)

        self.view.pushButton_play_1.clicked.connect(self.position_play)
        self.view.pushButton_play_2.clicked.connect(self.position_play)
        self.view.pushButton_play_3.clicked.connect(self.position_play)
        self.view.pushButton_play_4.clicked.connect(self.position_play)
        self.view.pushButton_play_5.clicked.connect(self.position_play)

        self.show_image_signal.connect(self.on_show_image)
        self.show_image_fg_signal.connect(self.on_show_image_fg)
        self.work_thread_finish_success_signal.connect(self.on_work_thread_finish_success)
        self.work_thread_finish_failed_signal.connect(self.on_work_thread_finish_failed)

        # 绑定配置文件中的相机与去显示的lable
        # app_model.camera_list
        self.bind_label_and_timer("left", self.view.label_video_fg, 0)  # 270)
        self.view.set_position_type_button_enable(self.position_index)
        # self.bind_label_and_timer("middle_left", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("middle_right", self.view.label_video_fg, 270)
        # self.bind_label_and_timer("right", self.view.label_video_fg, 270)

        self.direction_list = ["left", "middle_left", "middle_right", "right", "all"]

        self.dirct_trans = {"L": "left", "ML": "mid_left", "MR": "mid_right", "R": "right", "left": "L",
                            "mid_left": "ML", "mid_right": "MR", "right": "R"}
        self.clarity_lable = {"left": self.view.clarity_label_L, "middle_left": self.view.clarity_label_ML,
                              "middle_right": self.view.clarity_label_MR, "right": self.view.clarity_label_R}

        # 控制一键标定进程
        self.one_click_thread = False
        self.one_click_thread_event = threading.Event()

        # 角点
        self.chessboard = {}
        # 标定参数
        self.calib_parameter = {}
        self.camera_cali = Camera_Cali()

    # 切换设备类型
    def on_change_device_type(self, device_type):
        self.device_type = device_type
        self.view.pushButton_type_change(device_type)
        # if device_type == "FG":
        # self.view.set_layout_fg(True)
        # self.view.set_layout_rx5(False)
        # else:
        # self.view.set_layout_fg(False)
        # self.view.set_layout_rx5(True)

    # 一键标定槽函数
    def on_start(self):
        if self.view.position_type_text[self.position_index] != "全视野":
            return

        self.view.set_start_button_enable(False)

        # 创建目录
        sn = app_model.device_model.sn
        if not sn:
            self.log.log_err("sn获取失败")
            self.view.set_start_button_enable(True)
            return

        internal_data_path = os.path.join(app_model.work_path_internal, sn)
        # 第一次截图之前已经存在，则删除文件夹
        if self.screenshot_count == 0:
            self.create_path_new(internal_data_path)
        self.internal_data_path = internal_data_path

        if not self.internal_data_path:
            self.view.set_start_button_enable(True)
            return

        if self.work_thread_state:
            self.view.set_start_button_enable(True)
            return

        self.work_thread_state = True
        # 创建线程执行任务
        self.view.undistorted_checkBox.setChecked(False)
        # self.view.clarity_checkBox.setChecked(False)
        self.work_thread = threading.Thread(target=self.one_click_calibration, daemon=True)
        self.work_thread.start()

    def get_chessboard(self):
        self.chessboard = {}
        path_name_list = ["L", "ML", "MR", "R"]

        for position_index in range(len(path_name_list)):
            camera_type = "fisheye"
            if path_name_list[position_index][0] == "M":
                camera_type = "normal"

            filename = f"chessboard_{path_name_list[position_index]}.jpg"

            pic_path = os.path.join(self.internal_data_path, path_name_list[position_index], filename)
            if not os.path.exists(pic_path):
                print(f"{pic_path} is not exists")
                return False

            img = cv2.imread(pic_path)
            ok, obj_point_list, img_point_list, id_dict = self.get_aruco_corners(img, f"result/{filename}")

            if not ok:
                print(f"{filename} find error")
                self.show_message_signal.emit(False, f"{filename} chessboard find error")
                return False

            chessboard_dict = {"obj_point_list": obj_point_list, "img_point_list": img_point_list,
                               "id_dict": id_dict, "frame_size": img.shape[1::-1], "camera_type": camera_type}
            self.chessboard[f"{path_name_list[position_index]}"] = chessboard_dict
            self.show_message_signal.emit(True, f"{filename} chessboard find success")
        return True

    def get_aruco_corners(self, img, save_path=None):
        ok, obj_point_list, img_point_list, id_dict = False, None, None, None
        # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        ret_img_bool = False
        if save_path is not None:
            ret_img_bool = True

        objPoints, imgPoints, charucoIds, ret_img = aruco_tool.charuco_detect(img, ret_img_bool)

        # 亚像素级别的角点优化
        # criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 1000, 1e-6)
        # imgPoints = cv2.cornerSubPix(gray, imgPoints, (21, 21), (-1, -1), criteria)

        if objPoints is None:
            return ok, obj_point_list, img_point_list, id_dict

        threshold = m_global.bW * (m_global.bH + 1 + m_global.bSpacer)
        # 初始化一个列表来存储bNum个组
        temp_obj_point_list = [np.empty((0, 1, 3)) for _ in range(m_global.bNum)]
        temp_img_point_list = [np.empty((0, 1, 2)) for _ in range(m_global.bNum)]
        temp_id_dict = {i: [] for i in range(m_global.bNum)}

        # 将 objPoints 和 charucoIds 进行 zip，得到每个点对应的 charucoId
        points_with_charuco_ids = zip(objPoints, imgPoints, charucoIds)

        # 分组并筛选出满足条件的非空组
        begin_point = np.array([0, (m_global.bH + m_global.bSpacer + 1) * 0.25, 0])

        for obj_point, img_point, ids in points_with_charuco_ids:
            if ids is not None and 0 <= ids[0] < threshold * m_global.bNum:
                temp_ids = ids[0] // threshold
                temp_obj_point_list[temp_ids] = np.vstack([temp_obj_point_list[temp_ids], (
                        (obj_point[0] - begin_point * temp_ids).reshape(1, 1, -1) / 0.25 * m_global.bSize)])
                temp_img_point_list[temp_ids] = np.vstack(
                    [temp_img_point_list[temp_ids], img_point[0].reshape(1, 1, -1)])

                temp_id_dict[temp_ids].append(ids[0])

        # 过滤掉为空的组
        obj_point_list = [arr.astype(np.float32) for arr in temp_obj_point_list if arr.size > 12 * 3]
        img_point_list = [arr.astype(np.float32) for arr in temp_img_point_list if arr.size > 12 * 2]
        id_dict = {index: id_list for index, id_list in temp_id_dict.items() if len(id_list) > 12}

        if ret_img_bool:
            # temp_img = cv2.resize(ret_img, (800, 600))
            # cv2.imshow("ret_img", temp_img)
            # cv2.waitKey(0)
            cv2.imwrite(save_path, ret_img)

        if len(obj_point_list) > 0:
            ok = True
        return ok, obj_point_list, img_point_list, id_dict

    # 一键标定
    def one_click_calibration(self):
        self.calib_parameter = {}
        # 截图
        ret = self.save_frame_all()
        if ret != 0:
            self.view.set_start_button_enable(True)
            self.work_thread_state = False
            return

        # 找角点
        if not self.get_chessboard():
            print("角点寻找失败")
            self.show_message_signal.emit(False, "角点寻找失败")
            self.view.set_start_button_enable(True)
            self.work_thread_state = False
            return

        # 标定内参
        if not self.create_path_and_cali_in():
            print("内参标定失败")
            self.view.set_start_button_enable(True)
            self.work_thread_state = False
            return

        # 标定外参
        # if not self.one_click_thread:
        #     self.view.set_start_button_enable(True)
        #     return
        print("\n开始标定外参")
        # 标定外参
        self.create_path_and_cali_ex(self.internal_data_path)
        # self.cali_ex_cfg()

    # 保存所有图像
    def save_frame_all(self):
        path_name_list = ["L", "ML", "MR", "R"]
        for position_index in range(len(path_name_list)):
            # 创建截图保存路径，存在则清空并重新创建
            internal_data_path = os.path.join(self.internal_data_path, path_name_list[position_index])
            # print(f"\n{internal_data_path}\n")
            self.create_path_new(internal_data_path)

            # 保存截图
            filename = f"chessboard_{path_name_list[position_index]}.jpg"
            pic_path = os.path.join(internal_data_path, filename)
            # 读取文件并保存
            if m_global.m_connect_local:
                try:
                    if path_name_list[position_index] == "L":
                        frame = cv2.imread("m_data/hqtest/in_L.jpg")
                    elif path_name_list[position_index] == "ML":
                        frame = cv2.imread("m_data/hqtest/in_ML.jpg")
                    elif path_name_list[position_index] == "MR":
                        frame = cv2.imread("m_data/hqtest/in_MR.jpg")
                    else:
                        frame = cv2.imread("m_data/hqtest/in_R.jpg")
                    cv2.imwrite(pic_path, frame)
                except Exception as e:
                    print(f"{path_name_list[position_index]}读取出现错误：{e}")
                    return False
            else:
                ret = app_model.video_server.save_frame(self.direction_list[position_index], pic_path, False)
                if ret != 0:
                    return -1
            self.upload_file(app_model.device_model.ip, pic_path, "/mnt/usr/kvdb/usr_data_kvdb/" + filename)

            # 将截图在lable中进行显示
            self.show_image_fg_signal.emit(position_index, pic_path)
        return 0

    # 上传文件
    def upload_file(self, device_ip, upload_file, upload_path="/mnt/usr/kvdb/usr_data_kvdb/inter_cfg",
                    check_mode=-1):

        # self.one_click_thread_event.set()
        # self.one_click_thread = True
        # return True
        ret = False
        if not device_ip:
            self.show_message_signal.emit(False, "数据上传:设备IP异常")
        elif not server or not server.login(device_ip):
            self.show_message_signal.emit(False, "数据上传:设备登录失败")
        elif server.upload_file(filename=upload_file, upload_path=upload_path):
            if check_mode == -1:
                self.show_message_signal.emit(True, f"{upload_file}上传成功")
                self.work_thread_state = False
                ret = True
            elif check_mode == 0 and self.check_internal_cfg(upload_file):
                self.show_message_signal.emit(True, f"{upload_file}上传成功")
                self.work_thread_state = False
                self.show_message_signal.emit(True, "内参标定完成")
                ret = True
            elif check_mode == 1 and self.check_external_cfg(upload_file):
                self.show_message_signal.emit(True, f"{upload_file}上传成功")
                self.work_thread_state = False
                self.show_message_signal.emit(True, "外参标定完成")
                ret = True
            # server.logout()
        else:
            self.show_message_signal.emit(False, "数据上传失败")
            server.logout()

        self.one_click_thread = True
        self.one_click_thread_event.set()
        return ret

    # 开始标定内参
    def create_path_and_cali_in(self):
        # 获取sn号
        sn = app_model.device_model.sn
        if not sn:
            self.log.log_err("sn获取失败")
            self.show_message_signal.emit(False, "sn获取失败")
            return False
        # 创建目录
        internal_data_path = os.path.join(app_model.work_path_internal, sn)
        if not os.path.exists(internal_data_path):
            os.makedirs(internal_data_path)
        self.internal_data_path = internal_data_path
        if not self.internal_data_path:
            self.show_message_signal.emit(False, "内参保存路径创建失败")
            return False

        ok, result = self.cali_in()
        if ok:
            self.on_work_thread_finish_success(result)
            return True
        else:
            self.on_work_thread_finish_failed(f"内参获取失败：{result}")
            return False

    def cali_in(self):
        # 精度
        precision = m_global.inter_calib_precision

        for dirct in ["L", "ML", "MR", "R"]:
            chessboard = self.chessboard[dirct]
            obj_point_list, img_point_list, frame_size, camera_type = chessboard["obj_point_list"], chessboard[
                "img_point_list"], chessboard["frame_size"], chessboard["camera_type"]

            data = self.camera_cali.calib_in(obj_point_list, img_point_list, frame_size, camera_type)
            if data.camera_mat is None or data.dist_coeff is None:
                return False, f"{dirct} NoBoeardError"
            elif data.reproj_err >= precision:
                return False, f"{dirct} ReProjectionError: {data.reproj_err}"
            elif not data.ok:
                return False, f"{dirct} cacle abnormal abnormal"
            print(f"{dirct} Intrinsic Calibration Ok\n")
            self.show_message_signal.emit(True, f"{dirct} 内参标定成功")

            calib_result = self.create_internal(frame_size, data.camera_mat, data.dist_coeff)
            self.calib_parameter[f"{self.dirct_trans[dirct]}_calib"] = calib_result

        result = json.dumps(self.calib_parameter, indent=4, separators=(', ', ': '), ensure_ascii=False)
        return True, result

    def create_internal(self, img_size, mtx, distortion):
        calib = []
        # Camera Size
        calib.extend(list(img_size))
        # Camera Matrix
        mtx_array = np.array(mtx)
        mtx_array = mtx_array.flatten()
        calib.extend(mtx_array)
        # Distortion Coefficient
        distortion_array = np.array(distortion)
        distortion_array = distortion_array.flatten()
        calib.extend(distortion_array)
        return calib

    # # 进行内参计算
    # def get_inter_stitch(self):
    #     # if not self.check_device_factory_mode():
    #     #     self.work_thread_state = False
    #     #     return
    #     self.show_message_signal.emit(True, "开始计算相机内参")
    #     get_stitch(self.internal_data_path, self.work_thread_finish_success_signal,
    #                self.work_thread_finish_failed_signal)

    def create_path_and_cali_ex(self, internal_path=None):
        # 创建目录
        sn = app_model.device_model.sn
        if not sn:
            self.log.log_err("sn获取失败")
            self.show_message_signal.emit(False, "sn获取失败")
            self.view.set_start_button_enable(True)
            return False

        external_data_path = os.path.join(app_model.work_path_external, sn)
        if not os.path.exists(external_data_path):
            os.makedirs(external_data_path)
        self.external_data_path = external_data_path

        if not self.external_data_path:
            self.view.set_start_button_enable(True)
            self.show_message_signal.emit(False, "外参保存路径创建失败")
            return False

        if internal_path is None:
            print(f"内参文件路径为空")
            return False
        try:
            for key, values in {'L': ['L', "L_L"], 'ML': ["ML_L"], 'MR': ["MR_R"], 'R': ['R', "R_R"]}.items():
                for value in values:
                    source_file = f"{internal_path}\\{key}\\chessboard_{key}.jpg"
                    target_file = f"{self.external_data_path}\\chessboard_{value}.jpg"
                    shutil.copy(source_file, target_file)
                    print(f"Successfully copied {source_file} to {target_file}")
        except Exception as e:
            print(f"复制文件时出现错误：{e}")
            return False

        self.cali_ex(app_model.config_ex_internal_path)

    # 开始标定外参
    def cali_ex(self, internal_path=None):
        self.show_message_signal.emit(True, "开始计算相机外参")

        common_board = [m_global.board_id_fish, m_global.board_id_left, m_global.board_id_right]
        shape_normal = (1920, 1080)
        shape_fish = (2960, 1664)

        dirct_list = [["L", "R"], ["L", "ML"], ["R", "MR"]]
        prefix_list = ["", "left_", "right_"]
        rotate_list = [m_global.board_rotate_fish, m_global.board_rotate_left, m_global.board_rotate_right]

        cfg_params = None
        with open(internal_path, 'r') as file:
            cfg_params = json.load(file)

        for i in range(len(dirct_list)):
            dirct_1, dirct_2, prefix = dirct_list[i][0], dirct_list[i][1], prefix_list[i]
            camera_type_1, camera_type_2 = "normal", "normal"
            if dirct_1[0] != "M":
                camera_type_1 = "fisheye"
            if dirct_2[0] != "M":
                camera_type_2 = "fisheye"

            print(f"-----------------------")
            print(f"{prefix}cali_ex begin")

            ret_1, rvecs_1, tvecs_1, point_dict_1, point_dict_perspec_1 = self.cali_ex_one_camera(dirct_1,
                                                                                                  common_board[i],
                                                                                                  camera_type_1,
                                                                                                  rotate_list[i])
            print(f"{prefix}{dirct_1}:")
            print(f"rvecs_1:\n{rvecs_1}")
            print(f"tvecs_1:\n{tvecs_1}\n")
            ret_2, rvecs_2, tvecs_2, point_dict_2, point_dict_perspec_2 = self.cali_ex_one_camera(dirct_2,
                                                                                                  common_board[i],
                                                                                                  camera_type_2,
                                                                                                  rotate_list[i])
            print(f"{prefix}{dirct_2}:")
            print(f"rvecs_2:\n{rvecs_2}")
            print(f"tvecs_2:\n{tvecs_2}")

            cfg_params[prefix + 'rvecs_1'] = rvecs_1.flatten().tolist()
            cfg_params[prefix + 'tvecs_1'] = tvecs_1.flatten().tolist()
            cfg_params[prefix + 'rvecs_2'] = rvecs_2.flatten().tolist()
            cfg_params[prefix + 'tvecs_2'] = tvecs_2.flatten().tolist()

            common_keys = set(point_dict_1.keys()) & set(point_dict_2.keys())
            prespec_point_1, prespec_point_2 = [], []
            distance, distance_count = 0.0, 0
            for common_key in common_keys:
                prespec_point_1.append(point_dict_perspec_1[common_key])
                prespec_point_2.append(point_dict_perspec_2[common_key])
                distance += np.sqrt(np.sum((point_dict_1[common_key] - point_dict_2[common_key]) ** 2))
                distance_count += 1
            distance /= distance_count
            print(f"拼接参数误差 : {distance}")
            if distance > m_global.stitch_distance:  # 0.015
                self.show_message_signal.emit(False, "拼接标定误差较大")
                print("拼接标定误差较大")
                self.ex_cali_finish(False, cfg_params)
                return

            if prefix != "":
                M, mask = cv2.findHomography(np.array(prespec_point_1), np.array(prespec_point_2), cv2.RANSAC)
                cfg_params[prefix + 'M'] = M.flatten().tolist()

                distance = self.prespec_test(dirct_1, dirct_2, M)
                if distance > m_global.reproj_distance:  # 0.015
                    self.show_message_signal.emit(False, "透视矩阵标定误差较大")
                    print("透视矩阵标定误差较大")
                    self.ex_cali_finish(False, cfg_params)
                    return

        self.ex_cali_finish(True, cfg_params)

    def prespec_test(self, dirct_1, dirct_2, M):
        # 创建一个空白的黑色画布
        canvas = np.zeros((1080, 1960, 3), dtype=np.uint8)

        img_point_list_1 = copy.deepcopy(self.chessboard[dirct_1]['img_point_list'])
        id_dict_1 = self.chessboard[dirct_1]['id_dict']
        id_dict_list_1 = list(id_dict_1.keys())
        calib_param = self.calib_parameter[self.dirct_trans[dirct_1] + "_calib"]
        mtx_1 = np.array(calib_param[2:11]).reshape(3, 3)
        dist_1 = np.array(calib_param[11:])
        new_camera_matrix_1 = np.multiply(mtx_1, [[0.6, 1, 1], [1, 0.6, 1], [1, 1, 1]])
        for index in range(len(img_point_list_1)):
            img_points = img_point_list_1[index]
            img_points = cv2.fisheye.undistortPoints(img_points, mtx_1, dist_1, R=new_camera_matrix_1)
            img_points = img_points.reshape(-1, 2)
            points_homogeneous = np.hstack([img_points, np.ones((img_points.shape[0], 1))])
            transformed_points_homogeneous = points_homogeneous @ M.T
            img_points = transformed_points_homogeneous[:, :2] / transformed_points_homogeneous[:, 2, np.newaxis]
            img_point_list_1[index] = img_points.reshape(-1, 1, 2)

        img_point_list_2 = copy.deepcopy(self.chessboard[dirct_2]['img_point_list'])
        id_dict_2 = self.chessboard[dirct_2]['id_dict']
        id_dict_list_2 = list(id_dict_2.keys())
        calib_param = self.calib_parameter[self.dirct_trans[dirct_2] + "_calib"]
        mtx_2 = np.array(calib_param[2:11]).reshape(3, 3)
        dist_2 = np.array(calib_param[11:])
        new_camera_matrix_2 = np.multiply(mtx_2, [[0.8, 1, 1], [1, 0.8, 1], [1, 1, 1]])
        point_dict_1, point_dict_2 = {}, {}
        for index_2 in range(len(img_point_list_2)):
            img_points = img_point_list_2[index_2]
            img_point_list_2[index_2] = cv2.undistortPoints(img_points, mtx_2, dist_2, R=new_camera_matrix_2)
            # 寻找共同点
            chessboard_id = id_dict_list_2[index_2]
            if chessboard_id in id_dict_list_1:  # 共同标定板
                index_1 = id_dict_list_1.index(id_dict_list_2[index_2])
                point_dict_1.update({i: arr for i, arr in zip(id_dict_1[chessboard_id], img_point_list_1[index_1])})
                point_dict_2.update({i: arr for i, arr in zip(id_dict_2[chessboard_id], img_point_list_2[index_2])})

        common_keys = set(point_dict_1.keys()) & set(point_dict_2.keys())
        distance, distance_count = 0.0, 0
        for common_key in common_keys:
            distance += np.sqrt(np.sum((point_dict_1[common_key] - point_dict_2[common_key]) ** 2))
            distance_count += 1

            cv2.circle(canvas, (int(point_dict_1[common_key][0][0]), int(point_dict_1[common_key][0][1])), 5,
                       (0, 0, 255), -1)
            cv2.circle(canvas, (int(point_dict_2[common_key][0][0]), int(point_dict_2[common_key][0][1])), 5,
                       (0, 255, 0), -1)

        distance /= distance_count
        print(f"透视变化误差 : {distance}")
        return distance

    def cali_ex_one_camera(self, dirct, common_board, camera_type, rotate):
        dirct_1_key_list = list(self.chessboard[dirct]["id_dict"].keys())
        index = dirct_1_key_list.index(common_board)
        obj_point_list = self.chessboard[dirct]["obj_point_list"][index]
        img_point_list = self.chessboard[dirct]["img_point_list"][index]
        point_id_list = self.chessboard[dirct]["id_dict"][common_board]
        calib_param = self.calib_parameter[self.dirct_trans[dirct] + "_calib"]
        mtx = np.array(calib_param[2:11]).reshape(3, 3)
        dist = np.array(calib_param[11:])
        return self.camera_cali.calib_ex(obj_point_list, img_point_list, point_id_list, mtx, dist, check_mode=True,
                                         camera_type=camera_type, rotate=rotate)

    def ex_cali_finish(self, state, cfg_params=None):
        if not state:
            self.show_message_signal.emit(False, "外参标定失败...")
        else:
            # 保存文件
            try:
                result_json = json.dumps(cfg_params, indent=4)
                print("JSON serialization successful.")
            except Exception as e:
                print(f"An error occurred during JSON serialization: {e}")
                return False

            self.save_file(result_json, self.external_data_path, "external_cfg.json")
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
        return state

    # 相机位置切换槽函数
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

    # 相机位置切换函数
    def on_position_type_changed(self, index):
        self.position_index = index
        # 发出显示信号
        self.show_message_signal.emit(True, self.view.position_type_text[self.position_index] + "相机截图")
        # 更改显示视频
        if index != 4:
            self.start_video_unique([{"direction": self.direction_list[index],
                                      "label": self.view.label_video_fg, "rotate": 0}])
        else:  # 全视野截图
            self.start_video_all(self.direction_list, self.view.label_video_fg, 0)

        # 去畸变按钮槽函数
        def undistorted(self, state):
            app_model.video_server.set_undistorted_bool(state)

    # 去畸变按钮槽函数
    def undistorted(self, state):
        app_model.video_server.set_undistorted_bool(state)

    # 清晰度测试槽函数
    def clarity_test(self, state):
        app_model.video_server.set_clarity_test_bool(state)

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

    # 内参计算成功则上传参数到目标相机
    def on_work_thread_finish_success(self, result):
        self.view.close_loading()
        self.work_thread = None
        if not result:
            self.show_message_signal.emit(False, "内参计算失败")
            self.work_thread_state = False
            self.one_click_thread = True
            # print("one_click_thread_event set 1")
            self.one_click_thread_event.set()
            return
        self.screenshot_count = 0
        self.screenshot_lable_ok = []
        self.show_message_signal.emit(True, "内参计算完成")
        # time.sleep(0.2)
        app_model.video_server.internal_data = json.loads(result)
        # self.view.set_internal_result(result)

        device_ip = app_model.device_model.ip
        internal_file = self.save_file(result, self.internal_data_path)
        # ex_internal_file = self.save_file(result, os.path.dirname(internal_file), "external_cfg.json")
        # 应用在设备上
        # app_model.video_server.fisheye_internal_init(internal_file)
        app_model.config_ex_internal_path = internal_file

        self.show_message_signal.emit(True, "上传参数结果到相机")
        self.upload_file(device_ip, internal_file)
        print("内参标定完成")
        #
        self.work_thread_state = False
        self.show_image_fg_signal.emit(-1, "")

    # 内参计算失败
    def on_work_thread_finish_failed(self, error_msg):
        self.show_message_signal.emit(False, f"内参处理" + error_msg)
        # if error_msg.startswith('内参获取失败：L'):
        #     self.screenshot_lable_ok.remove('L')
        #     self.view.set_position_type_button_enable(0)
        #     self.on_position_type_changed(0)
        # elif error_msg.startswith('内参获取失败：ML'):
        #     self.screenshot_lable_ok.remove('ML')
        #     self.view.set_position_type_button_enable(1)
        #     self.on_position_type_changed(1)
        # elif error_msg.startswith('内参获取失败：MR'):
        #     self.screenshot_lable_ok.remove('MR')
        #     self.view.set_position_type_button_enable(2)
        #     self.on_position_type_changed(2)
        # elif error_msg.startswith('内参获取失败：R'):
        #     self.screenshot_lable_ok.remove('R')
        #     self.view.set_position_type_button_enable(3)
        #     self.on_position_type_changed(3)
        # self.screenshot_count -= 1

        self.work_thread_state = False

        self.one_click_thread = False
        self.one_click_thread_event.set()

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

    @staticmethod
    def save_file(result=None, file_path=None, file_name="inter_cfg.json"):
        if not result:
            return
        if file_path is None:
            file_path = os.path.join(os.getcwd(), "result", str(int(time.time())))
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        internal_file = os.path.join(file_path, file_name)
        with open(internal_file, "w", encoding="utf-8") as f:
            f.write(result)
        return internal_file

    def check_internal_cfg(self, local_internal_cfg_path):
        return True
        # local_internal_cfg_name = local_internal_cfg_path.replace('\\', '/')
        # with open(local_internal_cfg_name, 'r') as file:
        #     local_internal_cfg = json.load(file)
        #
        # if not local_internal_cfg:
        #     self.show_message_signal.emit(False, "获取设备本地内参文件失败:body")
        #     return False
        #
        # internal_cfg_info = server.get_internal_cfg()
        # if not internal_cfg_info:
        #     self.show_message_signal.emit(False, "获取设备内参文件失败")
        #     return False
        # internal_cfg = internal_cfg_info.get("body")
        # if not internal_cfg:
        #     self.show_message_signal.emit(False, "获取设备内参文件失败:body")
        #     return False
        #
        # # 检查字典长度是否相等
        # if len(local_internal_cfg) != len(internal_cfg):
        #     return False
        # # 逐一比较字典中的键和值
        # for key in local_internal_cfg.keys():
        #     if key not in internal_cfg:
        #         return False
        #     if not lists_equal(local_internal_cfg[key], internal_cfg[key]):
        #         return False
        #
        # return True
