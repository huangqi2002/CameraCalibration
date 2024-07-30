import time

import cv2
import cv2.aruco as aruco
import numpy as np

from utils.run_para import m_global


# ARuco类
class aruco_vz():
    def __init__(self):
        self.aruco_dictionary = cv2.aruco.getPredefinedDictionary(aruco.DICT_4X4_50)

        self.aruco_parameters = aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector()

        self.charuco_board = cv2.aruco.CharucoBoard((2, 2), 1, 0.8, self.aruco_dictionary)
        self.charuco_detector = cv2.aruco.CharucoDetector(self.charuco_board)
        self.dict_sizes = {
            4: {50: aruco.DICT_4X4_50, 100: aruco.DICT_4X4_100, 250: aruco.DICT_4X4_250, 1000: aruco.DICT_4X4_1000},
            5: {50: aruco.DICT_5X5_50, 100: aruco.DICT_5X5_100, 250: aruco.DICT_5X5_250, 1000: aruco.DICT_5X5_1000},
            6: {50: aruco.DICT_6X6_50, 100: aruco.DICT_6X6_100, 250: aruco.DICT_6X6_250, 1000: aruco.DICT_6X6_1000},
            7: {50: aruco.DICT_7X7_50, 100: aruco.DICT_7X7_100, 250: aruco.DICT_7X7_250, 1000: aruco.DICT_7X7_1000}
        }

    def init(self):
        aruco_tool.set_aruco_dictionary(m_global.dicSize, 1000)
        aruco_tool.set_charuco_board((m_global.bW + 1,
                                      (m_global.bH + 1) * m_global.bNum + m_global.bSpacer * (
                                              m_global.bNum - 1)))

    # 根据尺寸，数量获取aruco字典
    def get_aruco_dictionary(self, size, count):
        if size not in self.dict_sizes or count not in self.dict_sizes[size]:
            raise ValueError("Invalid size or count")

        pre_dictionary = self.dict_sizes[size][count]
        return aruco.getPredefinedDictionary(pre_dictionary)

    # 设置aruco字典
    def set_aruco_dictionary(self, size, num):
        self.aruco_dictionary = self.get_aruco_dictionary(size, num)
        self.aruco_detector.setDictionary(self.aruco_dictionary)

    # 生成aruco
    def aruco_gen(self, marker_id, marker_size):
        # aruco id
        marker_id = 23
        # aruco 像素尺寸
        marker_size = 200
        # 生成aruco
        marker_image = aruco.generateImageMarker(self.aruco_dictionary, marker_id, marker_size)
        return marker_image

    # 检测aruco
    def aruco_detect(self, img, paint=False):
        marker_corners, marker_ids, _ = self.aruco_detector.detectMarkers(img)
        if paint:
            cv2.aruco.drawDetectedMarkers(img, marker_corners, marker_ids)

        return marker_corners, marker_ids

    # 设置 charuco board
    def set_charuco_board(self, size, squareLength=0.25, markerLength=0.2):
        # # 创建一个从 0 开始的一维数组，包含 9 * 6 = 54 个元素
        # ids_array = np.arange(3, 111)
        # # 将一维数组转换为九行六列的二维数组
        # ids = ids_array.reshape(9, 12)

        self.charuco_board = cv2.aruco.CharucoBoard(size, squareLength, markerLength, self.aruco_dictionary)
        self.charuco_detector.setBoard(self.charuco_board)

    # 绘制并保存Charuco板图像
    def charuco_gen(self, size, img_path="charuco_board.png"):
        charuco_board_img = self.charuco_board.generateImage(size)
        cv2.imwrite(img_path, charuco_board_img)
        return charuco_board_img

    def draw_charuco_corners(self, img, charuco_corners):
        num_points_list = len(charuco_corners)
        for i in range(num_points_list):
            # 获取点的数量
            num_points_ndarray = charuco_corners[i].shape[0]

            # 创建一个从浅到深的颜色列表
            colors = [(0, 0, int(i * 255)) for i in np.linspace(0.5, 1, num_points_ndarray)]
            # 绘制图像
            for j in range(num_points_ndarray):
                color = colors[j]
                point = tuple(map(int, charuco_corners[i][j][0]))
                color = colors[j]
                cv2.circle(img, point, 5, color, -1)

    def draw_marker_corners(self, img, marker_corners):
        # 获取点的数量
        num_points_list = len(marker_corners)

        # 创建一个从浅到深的颜色列表
        colors = [(0, int(i * 255), 0) for i in np.linspace(0, 1, num_points_list)]

        # 绘制图像
        for i in range(num_points_list):
            color = colors[i]
            for j in range(4):
                point = tuple(map(int, marker_corners[i][0, j]))
                cv2.circle(img, point, 5, color, -1)

    # 检测charuco

    # def charuco_detect(self, img, paint=False, minMarkerPerimeterRate=0.001):
    #     objPoints, imgPoints, ret_img = None, None, img.copy()
    #
    #     # 创建 DetectorParameters 对象并设置参数
    #     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #     # gray = img
    #     # cv2.imshow("gray", gray)
    #     # cv2.waitKey(0)
    #     parameters = self.charuco_detector.getDetectorParameters()
    #     # parameters.adaptiveThreshWinSizeMin = 3  # 自适应阈值窗口的最小大小
    #     # parameters.adaptiveThreshWinSizeMax = 23  # 自适应阈值窗口的最大大小
    #     parameters.minMarkerPerimeterRate = minMarkerPerimeterRate  # 最小标记周长比率
    #     parameters.maxMarkerPerimeterRate = 1.0
    #     parameters.max = 0.01
    #     self.charuco_detector.setDetectorParameters(parameters)
    #
    #     # gray = cv2.equalizeHist(gray)
    #     # gray = cv2.GaussianBlur(gray, (3, 3), 0)
    #     # for i in range(100):
    #     #     print(f"{i}", end=" ")
    #     #     gray_detect = cv2.resize(gray, (int(gray.shape[0]*(1 + i * 0.1)), int(gray.shape[1]*(1 + i * 0.1))))
    #     #     charucoCorners, charucoIds, markerCorners, markerIds = self.charuco_detector.detectBoard(gray_detect)
    #     #     if charucoCorners is not None:
    #     #         print(f"find ok i={i}")
    #
    #     charucoCorners, charucoIds, markerCorners, markerIds = self.charuco_detector.detectBoard(gray)
    #     # if markerCorners is not None:
    #
    #
    #     if charucoCorners is not None:
    #         objPoints, imgPoints = self.charuco_board.matchImagePoints(charucoCorners, charucoIds)
    #         # if charucoCorners.shape[0] >= 10:
    #         if paint:
    #             # self.draw_charuco_corners(ret_img, charucoCorners)
    #             cv2.aruco.drawDetectedCornersCharuco(ret_img, charucoCorners, charucoIds, cornerColor=(0, 255, 0))
    #             print(f"min : {markerIds.min()}   max : {markerIds.max()}   len : {markerIds.max() - markerIds.min() + 1}")
    #     if markerCorners is not None and paint:
    #         cv2.aruco.drawDetectedMarkers(ret_img, markerCorners, markerIds, borderColor=(255, 0, 0))
    #         ids = np.sort(markerIds.reshape(-1))
    #         print(ids)
    #     print(len(charucoCorners))
    #
    #     return objPoints, imgPoints, charucoIds, ret_img

    # 检测charuco
    def charuco_detect(self, img, paint=False, minMarkerPerimeterRate=0.001):
        objPoints, imgPoints, charuco_ids, ret_img = None, None, None, img.copy()

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 创建 DetectorParameters 对象并设置参数
        # 检测Markers角点
        parameters = cv2.aruco.DetectorParameters()
        parameters.minMarkerPerimeterRate = minMarkerPerimeterRate  # 最小标记周长比率
        src_markerCorners, src_markerIds, _ = cv2.aruco.detectMarkers(gray, self.aruco_dictionary, parameters=parameters)

        if src_markerCorners is not None:
            src_markerIds_0, src_markerIds_1 = np.empty((0, 1), dtype=np.int32), np.empty((0, 1), dtype=np.int32)
            src_markerCorners_0, src_markerCorners_1 = (), ()
            thr = ((m_global.bH + 1) * (m_global.bW + 1) / 2)
            src_marker = zip(src_markerIds, src_markerCorners)
            for markerid, markercorner in src_marker:
                if int(markerid[0] // thr) % 2 == 0:
                    src_markerIds_0 = np.concatenate((src_markerIds_0, [markerid]), axis=0)
                    src_markerCorners_0 = src_markerCorners_0 + tuple([markercorner])
                else:
                    src_markerIds_1 = np.concatenate((src_markerIds_1, [markerid]), axis=0)
                    src_markerCorners_1 = src_markerCorners_1 + tuple([markercorner])

            charuco_corners = np.empty((0, 1, 2), dtype=np.float32)
            charuco_ids = np.empty((0, 1), dtype=np.int32)
            if len(src_markerCorners_0) != 0:
                charuco_retval, temp_charuco_corners, temp_charuco_ids = cv2.aruco.interpolateCornersCharuco(src_markerCorners_0, src_markerIds_0, gray, self.charuco_board)
                if charuco_retval != 0:
                    charuco_corners = np.concatenate((charuco_corners, temp_charuco_corners), axis=0)
                    charuco_ids = np.concatenate((charuco_ids, temp_charuco_ids), axis=0)
            if len(src_markerCorners_1) != 0:
                charuco_retval, temp_charuco_corners, temp_charuco_ids = cv2.aruco.interpolateCornersCharuco(src_markerCorners_1, src_markerIds_1, gray, self.charuco_board)
                if charuco_retval != 0:
                    charuco_corners = np.concatenate((charuco_corners, temp_charuco_corners), axis=0)
                    charuco_ids = np.concatenate((charuco_ids, temp_charuco_ids), axis=0)

            if len(charuco_corners) == 0:
                return objPoints, imgPoints, charuco_ids, ret_img

            objPoints, imgPoints = self.charuco_board.matchImagePoints(charuco_corners, charuco_ids)
            if paint:
                cv2.aruco.drawDetectedCornersCharuco(ret_img, charuco_corners, charuco_ids, cornerColor=(0, 255, 0))
                cv2.aruco.drawDetectedMarkers(ret_img, src_markerCorners, src_markerIds, borderColor=(255, 0, 0))

        return objPoints, imgPoints, charuco_ids, ret_img

    # 设置artah 参数
    # 创建 DetectorParameters 对象并设置参数
    # parameters = aruco.DetectorParameters_create()
    # parameters.adaptiveThreshWinSizeMin = 3  # 自适应阈值窗口的最小大小
    # parameters.adaptiveThreshWinSizeMax = 23  # 自适应阈值窗口的最大大小
    # parameters.adaptiveThreshWinSizeStep = 10  # 自适应阈值窗口大小的步长
    # parameters.minMarkerPerimeterRate = 0.03  # 最小标记周长比率
    # parameters.maxMarkerPerimeterRate = 4.0  # 最大标记周长比率
    # parameters.polygonalApproxAccuracyRate = 0.05  # 多边形逼近的精度率
    # parameters.minCornerDistanceRate = 0.05  # 最小角距离比率
    # parameters.minDistanceToBorder = 3  # 到图像边界的最小距离
    # parameters.minMarkerDistanceRate = 0.05  # 最小标记之间的距离比率
    # parameters.cornerRefinementWinSize = 5  # 角点细化窗口的大小
    # parameters.cornerRefinementMaxIterations = 30  # 角点细化的最大迭代次数
    # parameters.cornerRefinementMinAccuracy = 0.1  # 角点细化的最小精度
    # parameters.markerBorderBits = 1  # 标记边界的位数


aruco_tool = aruco_vz()
