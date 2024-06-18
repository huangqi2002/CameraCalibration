import ctypes
import json
import os

import cv2
import threading

import numpy as np
import ctypes as C

from aruco_vz import aruco_tool
from server.external.ex_Calib import ex_calib
from internal.IntrinsicCalibration.intrinsicCalib import InCalibrator, CalibMode
from server.internal.internal_server import create_internal

import img2pdf


rtsp_url = "rtsp://192.168.109.190:8557"
rtsp_url_0 = rtsp_url + "/left_main_1_0"
rtsp_url_1 = rtsp_url + "/out_left_sub_3_1"
rtsp_url_2 = rtsp_url + "/out_right_sub_4_1"
rtsp_url_3 = rtsp_url + "/right_main_2_0"

img_ex_L = cv2.imread("../m_data/aruco/bf/ex/cameraL.jpg")
img_ex_R = cv2.imread("../m_data/aruco/bf/ex/cameraR.jpg")
img_ex_ML = cv2.imread("../m_data/aruco/bf/ex/cameraML.jpg")
img_ex_MR = cv2.imread("../m_data/aruco/bf/ex/cameraMR.jpg")
in_cfg_path = "../configs/internal/external_cfg_90.json"

# read_frame_state = False
# read_frame = None
# thread_state = False
# 事件对象，用于控制线程的暂停和恢复
thread_state_event = threading.Event()

bW = 9
bH1 = 7
bNum1 = 25
bH2 = 7
bNum2 = 0
bH = 8
aruco_dictionary_num = 5
bSize = 50
bSpacer = 0
bNum = 20
white_pixs = 20

# 计数器
thread_count = 1
# 锁，用于保护计数器
lock = threading.Lock()


def read_rtsp_stream(input_para):
    print("begin open RTSP stream")
    global thread_state_event, thread_count
    cap = cv2.VideoCapture(input_para["rtsp_url"])
    if not cap.isOpened():
        print("Error: Failed to open RTSP stream")
        return
    with lock:
        thread_count = thread_count - 1
        print(f"{input_para["rtsp_url"]} is play ok")
        if thread_count == 0:
            thread_state_event.set()

    while True:
        while input_para["pause_state"]:  # , "pause_lock": threading.Lock(), "pause_state": False
            with input_para["pause_lock"]:
                input_para["pause_lock"].wait()
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to read frame from RTSP stream")
            break

        if not input_para["read_frame_state"]:
            input_para["read_frame"] = frame.copy()
            # print(f"{input_para["rtsp_url"]} is read one frame")
            input_para["read_frame_state"] = True

        if not input_para["thread_state"]:
            break

    input_para["read_frame"] = None
    cap.release()


def gen_test():
    aruco_tool.set_aruco_dictionary(aruco_dictionary_num, 1000)
    img_path = "../charuco/charuco_board.png"
    dpi = 300
    board_size = bSize

    scale_gen = 8
    white_pix = white_pixs * scale_gen

    aruco_tool.set_charuco_board((bW + 1, (bH1 + 1) * bNum1 + bSpacer * bNum1 + (bH2 + 1) * bNum2 + bSpacer * (bNum2 - 1)))
    aruco_tool.charuco_gen(((bW + 1) * board_size * scale_gen, ((bH1 + 1) * bNum1 + bSpacer * bNum1 + (bH2 + 1) * bNum2 + bSpacer * (bNum2 - 1)) * board_size * scale_gen), img_path)

    src_img = cv2.imread(img_path)
    begin_row = 0
    for i in range(bNum1):
        temp_img = src_img[begin_row * board_size * scale_gen: (begin_row + bH1 + 1) * board_size * scale_gen]
        temp_img = cv2.copyMakeBorder(temp_img, white_pix, white_pix, white_pix, white_pix, cv2.FONT_HERSHEY_SIMPLEX, value=(255, 255, 255))
        text = f"{bH1 + 1}x{bW + 1} | Checker Size: {board_size} mm | Dictionary.AruCo DICT_{aruco_dictionary_num}X{aruco_dictionary_num}."
        cv2.putText(temp_img, text, (int(white_pix + board_size * 2.5 * scale_gen), temp_img.shape[0] - 5 * scale_gen), cv2.FONT_HERSHEY_COMPLEX, 0.25 * scale_gen, (0, 0, 0), 2)
        begin_row += bH1 + 1 + bSpacer
        cv2.imwrite(f"../charuco/charuco_board_{i}.jpg", temp_img)

        # specify paper size (A4)
        inpt = (img2pdf.mm_to_pt((bW + 1) * board_size + white_pix / scale_gen * 2), img2pdf.mm_to_pt((bH1 + 1) * board_size + white_pix / scale_gen * 2))
        layout_fun = img2pdf.get_layout_fun(inpt)
        with open(f"../charuco/board_{i}.pdf", "wb") as f:
            f.write(img2pdf.convert(f"../charuco/charuco_board_{i}.jpg", dpi=dpi, layout_fun=layout_fun))

    for i in range(bNum2):
        temp_img = src_img[begin_row * board_size * scale_gen: (begin_row + bH2 + 1) * board_size * scale_gen]
        temp_img = cv2.copyMakeBorder(temp_img, white_pix, white_pix, white_pix, white_pix, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        text = f"{bH2 + 1}x{bW + 1} | Checker Size: {board_size} mm | Dictionary.AruCo DICT_{aruco_dictionary_num}X{aruco_dictionary_num}."
        cv2.putText(temp_img, text, (int(white_pix + board_size * 2.5 * scale_gen), temp_img.shape[0] - 5 * scale_gen), cv2.FONT_HERSHEY_COMPLEX, 0.25 * scale_gen, (0, 0, 0), 2)
        begin_row += bH2 + 1 + bSpacer
        cv2.imwrite(f"../charuco/charuco_board_{bNum1 + i}.jpg", temp_img)

        # specify paper size (A4)
        inpt = (img2pdf.mm_to_pt((bW + 1) * board_size + white_pix / scale_gen * 2), img2pdf.mm_to_pt((bH2 + 1) * board_size + white_pix / scale_gen * 2))
        layout_fun = img2pdf.get_layout_fun(inpt)
        with open(f"../charuco/board_{bNum1 + i}.pdf", "wb") as f:
            f.write(img2pdf.convert(f"../charuco/charuco_board_{bNum1 + i}.jpg", layout_fun=layout_fun))


def play_test():
    global thread_state_event
    aruco_tool.set_aruco_dictionary(aruco_dictionary_num, 1000)
    aruco_tool.set_charuco_board((bW + 1, (bH1 + 1) * bNum1 + bSpacer * bNum1 + (bH2 + 1) * bNum2 + bSpacer * (bNum2 - 1)))
    # aruco_tool.charuco_gen((2400, 17600))
    # aruco_tool.set_charuco_board((10, 150))

    # thread_state = True
    # read_frame = None
    # read_frame_state = False
    input_para = {"rtsp_url": rtsp_url_0, "read_frame_state": False, "read_frame": None,
                  "thread_state": True, "pause_lock": threading.Lock(), "pause_state": False}
    rtsp_thread = threading.Thread(target=read_rtsp_stream, args=(input_para,))
    rtsp_thread.start()

    thread_state_event.wait()
    thread_state_event.clear()

    cv2.namedWindow("RTSP Stream", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("RTSP Stream", 600, 900)

    max_wait_count = 30
    wait_count = 0
    board_size = 60

    i = 0

    # input_para["read_frame_state"] = True

    while True:
        if not input_para["read_frame_state"]:
            wait_count += 1
            if wait_count >= max_wait_count:
                break
            cv2.waitKey(10)
            continue

        wait_count = 0
        img = input_para["read_frame"].copy()
        # img = cv2.imread("../m_data/aruco/bf/in/L/chessboard_1714387592.jpg")
        # img = cv2.imread(f"../charuco/charuco_board_{i}.jpg")
        i += 1
        img = cv2.imread("../m_data/hqtest/in_L.jpg")
        objPoints, imgPoints, charucoIds, img = aruco_tool.charuco_detect(img, True)
        cv2.imwrite("aruco_test.jpg", img)
        # img = cv2.resize(img, (900, 600))
        if objPoints is not None:
            objPoints = objPoints / 0.25 * board_size
        cv2.imshow("RTSP Stream", img)
        input_para["read_frame_state"] = False

        if cv2.waitKey(1) == ord('q'):
            break

    input_para["thread_state"] = False
    rtsp_thread.join()
    cv2.destroyAllWindows()


def play_four():
    global thread_count
    thread_count = 4

    input_para_0 = {"rtsp_url": rtsp_url_0, "read_frame_state": False, "read_frame": None,
                    "thread_state": True, "pause_lock": threading.Lock(), "pause_state": False}
    rtsp_thread = threading.Thread(target=read_rtsp_stream, args=(input_para_0,))
    rtsp_thread.start()

    input_para_1 = {"rtsp_url": rtsp_url_1, "read_frame_state": False, "read_frame": None,
                    "thread_state": True, "pause_lock": threading.Lock(), "pause_state": False}
    rtsp_thread = threading.Thread(target=read_rtsp_stream, args=(input_para_1,))
    rtsp_thread.start()

    input_para_2 = {"rtsp_url": rtsp_url_2, "read_frame_state": False, "read_frame": None,
                    "thread_state": True, "pause_lock": threading.Lock(), "pause_state": False}
    rtsp_thread = threading.Thread(target=read_rtsp_stream, args=(input_para_2,))
    rtsp_thread.start()

    input_para_3 = {"rtsp_url": rtsp_url_3, "read_frame_state": False, "read_frame": None,
                    "thread_state": True, "pause_lock": threading.Lock(), "pause_state": False}
    rtsp_thread = threading.Thread(target=read_rtsp_stream, args=(input_para_3,))
    rtsp_thread.start()

    thread_state_event.wait()
    print(f"all url is play ok")

    wait_count = 0
    max_wait_count = 100
    while True:
        if not (input_para_0["read_frame_state"] and input_para_1["read_frame_state"] and input_para_2[
            "read_frame_state"] and input_para_3["read_frame_state"]):
            wait_count += 1
            if wait_count >= max_wait_count:
                break
            cv2.waitKey(10)
            continue
        wait_count = 0

        width = 600
        height = 400

        img_0 = input_para_0["read_frame"].copy()
        img_0 = cv2.resize(img_0, (width, height))

        img_1 = input_para_1["read_frame"].copy()
        img_1 = cv2.resize(img_1, (width, height))

        img_2 = input_para_2["read_frame"].copy()
        img_2 = cv2.resize(img_2, (width, height))

        img_3 = input_para_3["read_frame"].copy()
        img_3 = cv2.resize(img_3, (width, height))

        # 合成一张大图像
        top_row = np.hstack((img_0, img_1))
        bottom_row = np.hstack((img_2, img_3))
        result_image = np.vstack((top_row, bottom_row))
        cv2.imshow("result_image", result_image)

        input_para_0["read_frame_state"] = False
        # input_para_0["pause_state"] = True
        input_para_1["read_frame_state"] = False
        # input_para_1["pause_state"] = True
        input_para_2["read_frame_state"] = False
        # input_para_2["pause_state"] = True
        input_para_3["read_frame_state"] = False

        # img = cv2.imread("../m_data/aruco/bf/ex/camera0.jpg")
        # img = cv2.imread("charuco_board_19.jpg")
        # objPoints, imgPoints, charucoIds, img = aruco_tool.charuco_detect(img, True)
        # img = cv2.resize(img, (900, 600))
        # if objPoints is not None:
        #     objPoints = objPoints / 0.25 * board_size
        # cv2.imshow("RTSP Stream", img)
        # input_para["read_frame_state"] = False

        if cv2.waitKey(1) == ord('q'):
            break

    # 关闭所有窗口
    cv2.destroyAllWindows()


def runInCalib_test(mode, imgPath, imgPrefix, bResize, imgW, imgH, bW, bH, bSize, bNum, aruco_flag=False):
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
    args.IMAGE_FILE = ""
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


def calib_in_aruco():
    mode = "fisheye"
    mode_normal = "normal"
    precision = 0.9
    img_sizeLR_OLD = (2560, 1440)
    img_sizeML = (1920, 1080)
    img_sizeMR = (1920, 1080)
    img_sizeLR_NEW = (2960, 1664)
    # img_sizeML = img_sizeMR = img_sizeLR_NEW
    aruco_flag = True
    filePath = "../m_data/aruco/in"

    mtxL, distortionL, __, __, reProjectionErrorL = runInCalib_test(mode, filePath + "/L", "chessboard", False,
                                                                    img_sizeLR_NEW[0], img_sizeLR_NEW[1], bW, bH, bSize,
                                                                    bNum,
                                                                    aruco_flag)
    if mtxL is None or distortionL is None or reProjectionErrorL is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorL >= precision:
        return False, f"L ReProjectionError: {reProjectionErrorL}"
    print(f"L ReProjectionError: {reProjectionErrorL}")

    mtxML, distortionML, __, __, reProjectionErrorML = runInCalib_test(mode_normal, filePath + "/ML", "chessboard",
                                                                       False,
                                                                       img_sizeML[0], img_sizeML[1], bW, bH, bSize,
                                                                       bNum,
                                                                       aruco_flag)
    if mtxML is None or distortionML is None or reProjectionErrorML is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorML >= precision:
        return False, f"M ReProjectionError: {reProjectionErrorML}"
    print(f"ML ReProjectionError: {reProjectionErrorML}")

    mtxMR, distortionMR, __, __, reProjectionErrorMR = runInCalib_test(mode_normal, filePath + "/MR", "chessboard",
                                                                       False,
                                                                       img_sizeMR[0], img_sizeMR[1], bW, bH, bSize,
                                                                       bNum,
                                                                       aruco_flag)
    if mtxMR is None or distortionMR is None or reProjectionErrorMR is None:
        return False, f"L NoBoeardError"
    elif reProjectionErrorMR >= precision:
        return False, f"M ReProjectionError: {reProjectionErrorMR}"
    print(f"MR ReProjectionError: {reProjectionErrorMR}")

    mtxR, distortionR, __, __, reProjectionErrorR = runInCalib_test(mode, filePath + "/R", "chessboard", False,
                                                                    img_sizeLR_NEW[0], img_sizeLR_NEW[1], bW, bH, bSize,
                                                                    bNum,
                                                                    aruco_flag)
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


def calib_in_aruco_test():
    cmd = f"xcopy /E/Y ..\\m_data\\aruco\\bf\\in ..\\m_data\\aruco\\in"
    os.system(cmd)
    ret, calib_json = calib_in_aruco()
    with open("test/external_cfg.json", "w", encoding="utf-8") as f:
        f.write(calib_json)
    print(f"calib OK")


def calib_ex_aruco(img_0, img_1, mode="", save_path_1=None, save_path_2=None):
    check = True
    with open(in_cfg_path, 'r') as file:
        cfg_params = json.load(file)
    ex_calib.set_intrinsic_params(cfg_params)

    dirct_1, dirct_2, rotate_1, rotate_2, board_id, prefix = "left", "right", False, True, 6, ""  # 双鱼眼标定模式
    if mode == "left":  # 左边鱼眼+普通标定模式
        dirct_1, dirct_2, rotate_1, rotate_2, board_id, prefix = "left", "mid_left", False, False, 17, "left_"  # 左边鱼眼+普通标定模式
    elif mode == "right":  # 右边鱼眼+普通标定模式
        dirct_1, dirct_2, rotate_1, rotate_2, board_id, prefix = "right", "mid_right", True, True, 17, "right_"  # 右边鱼眼+普通标定模式

    ex_calib.show_img = np.zeros((3000, 2960, 3))

    ret, rvecs_1, tvecs_1, point_dict_1 = ex_calib.calibrate_aruco(dirct_1, img_0, dic_size=5, dic_num=1000,
                                                                   board_width=bW,
                                                                   board_height=bH, board_spacer=1, board_id=board_id,
                                                                   square_size=bSize, board_num=20,
                                                                   save_path=save_path_1, check_mode=True)


    if not ret:
        return
    print("L ex calib ok")

    ret, rvecs_2, tvecs_2, point_dict_2 = ex_calib.calibrate_aruco(dirct_2, img_1, dic_size=5, dic_num=1000,
                                                                   board_width=bW,
                                                                   board_height=bH, board_spacer=1, board_id=board_id,
                                                                   square_size=bSize, board_num=20,
                                                                   save_path=save_path_2,
                                                                   check_mode=True)  # "../m_data/aruco/ex/camera1.jpg")

    common_keys = set(point_dict_1.keys()) & set(point_dict_2.keys())
    # 输出具有相同键的元素
    distance = 0.0
    distance_count = 0
    for key in common_keys:
        distance += np.sqrt(np.sum((point_dict_1[key] - point_dict_2[key]) ** 2))
        distance_count += 1
    distance /= distance_count
    print(f"distance : {distance}")

    if not ret:
        return
    print("R ex calib ok")

    cfg_params[prefix + 'rvecs_1'] = rvecs_1.flatten().tolist()
    cfg_params[prefix + 'tvecs_1'] = tvecs_1.flatten().tolist()
    cfg_params[prefix + 'rvecs_2'] = rvecs_2.flatten().tolist()
    cfg_params[prefix + 'tvecs_2'] = tvecs_2.flatten().tolist()

    result_json = json.dumps(cfg_params, indent=4)
    print("JSON serialization successful.")
    with open(in_cfg_path, "w", encoding="utf-8") as f:
        f.write(result_json)

    if check:
        rvecs_mat_1, _ = cv2.Rodrigues(rvecs_1)
        cv2.invert(rvecs_mat_1, rvecs_mat_1)
        print(np.dot(rvecs_mat_1, tvecs_1))
        rvecs_mat_2, _ = cv2.Rodrigues(rvecs_2)
        cv2.invert(rvecs_mat_2, rvecs_mat_2)
        print(np.dot(rvecs_mat_2, tvecs_2))


def calib_ex_aruco_test():
    cmd = f"xcopy /E/Y ..\\m_data\\aruco\\bf\\ex ..\\m_data\\aruco\\ex"
    os.system(cmd)
    calib_ex_aruco(img_ex_L, img_ex_R, save_path_1="../m_data/aruco/ex/cameraL.jpg",
                   save_path_2="../m_data/aruco/ex/cameraR.jpg")
    calib_ex_aruco(img_ex_L, img_ex_ML, "left", "../m_data/aruco/ex/cameraL_L.jpg", "../m_data/aruco/ex/cameraML_L.jpg")

    print(f"calib OK")


def stitch_test(frame_1, frame_2, ex_internal_data_path):
    # frame_1 = np.zeros_like(frame_1)
    path_fisheye_dll = "../lib3rd/fisheye/video_fuse.dll"
    fisheye_dll = ctypes.CDLL(path_fisheye_dll)

    internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
    fisheye_dll.fisheye_initialize(internal_data_path)
    fisheye_dll.fisheye_external_initialize(internal_data_path)

    height = 1200
    width = 1600

    fisheye_dll.fisheye_run_yuv.restype = ctypes.c_char_p

    frame_1_stitch = np.zeros(dtype=np.uint8, shape=(height, width, 3))
    frame_2_stitch = np.zeros(dtype=np.uint8, shape=(height, width, 3))

    fisheye_dll.fisheye_set_winpos(22)
    fisheye_dll.fisheye_run_yuv_separate(frame_1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                         , frame_2.ctypes.data_as(C.POINTER(C.c_ubyte))
                                         , frame_1_stitch.ctypes.data_as(C.POINTER(C.c_ubyte))
                                         , frame_2_stitch.ctypes.data_as(C.POINTER(C.c_ubyte)))

    ex_calib.get_corners_aruco(frame_1_stitch, dic_size=5, dic_num=1000, board_width=bW,
                               board_height=bH, board_spacer=1, threshold_min=432, threshold_max=503,
                               square_size=bSize, board_num=20,
                               save_path=None)
    imgPoints_1 = ex_calib.imgPoints
    temp_id_list_1 = ex_calib.temp_id_list

    ex_calib.get_corners_aruco(frame_2_stitch, dic_size=5, dic_num=1000, board_width=bW,
                               board_height=bH, board_spacer=1, threshold_min=432, threshold_max=503,
                               square_size=bSize, board_num=20,
                               save_path=None)
    imgPoints_2 = ex_calib.imgPoints
    temp_id_list_2 = ex_calib.temp_id_list

    # stitch_image = cv2.resize(frame_1_stitch, (1600, 800))
    cv2.imshow("frame_1_stitch", frame_1_stitch)
    cv2.imshow("frame_2_stitch", frame_2_stitch)
    cv2.waitKey(0)


def stitch_show(frame_1, frame_2, ex_internal_data_path):
    path_fisheye_dll = "../lib3rd/fisheye/video_fuse_515.dll"
    fisheye_dll = ctypes.CDLL(path_fisheye_dll)

    internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
    fisheye_dll.fisheye_initialize(internal_data_path)
    fisheye_dll.fisheye_external_initialize(internal_data_path)

    height = 1200
    width = 1600

    fisheye_dll.fisheye_run_yuv.restype = ctypes.c_char_p

    stitch_image = np.zeros(dtype=np.uint8, shape=(height, width, 3))

    fisheye_dll.fisheye_set_winpos(22)
    fisheye_dll.fisheye_run_yuv(frame_1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , frame_2.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , stitch_image.ctypes.data_as(C.POINTER(C.c_ubyte)))

    stitch_image = cv2.resize(stitch_image, (1600, 800))
    cv2.imshow("stitch_image", stitch_image)
    cv2.waitKey(0)


def stitch_show_1(frame_1, frame_2, ex_internal_data_path):
    # frame_1 = np.zeros_like(frame_1)
    # frame_1 = np.ones_like(frame_1) * 254
    # frame_2 = np.zeros_like(frame_2)
    # frame_1 = np.zeros_like(frame_1)
    # frame_1[:, :, 2] = 254
    # frame_2 = np.zeros_like(frame_2)

    path_fisheye_dll = "../lib3rd/fisheye/video_fuse_515.dll"
    fisheye_dll = ctypes.CDLL(path_fisheye_dll)

    ex_internal_data_path_0 = "../configs/internal/external_cfg_90_L.json"
    internal_data_path = ex_internal_data_path_0.encode(encoding="utf-8", errors="ignore")
    fisheye_dll.fisheye_initialize(internal_data_path)
    fisheye_dll.fisheye_external_initialize(internal_data_path)

    height = 1200
    width = 1600

    fisheye_dll.fisheye_run_yuv.restype = ctypes.c_char_p

    # frame_2 = np.zeros_like(frame_2)
    stitch_image_src = np.zeros(dtype=np.uint8, shape=(height, width, 3))
    fisheye_dll.fisheye_set_winpos(22)
    fisheye_dll.fisheye_run_yuv(frame_1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , frame_2.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , stitch_image_src.ctypes.data_as(C.POINTER(C.c_ubyte)))

    internal_data_path = ex_internal_data_path.encode(encoding="utf-8", errors="ignore")
    fisheye_dll.fisheye_initialize(internal_data_path)
    fisheye_dll.fisheye_external_initialize(internal_data_path)

    frame_2 = np.zeros_like(frame_1)
    frame_2[:, :, 2] = 254
    frame_1 = np.ones_like(frame_2)
    stitch_image = np.zeros(dtype=np.uint8, shape=(height, width, 3))
    fisheye_dll.fisheye_set_winpos(22)
    fisheye_dll.fisheye_run_yuv(frame_1.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , frame_2.ctypes.data_as(C.POINTER(C.c_ubyte))
                                , stitch_image.ctypes.data_as(C.POINTER(C.c_ubyte)))
    # 遍历图像的每个像素
    for y in range(stitch_image.shape[0]):
        for x in range(stitch_image.shape[1]):
            # 如果像素点不合法
            if stitch_image[y, x, 0] != 0 and stitch_image[y, x, 0] == stitch_image[y, x, 2]:
                # 将该像素设置为黑色（[0, 0, 0]）
                stitch_image[y, x] = [0, 0, 0]

            stitch_image[y, x, 0] = stitch_image[y, x, 1] = stitch_image[y, x, 2]

            if not np.array_equal(stitch_image[y, x], np.array([0, 0, 0])):
                stitch_image_src[y, x] = (stitch_image_src[y, x] / 255 * stitch_image[y, x, 0]).astype(np.uint8)
    stitch_image_src = cv2.resize(stitch_image_src, (1600, 800))
    cv2.imshow("stitch_image", stitch_image_src)
    cv2.waitKey(0)


if __name__ == '__main__':
    # gen_test()
    # calib_in_aruco_test()
    # calib_ex_aruco_test()
    # stitch_show(img_ex_L, img_ex_R, in_cfg_path)
    play_test()
    # gen_test()
    # play_four()
    # frame_1 = cv2.imread("..\\m_data\\hqtest\\ex_L.jpg")
    # frame_2 = cv2.imread("..\\m_data\\hqtest\\ex_R.jpg")
    # stitch_show(frame_1, frame_2, "../configs/internal/external_cfg.json")
    # stitch_show_1(frame_1, frame_2, "../configs/internal/external_cfg_90.json")

