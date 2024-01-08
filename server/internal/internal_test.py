import cv2
import os
import numpy as np
from ExtrinsicCalibration import ExCalibrator
from IntrinsicCalibration import InCalibrator, CalibMode
from cv2 import imwrite


def runInCalib_1():
    print("Intrinsic Calibration ......")
    calibrator = InCalibrator('fisheye')  # 初始化内参标定器
    PATH = 'IntrinsicCalibration/data/'
    images = os.listdir(PATH)
    for img in images:
        print(PATH + img)
        raw_frame = cv2.imread(PATH + img)
        result = calibrator(raw_frame)  # 每次读入一张原始图片 更新标定结果

    print("Camera Matrix is : {}".format(result.camera_mat.tolist()))
    print("Distortion Coefficient is : {}".format(result.dist_coeff.tolist()))
    print("Reprojection Error is : {}".format(np.mean(result.reproj_err)))

    raw_frame = cv2.imread('IntrinsicCalibration/data/img_raw0.jpg')
    cv2.imshow("Raw Image", raw_frame)
    undist_img = calibrator.undistort(raw_frame)  # 使用undistort方法得到去畸变图像
    cv2.imshow("Undistorted Image", undist_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def runInCalib_2(mode, imgPath, imgPrefix, bResize, imgW, imgH, bW, bH, bSize):
    print("Intrinsic Calibration ......")
    args = InCalibrator.get_args()  # 获取内参标定args参数
    args.INPUT_PATH = imgPath  # 修改为新的参数
    args.IMAGE_FILE = imgPrefix
    args.RESIZE_FLAG = bResize
    args.FRAME_WIDTH = imgW
    args.FRAME_HEIGHT = imgH
    args.BORAD_WIDTH = bW
    args.BORAD_HEIGHT = bH
    args.SQUARE_SIZE = bSize
    calibrator = InCalibrator(mode)  # 初始化内参标定器
    calib = CalibMode(calibrator, 'image', 'auto')  # 选择标定模式
    result = calib()  # 开始标定

    print("Camera Matrix is : {}".format(result.camera_mat.tolist()))
    print("Distortion Coefficient is : {}".format(result.dist_coeff.tolist()))
    print("Reprojection Error is : {}".format(np.mean(result.reproj_err)))

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return result.camera_mat, result.dist_coeff, calibrator.borad, calibrator.corners


def runExCalib():
    print("Extrinsic Calibration ......")
    exCalib = ExCalibrator()  # 初始化外参标定器

    src_raw = cv2.imread('ExtrinsicCalibration/data/img_src_back.jpg')
    dst_raw = cv2.imread('ExtrinsicCalibration/data/img_dst_back.jpg')

    homography = exCalib(src_raw, dst_raw)  # 输入对应的两张去畸变图像 得到单应性矩阵
    print("Homography Matrix is:")
    print(homography.tolist())

    src_warp = exCalib.warp()  # 使用warp方法得到原始图像的变换结果

    cv2.namedWindow("Source View", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow("Source View", src_raw)
    cv2.namedWindow("Destination View", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow("Destination View", dst_raw)
    cv2.namedWindow("Warped Source View", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.imshow("Warped Source View", src_warp)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def stitch_test(filePath):
    mode = "fisheye"
    img_sizeL = (2560, 1440)
    img_sizeM = (1920, 1080)
    img_sizeR = (2560, 1440)

    mtxL, __, __, __ = runInCalib_2(mode, filePath + "/L", "ispPlayer", False, img_sizeL[0], img_sizeL[1], 11, 8, 25)
    mtxM, __, __, __ = runInCalib_2(mode, filePath + "/M", "ispPlayer", False, img_sizeM[0], img_sizeM[1], 11, 8, 25)
    mtxR, __, __, __ = runInCalib_2(mode, filePath + "/R", "ispPlayer", False, img_sizeR[0], img_sizeR[1], 11, 8, 25)

    cv2.waitKey(0)


def dup_mapToFile(path, mapX, mapY):
    mapX = mapX.reshape(-1, 1)
    mapY = mapY.reshape(-1, 1)
    print(mapX[0], mapY[0])
    map = np.hstack((mapX, mapY))
    map = map.flatten()
    mapfile = open(path, 'wb')
    mapfile.write(map)
    mapfile.close()


def dup_get_dispImg(lImg, rImg, dispPath):
    window_size = 7  # 匹配的块大小 > = 1的奇数
    min_disp = 16  # 最小可能的差异值
    num_disp = 192 - min_disp  # 最大差异减去最小差异
    uniquenessRatio = 1  # 最佳（最小）计算成本函数值
    speckleRange = 3  # 每个连接组件内的最大视差变化
    speckleWindowSize = 3  # 平滑视差区域的最大尺寸
    disp12MaxDiff = 200  # 左右视差检查中允许的最大差异
    P1 = 600  # 控制视差平滑度的第一个参数
    P2 = 2400  # 第二个参数控制视差平滑度
    imgL = cv2.imread(lImg)  # 左目图像
    imgR = cv2.imread(rImg)  # 右目图像
    # 创建StereoSGBM对象并计算
    stereo = cv2.StereoSGBM_create(minDisparity=min_disp, numDisparities=num_disp, blockSize=window_size,
                                   uniquenessRatio=uniquenessRatio, speckleRange=speckleRange,
                                   speckleWindowSize=speckleWindowSize, disp12MaxDiff=disp12MaxDiff, P1=P1, P2=P2)
    disp = stereo.compute(imgL, imgR).astype(np.float32) / 16.0  # 计算视差图
    disp = (disp - min_disp) / num_disp
    # disp = (disp * 255).astype(np.uint8)
    cv2.imwrite(dispPath, disp)
    cv2.imshow('Depth Image SGBM', disp)  # 显示视差图结果

    cv2.waitKey(0)


def dpu_test():
    mode = "normal"
    img_size = (1280, 720)
    file_root = "F:/ISP/DV500/DPU/GC4653"

    mtxL, distL, obj_pointsL, img_pointsL = runInCalib_2(mode, file_root + "/L", "ispPlayer", True, img_size[0],
                                                         img_size[1], 11, 8, 25)
    mtxR, distR, __, img_pointsR = runInCalib_2(mode, file_root + "/R", "ispPlayer", True, img_size[0], img_size[1], 11,
                                                8, 25)

    args = {}
    args["mtxL"] = mtxL
    args["distL"] = distL
    args["obj_pointsL"] = obj_pointsL
    args["img_pointsL"] = img_pointsL
    args["mtxR"] = mtxR
    args["distR"] = distR
    args["img_pointsR"] = img_pointsR
    np.save(file_root + "/OUT/args.npy", args)

    ret, M1, D1, M2, D2, R, T, E, F = cv2.stereoCalibrate(obj_pointsL, img_pointsL, img_pointsR, mtxL, distL, mtxR,
                                                          distR, img_size)
    R1, R2, P1, P2, Q, roi_left, roi_right = cv2.stereoRectify(mtxL, distL, mtxR, distR, img_size, R, T,
                                                               flags=cv2.CALIB_ZERO_DISPARITY)
    mapXL, mapYL = cv2.initUndistortRectifyMap(M1, D1, R1, P1, img_size, cv2.CV_32FC1)
    mapXR, mapYR = cv2.initUndistortRectifyMap(M2, D2, R2, P2, img_size, cv2.CV_32FC1)

    dup_mapToFile(file_root + "/OUT/rx5_720P_L.bin", mapXL, mapYL)
    dup_mapToFile(file_root + "/OUT/rx5_720P_R.bin", mapXR, mapYR)

    inImgL = cv2.imread(file_root + "/TEST/YUV_L.bmp")
    outImgL = cv2.remap(inImgL, mapXL, mapYL, cv2.INTER_LINEAR)
    inImgR = cv2.imread(file_root + "/TEST/YUV_R.bmp")
    outImgR = cv2.remap(inImgR, mapXR, mapYR, cv2.INTER_LINEAR)
    outImg = np.hstack((outImgL, outImgR))
    cv2.imwrite(file_root + "/OUT/Map_L.jpg", outImgL);
    cv2.imwrite(file_root + "/OUT/Map_R.jpg", outImgR);
    showImg = cv2.resize(outImg, (1920, 1080))
    cv2.imshow("outImg", showImg)
    cv2.waitKey(0)


def vz_stitch():
    img_size = (2960, 1664)
    mtx = np.float32(
        [[1068.334332, 0.000000, 1516.338828], [0.000000, 1067.451740, 695.934544], [0.000000, 0.000000, 1.000000]])
    dist = np.float32([-0.022859, 0.011520, -0.016736, 0.006746])
    mapX, mapY = cv2.initUndistortRectifyMap(mtx, dist, None, mtx, img_size, cv2.CV_32FC1)


def main():
    # file_root = "F:/ISP/DV500/DPU/GC4653"
    # dpu_test()
    # dup_get_dispImg(file_root + "/OUT/Map_L.jpg", file_root + "/OUT/Map_R.jpg", file_root + "/OUT/disp.jpg")
    filePath = "data_test/W"
    stitch_test(filePath)


if __name__ == '__main__':
    main()
