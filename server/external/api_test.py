#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
from lib3rd.load_lib import *

if __name__ == '__main__':
    time.time()
    sdk_avs_version = (c_char * 128)()
    print("mpi_avs_version start", sdk_avs_version.value.decode())
    ret_get_version = sdk.mpi_avs_version(sdk_avs_version)
    print("mpi_avs_version end", ret_get_version, sdk_avs_version.value.decode())

    # config_file = os.path.join(os.getcwd(), "data_test", "chessboard.yml").encode()
    config_file = "./data_test/chessboard.yml".encode("utf-8")
    result = AvsCalibrationMeasurement()
    output_error_flag = c_int(0)
    # ret_avs_chessboard = sdk.mpi_avs_chessboard_calibration(config_file, byref(result), byref(output_error_flag))
    ret_avs_chessboard = sdk.mpi_avs_chessboard_calibration(config_file, result, output_error_flag)
    print("mpi_avs_chessboard_calibration end", "result:", ret_avs_chessboard,
          "output_error_flag:", output_error_flag.value,
          "max_reprojection_err:", result.max_reprojection_err,
          "average_reprojection_err:", result.average_reprojection_err,
          "total_matched_points:", result.total_matched_points)

    # avs_stitch_config = StitchAvsConfig()
    # avs_stitch_config.camera_num = 2
    # avs_stitch_config.src_size.width = 2688
    # avs_stitch_config.src_size.height = 1520
    # avs_stitch_config.dst_size.width = 3000
    # avs_stitch_config.dst_size.height = 900
    # #
    # avs_stitch_config.prj_mode = 0
    #
    # avs_stitch_config.center.x = 810
    # avs_stitch_config.center.y = 146
    # avs_stitch_config.fov.fov_x = 17500
    # avs_stitch_config.fov.fov_y = 4800
    # avs_stitch_config.ori_rotation.yaw = 0
    # avs_stitch_config.ori_rotation.pitch = 0
    # avs_stitch_config.ori_rotation.roll = 0
    # avs_stitch_config.rotation.yaw = 0
    # avs_stitch_config.rotation.pitch = 0
    # avs_stitch_config.rotation.roll = 0
    #
    # config_stitch = StitchConfig()
    # config_stitch.avs_stitch_config = avs_stitch_config
    # config_stitch_img_size = StitchImgSizeCfg()
    # param_stitch_out = StitchOutParam()
    # config_file = "./data_test/out_param.lut".encode()
    # ret_stitch_lut = sdk.ot_mpi_stitch_lut_generate(config_stitch, config_stitch_img_size, param_stitch_out, config_file)
    # print("ot_mpi_stitch_lut_generate end", "result:", ret_stitch_lut)
