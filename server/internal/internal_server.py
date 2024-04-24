#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json

import numpy as np

# from server.internal.ExtrinsicCalibration import ExCalibrator
from server.internal.IntrinsicCalibration.intrinsicCalib import InCalibrator, CalibMode


def runInCalib_2(mode, imgPath, imgPrefix, bResize, imgW, imgH, bW, bH, bSize):
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
    calibrator = InCalibrator(mode)  # 初始化内参标定器
    calib = CalibMode(calibrator, 'image', 'auto')  # 选择标定模式
    result = calib()  # 开始标定

    re_projection_error = None
    if result is not None:
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
    precision = 0.1
    img_sizeLR_OLD = (2560, 1440)
    img_sizeML = (1920, 1080)
    img_sizeMR = (1920, 1080)
    img_sizeLR_NEW = (2960, 1664)
    # img_sizeML = img_sizeMR = img_sizeLR_NEW

    print(1)
    mtxL, distortionL, __, __, reProjectionErrorL = runInCalib_2(mode, filePath + "/L", "chessboard", False,
                                                                 img_sizeLR_NEW[0], img_sizeLR_NEW[1], 11, 8, 25)
    print(2)
    if mtxL is None or distortionL is None or reProjectionErrorL is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorL >= precision:
        return False, f"L ReProjectionError: {reProjectionErrorL}"
    print(f"L ReProjectionError: {reProjectionErrorL}")

    mtxML, distortionML, __, __, reProjectionErrorML = runInCalib_2(mode_normal, filePath + "/ML", "chessboard", False,
                                                                    img_sizeML[0], img_sizeML[1], 11, 8, 25)
    if mtxML is None or distortionML is None or reProjectionErrorML is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorML >= precision:
        return False, f"M ReProjectionError: {reProjectionErrorML}"
    print(f"ML ReProjectionError: {reProjectionErrorML}")

    mtxMR, distortionMR, __, __, reProjectionErrorMR = runInCalib_2(mode_normal, filePath + "/MR", "chessboard", False,
                                                                    img_sizeMR[0], img_sizeMR[1], 11, 8, 25)
    if mtxMR is None or distortionMR is None or reProjectionErrorMR is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorMR >= precision:
        return False, f"M ReProjectionError: {reProjectionErrorMR}"
    print(f"MR ReProjectionError: {reProjectionErrorMR}")

    mtxR, distortionR, __, __, reProjectionErrorR = runInCalib_2(mode, filePath + "/R", "chessboard", False,
                                                                 img_sizeLR_NEW[0], img_sizeLR_NEW[1], 11, 8, 25)
    if mtxR is None or distortionR is None or reProjectionErrorR is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorR >= precision:
        return False, f"R ReProjectionError: {reProjectionErrorR}"
    print(f"R ReProjectionError: {reProjectionErrorR}")

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
        else:
            error_signal.emit(f"内参获取失败：{result}")
    except Exception as e:
        error_signal.emit(f"内参获取失败：{e}")
    print("get_stitch")
