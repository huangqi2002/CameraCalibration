#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import ctypes
import os
import win32api
from ctypes import *

path_root = os.getcwd()
path_custom = [os.path.join(path_root, "lib3rd", "win64"), os.path.join(path_root, "server", "external", "lib3rd", "win64")]

for path in path_custom:
    path = os.path.realpath(path)
    print("Add environ path ->", path)
    os.environ['path'] += f';{path}'


class VzCalibrationSDK:
    def __init__(self):
        # 加载SDK
        # self.calibration_dll = cdll.LoadLibrary(os.path.join(path_custom[0], "VZ_Calibration"))
        print(os.path.join(path_custom[1], "VZ_Calibration.dll"))
        self.calibration_dll = ctypes.CDLL(os.path.join(path_custom[1], "VZ_Calibration.dll"))

    def __del__(self):
        # 释放SDK
        try:
            if self.calibration_dll:
                win32api.FreeLibrary(self.calibration_dll._handle)
        except Exception as e:
            print(f"release lib failed: {e}")

    def model_calibration(self, config_file:str):
        if not self.calibration_dll:
            print("load VZ_Calibration.dll failed.")
            return -1
        config_file = config_file.encode(encoding="utf-8", errors="ignore")
        return self.calibration_dll.Model_Calibration(config_file)

    def x2_lut_generate(self, cal_file_in, mesh_file_prefix):
        if not self.calibration_dll:
            print("load VZ_Calibration.dll failed.")
            return -1
        cal_file_in = cal_file_in.encode(encoding="utf-8", errors="ignore")
        mesh_file_prefix = mesh_file_prefix.encode(encoding="utf-8", errors="ignore")
        return self.calibration_dll.X2_lut_generate(cal_file_in, mesh_file_prefix)

    def fg_lut_generate(self, cal_file_in, mesh_file_prefix):
        if not self.calibration_dll:
            print("load VZ_Calibration.dll failed.")
            return -1
        cal_file_in = cal_file_in.encode(encoding="utf-8", errors="ignore")
        mesh_file_prefix = mesh_file_prefix.encode(encoding="utf-8", errors="ignore")
        return self.calibration_dll.FG_lut_generate(cal_file_in, mesh_file_prefix)

    def rotate_and_resize_images(self, image_path):
        if not self.calibration_dll:
            print("load VZ_Calibration.dll failed.")
            return -1
        image_path = image_path.encode(encoding="utf-8", errors="ignore")
        print("befor rotate_and_resize_images_01")
        print(image_path)
        ret = self.calibration_dll.rotate_and_resize_images(image_path)
        print("after rotate_and_resize_images")
        return ret


sdk = VzCalibrationSDK()
