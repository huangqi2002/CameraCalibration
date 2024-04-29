import cv2
import cv2.aruco as aruco
import numpy as np


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
    def charuco_detect(self, img, paint=False):
        objPoints, imgPoints, ret_img = None, None, img.copy()
        charucoCorners, charucoIds, markerCorners, markerIds = self.charuco_detector.detectBoard(img)
        if charucoCorners is not None:
            objPoints, imgPoints = self.charuco_board.matchImagePoints(charucoCorners, charucoIds)
            # if charucoCorners.shape[0] >= 10:
            if paint:
                # self.draw_charuco_corners(ret_img, charucoCorners)
                cv2.aruco.drawDetectedCornersCharuco(ret_img, charucoCorners, charucoIds, cornerColor=(0, 255, 0))
                # cv2.aruco.drawDetectedMarkers(ret_img, markerCorners, markerIds)
                # print(charucoCorners)
        return objPoints, imgPoints, charucoIds, ret_img

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
