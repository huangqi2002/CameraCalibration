#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import time

import numpy as np

# from server.internal.ExtrinsicCalibration import ExCalibrator
from server.internal.IntrinsicCalibration.intrinsicCalib import InCalibrator, CalibMode
from utils.run_para import m_global


def runInCalib_2(mode, imgPath, imgPrefix, bResize, imgW, imgH, bW, bH, bSize, bSpacer, bNum, aruco_flag=False,
                 find_type=False):
    print("Intrinsic Calibration ......")
    args = InCalibrator.get_args()  # 获取内参标定args参数
    args.INPUT_PATH = imgPath  # 修改为新的参数
    args.IMAGE_FILE = imgPrefix
    args.RESIZE_FLAG = bResize
    args.FRAME_WIDTH = imgW
    args.FRAME_HEIGHT = imgH
    args.BOARD_WIDTH = bW
    args.BOARD_HEIGHT = bH
    args.SQUARE_SIZE = bSize
    args.ARUCO_BOARD_SPACER = bSpacer
    args.ARUCO_BOARD_NUM = bNum
    args.ARUCO_FLAG = aruco_flag
    args.FIND_TYPE = find_type
    calibrator = InCalibrator(mode)  # 初始化内参标定器
    calib = CalibMode(calibrator, 'image', 'auto')  # 选择标定模式
    # args.CALI_STATE = False
    # result = calib()  # 开始标定
    args.CALI_STATE = True
    result = calib()  # 开始标定

    re_projection_error = None
    if result is not None and result.ok:
        print("Camera Matrix is : {}".format(result.camera_mat.tolist()))
        print("Distortion Coefficient is : {}".format(result.dist_coeff.tolist()))
        re_projection_error = np.mean(result.reproj_err)
        print("Reprojection Error is : {}".format(re_projection_error))
    return result.camera_mat, result.dist_coeff, calibrator.camera.board, calibrator.corners, re_projection_error


def create_internal(img_size, mtx, distortion):
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


def stitch_test(filePath):
    mode = "fisheye"
    mode_normal = "normal"
    precision = m_global.inter_calib_precision
    img_sizeLR_OLD = (2560, 1440)
    img_sizeML = (1920, 1080)
    img_sizeMR = (1920, 1080)
    img_sizeLR_NEW = (2960, 1664)
    # img_sizeML = img_sizeMR = img_sizeLR_NEW
    aruco_flag = m_global.aruco_flag
    bW = m_global.bW
    bH = m_global.bH
    bSize = m_global.bSize
    bSpacer = m_global.bSpacer
    bNum = m_global.bNum
    imgPrefix, find_type = "chessboard", m_global.find_type
    # imgPrefix, find_type = "chessboard", False

    mtxL, distortionL, __, __, reProjectionErrorL = runInCalib_2(mode, filePath + "/L", imgPrefix, False,
                                                                 img_sizeLR_NEW[0], img_sizeLR_NEW[1], bW, bH, bSize,
                                                                 bSpacer, bNum, aruco_flag, find_type)
    print(f"L Intrinsic Calibration Ok\n")
    # time.sleep(0.2)

    mtxML, distortionML, __, __, reProjectionErrorML = runInCalib_2(mode_normal, filePath + "/ML", imgPrefix, False,
                                                                    img_sizeML[0], img_sizeML[1], bW, bH, bSize,
                                                                    bSpacer, bNum, aruco_flag, find_type)
    print(f"ML Intrinsic Calibration Ok\n")
    # time.sleep(0.2)

    mtxMR, distortionMR, __, __, reProjectionErrorMR = runInCalib_2(mode_normal, filePath + "/MR", imgPrefix, False,
                                                                    img_sizeMR[0], img_sizeMR[1], bW, bH, bSize,
                                                                    bSpacer, bNum, aruco_flag, find_type)
    print(f"MR Intrinsic Calibration Ok\n")
    # time.sleep(0.2)

    mtxR, distortionR, __, __, reProjectionErrorR = runInCalib_2(mode, filePath + "/R", imgPrefix, False,
                                                                 img_sizeLR_NEW[0], img_sizeLR_NEW[1], bW, bH, bSize,
                                                                 bSpacer, bNum, aruco_flag, find_type)
    print(f"R  Intrinsic Calibration Ok\n")
    # time.sleep(0.2)

    if mtxL is None or distortionL is None or reProjectionErrorL is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorL >= precision:
        return False, f"L ReProjectionError: {reProjectionErrorL}"

    if mtxML is None or distortionML is None or reProjectionErrorML is None:
        return False, f"ML NoBoeardError"
    elif reProjectionErrorML >= precision:
        return False, f"ML ReProjectionError"

    if mtxMR is None or distortionMR is None or reProjectionErrorMR is None:
        return False, f"MR NoBoeardError"
    elif reProjectionErrorMR >= precision:
        return False, f"MR ReProjectionError: {reProjectionErrorMR}"

    if mtxR is None or distortionR is None or reProjectionErrorR is None:
        return False, f"R NoBoeardError"
    elif reProjectionErrorR >= precision:
        return False, f"R ReProjectionError: {reProjectionErrorR}"

    left_calib = create_internal(img_sizeLR_NEW, mtxL, distortionL)
    mid_left_calib = create_internal(img_sizeML, mtxML, distortionML)
    mid_right_calib = create_internal(img_sizeMR, mtxMR, distortionMR)
    right_calib = create_internal(img_sizeLR_NEW, mtxR, distortionR)

    result = {"left_calib": left_calib, "mid_left_calib": mid_left_calib, "mid_right_calib": mid_right_calib,
              "right_calib": right_calib}
    return True, json.dumps(result, indent=4, separators=(', ', ': '), ensure_ascii=False)


def get_stitch(file_path, success_signal, error_signal):
    try:
        success, result = stitch_test(file_path)
        if success:
            success_signal.emit(result)
            return True
        else:
            error_signal.emit(f"内参获取失败：{result}")
            return False
    except Exception as e:
        error_signal.emit(f"内参获取失败：{e}")
        return False
    # print("get_stitch")
