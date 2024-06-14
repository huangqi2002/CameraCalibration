import copy
import json
import os
import random

import numpy as np
import cv2

from server.aruco_vz import aruco_tool
from server.internal.boardSplit import getBoardPosition


class ExternalCalibrator:
    def __init__(self, point_id_list=None, objectPoints=None, imgPoints=None, intrinsic_params=None):
        self.point_id_list = point_id_list
        self.objectPoints = objectPoints
        self.imgPoints = imgPoints
        self.intrinsic_params = intrinsic_params
        self.show_img = np.zeros((3000, 2960, 3))

        self.perspec_point = None
        self.undistorted_img = None

    def set_intrinsic_params(self, internal_cfg):
        self.intrinsic_params = internal_cfg
        # with open(internal_cfg_path, 'r') as file:
        #     self.intrinsic_params = json.load(file)

    def get_corners_aruco(self, img, dic_size=5, dic_num=1000, board_width=11, board_height=8, board_spacer=1,
                          board_id=-1, square_size=25, board_num=10, save_path=None, rotate=False):
        ok = False
        threshold = board_width * (board_height + 2)
        if board_id < 0:
            threshold_min = 0
            threshold_max = threshold * board_num
        else:
            threshold_min = threshold * board_id
            threshold_max = threshold * (board_id + 1) - 1
        # img = cv2.imread("../m_data/aruco/bf/in/L/chessboard_1714387592.jpg")
        aruco_tool.set_aruco_dictionary(dic_size, dic_num)
        aruco_tool.set_charuco_board((board_width + 1, (board_height + 1) * board_num + board_spacer * (board_num - 1)))

        # objPoints, imgPoints, charucoIds, img = aruco_tool.charuco_detect(img, True)

        objPoints, imgPoints, charucoIds, ret_img = aruco_tool.charuco_detect(img, False)
        if objPoints is None:
            return ok

        threshold = board_width * (board_height + 1 + board_spacer)

        # 初始化一个列表来存储十个组
        temp_id_list = [np.empty((0, 1, 1)) for _ in range(board_num)]
        temp_obj_point_list = [np.empty((0, 1, 3)) for _ in range(board_num)]
        temp_img_point_list = [np.empty((0, 1, 2)) for _ in range(board_num)]

        # 将 objPoints 和 charucoIds 进行 zip，得到每个点对应的 charucoId
        points_with_charuco_ids = zip(objPoints, imgPoints, charucoIds)

        # 判断方向
        board_dict = [0, 0, 0, 0]

        # 分组并筛选出满足条件的非空组
        for obj_point, img_point, ids in points_with_charuco_ids:
            if ids is not None and threshold_min <= ids[0] <= threshold_max:
                temp_ids = ids[0] // threshold
                temp_id_list[temp_ids] = np.vstack([temp_id_list[temp_ids], np.array(ids[0]).reshape(1, 1, 1)])
                begin_point = np.array([0, (board_height + board_spacer + 1) * temp_ids * 0.25, 0])
                temp_obj_point_list[temp_ids] = np.vstack(
                    [temp_obj_point_list[temp_ids],
                     ((obj_point[0] - begin_point).reshape(1, 1, -1) / 0.25 * square_size)])

                temp_img_point_list[temp_ids] = np.vstack(
                    [temp_img_point_list[temp_ids], img_point[0].reshape(1, 1, -1)])

                if board_id >= 0:
                    if (ids[0] - 1) in temp_id_list[temp_ids] and (ids[0] % board_width != 0):
                        temp_dict = (temp_img_point_list[temp_ids][-1] - temp_img_point_list[temp_ids][-2])[0]
                        if abs(temp_dict[0]) > abs(temp_dict[1]):
                            if temp_dict[0] > 0:  # 无需旋转
                                board_dict[0] += 1
                            else:  # 顺转180
                                board_dict[2] += 1
                        else:
                            if temp_dict[1] > 0:  # 顺转90
                                board_dict[3] += 1
                            else:  # 顺转270
                                board_dict[1] += 1

        board_dict_index = board_dict.index(max(board_dict))
        if rotate:
            board_dict_index = (board_dict_index + rotate * 2) % 4
        # print(f"board_dict_index : {board_dict_index}")

        # 过滤掉为空的组
        self.objectPoints = [arr.astype(np.float32) for arr in temp_obj_point_list if arr.size > 0]
        self.point_id_list = [arr.astype(np.float32) for arr in temp_id_list if arr.size > 0]

        self.imgPoints = [arr.astype(np.float32) for arr in temp_img_point_list if arr.size > 0]

        if save_path is not None:
            aruco_tool.draw_charuco_corners(ret_img, self.imgPoints)
            cv2.imwrite(save_path, ret_img)

        if len(self.objectPoints) > 0:
            ok = True

            # print(f"board_dict_index : {board_dict_index}")
            end_point = np.array([(board_width + 1) * square_size, (board_height + 1) * square_size, 0])
            if board_dict_index == 1:  # 顺转90
                self.objectPoints[0][:, :, 0:2] = np.flip(self.objectPoints[0][:, :, 0:2], 2)
                self.objectPoints[0][:, :, 1] = end_point[1] - self.objectPoints[0][:, :, 1]
            elif board_dict_index == 2:  # 顺转180
                end_point = np.array([(board_width + 1) * square_size, (board_height + 1) * square_size, 0])
                self.objectPoints[0] = end_point - self.objectPoints[0]
            elif board_dict_index == 3:  # 顺转270
                # self.objectPoints[0] = np.flip(self.objectPoints[0], 2)
                self.objectPoints[0][:, :, 0:2] = np.flip(self.objectPoints[0][:, :, 0:2], 2)
                self.objectPoints[0][:, :, 0] = end_point[0] - self.objectPoints[0][:, :, 0]
        return ok

    def get_corners(self, img, board_width=11, board_height=8, square_size=25, save_path=None):
        _, ex_img = getBoardPosition(img, (board_width, board_height), save_path, find_ex_board=True, path_bool=False)

        # 寻找并绘制每个棋盘格的角点
        ret, corners = cv2.findChessboardCorners(ex_img, (board_width, board_height),
                                                 flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_FAST_CHECK)
        self.objectPoints = [np.array([[(j * square_size, i * square_size, 0.)] for i in range(board_height)
                                       for j in range(board_width)], dtype=np.float32)]
        self.imgPoints = [corners]
        self.point_id_list = [np.array([(j + i * board_width) for i in range(board_height)
                                        for j in range(board_width)], dtype=np.float32)]
        ok = False
        if len(self.objectPoints) > 0:
            ok = True
        return ok

    #
    #     aruco_tool.set_aruco_dictionary(dic_size, dic_num)
    #     aruco_tool.set_charuco_board((board_width + 1, (board_height + 1) * board_num + board_spacer * (board_num - 1)))
    #
    #     # objPoints, imgPoints, charucoIds, img = aruco_tool.charuco_detect(img, True)
    #
    #     objPoints, imgPoints, charucoIds, ret_img = aruco_tool.charuco_detect(img, False)
    #     threshold = board_width * (board_height + 1 + board_spacer)
    #
    #     # 初始化一个列表来存储十个组
    #     temp_id_list = [np.empty((0, 1, 1)) for _ in range(board_num)]
    #     temp_obj_point_list = [np.empty((0, 1, 3)) for _ in range(board_num)]
    #     temp_img_point_list = [np.empty((0, 1, 2)) for _ in range(board_num)]
    #
    #     # 将 objPoints 和 charucoIds 进行 zip，得到每个点对应的 charucoId
    #     points_with_charuco_ids = zip(objPoints, imgPoints, charucoIds)
    #
    #     # 分组并筛选出满足条件的非空组
    #     for obj_point, img_point, ids in points_with_charuco_ids:
    #         if ids is not None and threshold_min <= ids[0] <= threshold_max:
    #             temp_ids = ids[0] // threshold
    #             temp_id_list[temp_ids] = np.vstack([temp_id_list[temp_ids], np.array(ids[0]).reshape(1, 1, 1)])
    #             begin_point = np.array([0, 8 * temp_ids * 0.25, 0])
    #             temp_obj_point_list[temp_ids] = np.vstack(
    #                 [temp_obj_point_list[temp_ids],
    #                  ((obj_point[0] - begin_point).reshape(1, 1, -1) / 0.25 * square_size)])
    #
    #             temp_img_point_list[temp_ids] = np.vstack(
    #                 [temp_img_point_list[temp_ids], img_point[0].reshape(1, 1, -1)])
    #
    #     # 过滤掉为空的组
    #     self.objectPoints = [arr.astype(np.float32) for arr in temp_obj_point_list if arr.size > 0]
    #     self.point_id_list = [arr.astype(np.float32) for arr in temp_id_list if arr.size > 0]
    #
    #     self.imgPoints = [arr.astype(np.float32) for arr in temp_img_point_list if arr.size > 0]
    #
    #     if save_path is not None:
    #         aruco_tool.draw_charuco_corners(ret_img, self.imgPoints)
    #         cv2.imwrite(save_path, ret_img)
    #
    #     ok = False
    #     if len(self.objectPoints) > 0:
    #         ok = True
    #     return ok

    def calibrate_aruco(self, dirct, img, dic_size=5, dic_num=1000, board_width=11, board_height=8, board_spacer=1,
                        board_id=0, square_size=25, board_num=10, save_path=None, check_mode=False, rotate=False):
        self.perspec_point = {}
        ret, rvecs, tvecs, point_dict = False, None, None, {}
        if dirct is None or self.intrinsic_params is None:
            return ret, rvecs, tvecs
        dirct_calib = dirct + "_calib"
        if dirct_calib not in self.intrinsic_params:
            return ret, rvecs, tvecs

        intrinsic_params_dirct = self.intrinsic_params[dirct_calib]
        # 内参
        mtx = np.array(intrinsic_params_dirct[2:11]).reshape(3, 3)
        dist = np.array(intrinsic_params_dirct[11:])
        dist_e = np.zeros_like(dist)

        # 图像去畸变
        if dirct == "left" or dirct == "right":
            new_size = (img.shape[1], img.shape[0])
            # 畸变校正
            new_camera_matrix = np.multiply(mtx, [[0.6, 1, 1], [1, 0.6, 1], [1, 1, 1]])
            mapx, mapy = cv2.fisheye.initUndistortRectifyMap(mtx, dist, np.eye(3), new_camera_matrix, new_size, cv2.CV_32FC1)
            self.undistorted_img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
        else:
            new_size = (img.shape[1], img.shape[0])
            # 畸变校正
            new_camera_matrix = np.multiply(mtx, [[0.8, 1, 1], [1, 0.8, 1], [1, 1, 1]])
            mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, np.eye(3), new_camera_matrix, new_size, cv2.CV_32FC1)
            self.undistorted_img = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)

        ok = self.get_corners_aruco(img, dic_size, dic_num, board_width, board_height, board_spacer, board_id,
                                    square_size,
                                    board_num, save_path, rotate=rotate)
        # 亚像素级别的角点优化
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        color = (0, 0.5, 0)
        # img = cv2.imread("../m_data/hqtest/690/ex_R_ss.jpg")
        # if dirct == "left":
        #     color = (0, 0, 0.5)
        #     img = cv2.imread("../m_data/hqtest/690/ex_L_ss.jpg")

        if ok:
            temp_imgPoints = copy.deepcopy(self.imgPoints)
            perspec_points = copy.deepcopy(self.imgPoints)

            for i in range(len(self.imgPoints)):
                PointsNdarray = self.imgPoints[i]
                PointsNdarray_perspec = perspec_points[i]
                # 亚像素级别的角点优化
                PointsNdarray = cv2.cornerSubPix(gray, PointsNdarray, (11, 11), (-1, -1), criteria)
                PointsNdarray_perspec = cv2.cornerSubPix(gray, PointsNdarray_perspec, (11, 11), (-1, -1), criteria)
                if dirct == "left" or dirct == "right":
                    cv2.fisheye.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, P=mtx)
                    mtx_p = mtx.copy()
                    mtx_p[0, 0] *= 0.6
                    mtx_p[1, 1] *= 0.6
                    cv2.fisheye.undistortPoints(PointsNdarray_perspec, mtx, dist, PointsNdarray_perspec, P=mtx_p)
                else:
                    cv2.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, P=mtx)
                    mtx_p = mtx.copy()
                    mtx_p[0, 0] *= 0.8
                    mtx_p[1, 1] *= 0.8
                    cv2.undistortPoints(PointsNdarray_perspec, mtx, dist, PointsNdarray_perspec, P=mtx_p)

                # points = PointsNdarray[:, 0, :]
                # # 使用广播将每个点的坐标进行相应的转换
                # points[:, 0] = points[:, 0] * mtx[0][0] + mtx[0][2]
                # points[:, 1] = points[:, 1] * mtx[1][1] + mtx[1][2]
                # PointsNdarray[:, 0, :] = points

                for j in range(PointsNdarray.shape[0]):
                    points = PointsNdarray[j][0]
                    if j == 0:
                        cv2.circle(self.show_img, (int(points[0]), int(points[1])), 5, (1, 1, 1), -1)
                    else:
                        cv2.circle(self.show_img, (int(points[0]), int(points[1])), 5, color, -1)

            color = [i * 2 for i in color]
            ret, rvecs, tvecs = cv2.solvePnP(self.objectPoints[0], self.imgPoints[0], mtx, dist_e)
            # rvecs = tvecs = np.zeros((3, 1))
            # print(temp_rvecs)
            # for i in range(len(self.objectPoints)):
            #     # if i == 0:
            #     #     continue
            #     ret, temp_rvecs, temp_tvecs = cv2.solvePnP(self.objectPoints[i], self.imgPoints[i], mtx, dist_e)
            #     # rvecs += temp_rvecs
            #     print(temp_rvecs)
            #     if i == 0:
            #         tvecs = temp_tvecs
            #         rvecs = temp_rvecs
            # # rvecs /= 2

            if check_mode:  # 检查模式
                rvecs_mat, _ = cv2.Rodrigues(rvecs)
                cv2.invert(rvecs_mat, rvecs_mat)
                tvecs_1 = np.dot(rvecs_mat, tvecs)
                print(tvecs_1)

                for i in range(len(temp_imgPoints)):
                    PointsNdarray = temp_imgPoints[i]
                    PointsIdNdarray = self.point_id_list[i]

                    PointsNdarray_perspec = perspec_points[i]

                    if dirct == "left" or dirct == "right":
                        cv2.fisheye.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, rvecs_mat)
                    else:
                        cv2.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, rvecs_mat)

                    for j in range(PointsNdarray.shape[0]):
                        points = PointsNdarray[j][0]
                        point_id = PointsIdNdarray[j][0][0]

                        points_perspec = PointsNdarray_perspec[j][0]

                        points[0] = (points[0] - 1 * tvecs_1[0] / 1000) * (tvecs_1[2] / 1000) + 0.1
                        points[1] = (points[1] - 1 * tvecs_1[1] / 1000) * (tvecs_1[2] / 1000) + 0.1

                        point_dict[f"{point_id}"] = points
                        self.perspec_point[f"{point_id}"] = points_perspec

                        # print(points)
                        if j == 0:
                            cv2.circle(self.show_img, (int(points[0] * 1000), int(points[1] * 1000)), 5, (1, 1, 1), -1)
                        else:
                            cv2.circle(self.show_img, (int(points[0] * 1000), int(points[1] * 1000)), 5, color, -1)
                show_img = cv2.resize(self.show_img, (600, 400))
                # cv2.imshow("show_img_1", show_img)
                # cv2.waitKey(0)
                show_img *= 255
                cv2.imwrite(f"./result/{board_id}_{dirct}_check.jpg", show_img)

        # 返回结果
        return ret, rvecs, tvecs, point_dict

    def calibrate(self, dirct, img, board_width=11, board_height=8, square_size=25, save_path=None, check_mode=False):
        ret, rvecs, tvecs, point_dict = False, None, None, {}
        if self.intrinsic_params is None:
            return ret, rvecs, tvecs
        dirct_calib = dirct + "_calib"
        if dirct_calib not in self.intrinsic_params:
            return ret, rvecs, tvecs

        intrinsic_params_dirct = self.intrinsic_params[dirct_calib]
        # 内参
        mtx = np.array(intrinsic_params_dirct[2:11]).reshape(3, 3)
        dist = np.array(intrinsic_params_dirct[11:])
        dist_e = np.zeros_like(dist)

        ok = self.get_corners(img, board_width, board_height, square_size, save_path)
        # 亚像素级别的角点优化
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        color = (0, 0.5, 0)

        if ok:
            temp_imgPoints = copy.deepcopy(self.imgPoints)
            for i in range(len(self.imgPoints)):
                PointsNdarray = self.imgPoints[i]
                # 亚像素级别的角点优化
                PointsNdarray = cv2.cornerSubPix(gray, PointsNdarray, (11, 11), (-1, -1), criteria)
                if dirct == "left" or dirct == "right":
                    cv2.fisheye.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray)
                else:
                    cv2.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray)

                points = PointsNdarray[:, 0, :]
                # 使用广播将每个点的坐标进行相应的转换
                points[:, 0] = points[:, 0] * mtx[0][0] + mtx[0][2]
                points[:, 1] = points[:, 1] * mtx[1][1] + mtx[1][2]
                PointsNdarray[:, 0, :] = points

                for j in range(PointsNdarray.shape[0]):
                    points = PointsNdarray[j][0]
                    if j == 0:
                        cv2.circle(self.show_img, (int(points[0]), int(points[1])), 5, (1, 1, 1), -1)
                    else:
                        cv2.circle(self.show_img, (int(points[0]), int(points[1])), 5, color, -1)

            color = [i * 2 for i in color]
            ret, rvecs, tvecs = cv2.solvePnP(self.objectPoints[0], self.imgPoints[0], mtx, dist_e)

            if check_mode:  # 检查模式
                rvecs_mat, _ = cv2.Rodrigues(rvecs)
                cv2.invert(rvecs_mat, rvecs_mat)
                tvecs_1 = np.dot(rvecs_mat, tvecs)
                print(tvecs_1)

                for i in range(len(temp_imgPoints)):
                    PointsNdarray = temp_imgPoints[i]
                    PointsIdNdarray = self.point_id_list[i]

                    if dirct == "left" or dirct == "right":
                        cv2.fisheye.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, rvecs_mat)
                    else:
                        cv2.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray, rvecs_mat)

                    for j in range(PointsNdarray.shape[0]):
                        points = PointsNdarray[j][0]
                        point_id = PointsIdNdarray[j]

                        points[0] = (points[0] - 1 * tvecs_1[0] / 1000) * (tvecs_1[2] / 1000) + 0.1
                        points[1] = (points[1] - 1 * tvecs_1[1] / 1000) * (tvecs_1[2] / 1000) + 0.1

                        point_dict[f"{point_id}"] = points
                        # print(points)
                        if j == 0:
                            cv2.circle(self.show_img, (int(points[0] * 1000), int(points[1] * 1000)), 5, (1, 1, 1), -1)
                        else:
                            cv2.circle(self.show_img, (int(points[0] * 1000), int(points[1] * 1000)), 5, color, -1)
                show_img = cv2.resize(self.show_img, (600, 400))
                # cv2.imshow("show_img_1", show_img)
                # cv2.waitKey(0)
                show_img *= 255
                cv2.imwrite(f"./result/{os.path.basename(save_path)}_{dirct}_check.jpg", show_img)

        # 返回结果
        return ret, rvecs, tvecs, point_dict

    def calibrate_src(self, dirct, img, dic_size=5, dic_num=1000, board_width=11, board_height=8, board_spacer=1,
                      board_id=0, square_size=25, board_num=10, save_path=None):
        ret, rvecs, tvecs = False, None, None
        if dirct is None or self.intrinsic_params is None:
            return ret, rvecs, tvecs
        dirct_calib = dirct + "_calib"
        if dirct_calib not in self.intrinsic_params:
            return ret, rvecs, tvecs

        intrinsic_params_dirct = self.intrinsic_params[dirct_calib]
        # 内参
        mtx = np.array(intrinsic_params_dirct[2:11]).reshape(3, 3)
        dist = np.array(intrinsic_params_dirct[11:])
        dist_e = np.zeros_like(dist)

        # 寻找角点
        if self.get_corners_aruco(img, dic_size, dic_num, board_width, board_height, board_spacer, board_id,
                                  square_size,
                                  board_num, save_path):
            # 亚像素级别的角点优化
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 1e-6)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            for i in range(len(self.imgPoints)):
                PointsNdarray = self.imgPoints[i]
                # 亚像素级别的角点优化
                PointsNdarray = cv2.cornerSubPix(gray, PointsNdarray, (11, 11), (-1, -1), criteria)
                if dirct == "left" or dirct == "right":
                    cv2.fisheye.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray)
                else:
                    cv2.undistortPoints(PointsNdarray, mtx, dist, PointsNdarray)

                for j in range(PointsNdarray.shape[0]):
                    points = PointsNdarray[j][0]
                    points[0] = points[0] * mtx[0][0] + mtx[0][2]
                    points[1] = points[1] * mtx[1][1] + mtx[1][2]

            rvecs = tvecs = np.zeros((3, 1))
            for i in range(len(self.objectPoints)):
                ret, temp_rvecs, temp_tvecs = cv2.solvePnP(self.objectPoints[i], self.imgPoints[i], mtx, dist_e)
                # rvecs += temp_rvecs
                print(temp_rvecs)
                if i == 0:
                    tvecs = temp_tvecs
                    rvecs = temp_rvecs
            # rvecs /= 2

        # 返回结果
        return ret, rvecs, tvecs


ex_calib = ExternalCalibrator()
