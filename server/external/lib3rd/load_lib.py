#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import os
import time

import numpy as np
import win32api
from ctypes import *

path_root = os.getcwd()
path_custom = [os.path.join(path_root, "lib3rd", "win64"),
               os.path.join(path_root, "server", "external", "lib3rd", "win64"),
               os.path.join(path_root, "lib3rd", "fisheye"), os.path.join(path_root, "lib3rd", "chessboard")]

for path in path_custom:
    path = os.path.realpath(path)
    print("Add environ path ->", path)
    os.environ['path'] += f';{path}'


# class VzCalibrationSDK:
#     def __init__(self):
#         # 加载SDK
#         # self.calibration_dll = cdll.LoadLibrary(os.path.join(path_custom[0], "VZ_Calibration"))
#         print(os.path.join(path_custom[1], "VZ_Calibration.dll"))
#         self.calibration_dll = ctypes.CDLL(os.path.join(path_custom[1], "VZ_Calibration.dll"))
#
#     def __del__(self):
#         # 释放SDK
#         try:
#             if self.calibration_dll:
#                 win32api.FreeLibrary(self.calibration_dll._handle)
#         except Exception as e:
#             print(f"release lib failed: {e}")
#
#     def model_calibration(self, config_file: str):
#         if not self.calibration_dll:
#             print("load VZ_Calibration.dll failed.")
#             return -1
#         config_file = config_file.encode(encoding="utf-8", errors="ignore")
#         return self.calibration_dll.Model_Calibration(config_file)
#
#     def x2_lut_generate(self, cal_file_in, mesh_file_prefix):
#         if not self.calibration_dll:
#             print("load VZ_Calibration.dll failed.")
#             return -1
#         cal_file_in = cal_file_in.encode(encoding="utf-8", errors="ignore")
#         mesh_file_prefix = mesh_file_prefix.encode(encoding="utf-8", errors="ignore")
#         return self.calibration_dll.X2_lut_generate(cal_file_in, mesh_file_prefix)
#
#     def fg_lut_generate(self, cal_file_in, mesh_file_prefix):
#         if not self.calibration_dll:
#             print("load VZ_Calibration.dll failed.")
#             return -1
#         cal_file_in = cal_file_in.encode(encoding="utf-8", errors="ignore")
#         mesh_file_prefix = mesh_file_prefix.encode(encoding="utf-8", errors="ignore")
#         return self.calibration_dll.FG_lut_generate(cal_file_in, mesh_file_prefix)
#
#     def rotate_and_resize_images(self, image_path):
#         if not self.calibration_dll:
#             print("load VZ_Calibration.dll failed.")
#             return -1
#         modified_image_path = image_path.replace("\\", "/")
#         print(f"modified_image_path : {modified_image_path}")
#         filenames = os.listdir(modified_image_path)  # 在argparse中修改图片路径
#         print(modified_image_path)
#         for filename in filenames:
#             print(filename)
#         modified_image_path = modified_image_path.encode(encoding="utf-8", errors="ignore")
#         # image_path = image_path.encode(encoding="utf-8", errors="ignore")
#         # print(image_path)
#         ret = self.calibration_dll.rotate_and_resize_images(modified_image_path)
#         print("after rotate_and_resize_images")
#         return ret


# def add_suffix_to_file(filepath, suffix='_result'):
#     # 分割文件路径和文件名
#     directory, filename = os.path.split(filepath)
#     # 分割文件名和后缀
#     basename, ext = os.path.splitext(filename)
#     # 新的文件名
#     new_filename = basename + suffix + ext
#     # 组合新的路径
#     new_filepath = os.path.join(directory, new_filename)
#     return new_filepath


# class ChessboardFindSDK:
#     def __init__(self):
#         # 加载SDK
#         # self.calibration_dll = cdll.LoadLibrary(os.path.join(path_custom[0], "VZ_Calibration"))
#         # print(os.path.join(path_custom[3], "chessboard_detect_dll.dll"))
#         self.calibration_dll = ctypes.CDLL(os.path.join(path_custom[3], "chessboard_detect_dll.dll"))
#
#     def find_chessboard(self, img, factor, filename):
#         if not self.calibration_dll:
#             print("load chessboard_detect_dll.dll failed.")
#             return -1
#
#         # 定义函数参数和返回类型
#         self.calibration_dll.chessboard_find_c.argtypes = [ctypes.POINTER(ctypes.c_void_p),
#                                                            ctypes.POINTER(ctypes.c_void_p),
#                                                            ctypes.POINTER(ctypes.c_ubyte), ctypes.c_double,
#                                                            ctypes.c_bool, ctypes.c_char_p]
#         self.calibration_dll.chessboard_find_c.restype = None
#
#         # 创建空的向量，用于存储返回的坐标点
#         coordinates1_ptr = ctypes.c_void_p()
#         coordinates2_ptr = ctypes.c_void_p()
#
#         save = False
#         img_path_c = None
#         if filename != "":
#             filename = add_suffix_to_file(filename)
#             # 调用 C 函数，传递空的向量指针
#             img_path_c = filename.encode(encoding="utf-8", errors="ignore")
#             save = True
#         self.calibration_dll.chessboard_find_c(ctypes.byref(coordinates1_ptr), ctypes.byref(coordinates2_ptr),
#                                                img.ctypes.data_as(ctypes.POINTER(ctypes.c_ubyte)), factor, save,
#                                                img_path_c)
#
#         # 将指针转换为 NumPy 数组
#         coordinates1_np = np.ctypeslib.as_array(coordinates1_ptr.contents)
#         coordinates2_np = np.ctypeslib.as_array(coordinates2_ptr.contents)
#
#         # 打印 NumPy 数组
#         print("coordinates1_np:\n", coordinates1_np)
#         print("coordinates2_np:\n", coordinates2_np)
#
#         # 释放指针内存
#         self.calibration_dll.delete_coordinates(coordinates1_ptr)
#         self.calibration_dll.delete_coordinates(coordinates2_ptr)
#
#         return coordinates1_np, coordinates2_np


# sdk = VzCalibrationSDK()
# chess_board_sdk = ChessboardFindSDK()
