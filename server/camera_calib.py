import copy

import cv2
import numpy as np

from utils.run_para import m_global


class Calib_Data:
    def __init__(self):
        self.type = None
        self.camera_mat = None
        self.dist_coeff = None
        self.rvecs = None
        self.tvecs = None
        self.reproj_err = None
        self.ok = False
        self.check = True


def split_points(obj_point_list, img_point_list, test_size=0.2, random_state=None):
    if random_state is not None:
        np.random.seed(random_state)

    obj_train, obj_test, img_train, img_test = [], [], [], []

    for obj_points, img_points in zip(obj_point_list, img_point_list):
        num_points = len(obj_points)
        indices = np.arange(num_points)
        np.random.shuffle(indices)

        test_count = int(num_points * test_size)
        test_indices = indices[:test_count]
        train_indices = indices[test_count:]

        obj_train.append(obj_points[train_indices])
        obj_test.append(obj_points[test_indices])
        img_train.append(img_points[train_indices])
        img_test.append(img_points[test_indices])

    return obj_train, obj_test, img_train, img_test


class Camera_Cali:
    def __init__(self):
        self.init_camera_mat = np.array(
            [[1062.267560, 0.000000, 1501.057278], [0.000000, 1062.212564, 867.887492], [0.000000, 0.000000, 1.000000]])
        self.init_dist_coeff = np.array(
            [[-0.018123981144576858], [-0.0026101267970621823], [0.0006215782316954739], [-0.00030905667520437564]])

        self.init_camera_mat_normal = np.array(
            [[1345.159861, 0.000000, 973.776987], [0.000000, 1344.626518, 541.407299], [0.000000, 0.000000, 1.000000]])
        self.init_dist_coeff_normal = np.array(
            [[-0.404256259818931], [0.21922420928359876], [-0.00016181802429342013], [-7.126641144546051e-05],
             [-0.06924570764420157]])

    def calib_in(self, obj_point_list, img_point_list, frame_size, camera_type):
        if camera_type == "fisheye":
            return self.calib_in_fisheye(obj_point_list, img_point_list, frame_size)
        else:
            return self.calib_in_normal(obj_point_list, img_point_list, frame_size)

    def calib_in_fisheye(self, obj_point_list, img_point_list, frame_size):
        data = Calib_Data()
        if len(obj_point_list) <= 3:
            print(f"chessboard num is {len(obj_point_list)} <= 3")
            return data

        # 使用train_test_split划分训练集和测试集
        obj_train, obj_test, img_train, img_test = split_points(obj_point_list, img_point_list, test_size=0.1,
                                                                random_state=42)

        data.camera_mat, data.dist_coeff = self.init_camera_mat, self.init_dist_coeff
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.fisheye.calibrate(
            obj_train, img_train, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.fisheye.CALIB_FIX_SKEW | cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 1000, 1e-6))

        # 计算重投影误差
        if data.ok:
            reproj_err = []

            for i in range(len(img_point_list)):
                corners_reproj, _ = cv2.fisheye.projectPoints(obj_test[i], data.rvecs[i], data.tvecs[i],
                                                              data.camera_mat,
                                                              data.dist_coeff)
                err = cv2.norm(corners_reproj, img_test[i], cv2.NORM_L2) / len(corners_reproj)
                reproj_err.append(err)

            data.reproj_err = np.mean(reproj_err)

        # 判断数据有效性
        if data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff):
            # 确保两个矩阵具有相同的形状
            assert data.camera_mat.shape == self.init_camera_mat.shape, "矩阵形状不匹配"
            # 计算两个矩阵每个元素的差的绝对值
            abs_diff = np.abs(data.camera_mat - self.init_camera_mat)
            # 计算init矩阵对应位置的阈值
            threshold = m_global.similar_threshold * np.abs(self.init_camera_mat)
            # 检查是否小于阈值
            below_threshold_1 = abs_diff <= threshold

            # 确保两个矩阵具有相同的形状
            assert data.dist_coeff.shape == self.init_dist_coeff.shape, "矩阵形状不匹配"
            # 计算init矩阵对应位置的阈值
            threshold = np.ones_like(self.init_dist_coeff)
            # 检查是否小于阈值
            below_threshold_2 = np.abs(data.dist_coeff) <= threshold

            # 判断这些值是否都大于0
            if not np.all(below_threshold_1) or not np.all(below_threshold_2):
                data.ok = False

        print("Camera Matrix is : {}".format(data.camera_mat.tolist()))
        print("Distortion Coefficient is : {}".format(data.dist_coeff.tolist()))
        print("Reprojection Error is : {}".format(data.reproj_err))

        return data

    def calib_in_normal(self, obj_point_list, img_point_list, frame_size):
        data = Calib_Data()
        if len(obj_point_list) <= 3:
            print(f"chessboard num is {len(obj_point_list)} <= 3")
            return data

        # 使用train_test_split划分训练集和测试集
        obj_train, obj_test, img_train, img_test = split_points(obj_point_list, img_point_list, test_size=0.1,
                                                                random_state=42)
        # obj_train, obj_test, img_train, img_test = obj_point_list, obj_point_list, img_point_list, img_point_list

        data.camera_mat, data.dist_coeff = self.init_camera_mat_normal.copy(), self.init_dist_coeff_normal.copy()

        # show_img = cv2.imread("m_data/hqtest/in_MR.jpg")
        # for point_list in img_train:
        #     for point in point_list:
        #         cv2.circle(show_img, (int(point[0][0]), int(point[0][1])), 5, (255, 0, 0), -1)
        # cv2.imwrite("m_data/hqtest/in_MR_show.jpg", show_img)

        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.calibrateCamera(
            obj_train, img_train, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 1000, 1e-6))

        # 计算重投影误差
        if data.ok:
            reproj_err = []

            for i in range(len(img_point_list)):
                corners_reproj, _ = cv2.projectPoints(obj_test[i], data.rvecs[i], data.tvecs[i],
                                                      data.camera_mat,
                                                      data.dist_coeff)
                err = cv2.norm(corners_reproj, img_test[i], cv2.NORM_L2) / len(corners_reproj)
                reproj_err.append(err)

            data.reproj_err = np.mean(reproj_err)

        # 判断数据有效
        if data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff):
            # 确保两个矩阵具有相同的形状
            assert data.camera_mat.shape == self.init_camera_mat_normal.shape, "矩阵形状不匹配"
            # 计算两个矩阵每个元素的差的绝对值
            abs_diff = np.abs(data.camera_mat - self.init_camera_mat_normal)
            # 计算init矩阵对应位置的阈值
            threshold = m_global.similar_threshold * np.abs(self.init_camera_mat_normal)  # 0.15
            # 检查是否小于阈值
            below_threshold_1 = abs_diff <= threshold

            # 确保两个矩阵具有相同的形状
            assert data.dist_coeff.shape == self.init_dist_coeff_normal.shape, "矩阵形状不匹配"
            # 计算init矩阵对应位置的阈值
            threshold = np.ones_like(self.init_dist_coeff_normal)
            # 检查是否小于阈值
            below_threshold_2 = np.abs(data.dist_coeff) <= threshold

            # 判断这些值是否都大于0
            if not np.all(below_threshold_1) or not np.all(below_threshold_2):
                data.ok = False

        # if data is not None and data.ok:
        print("Camera Matrix is : {}".format(data.camera_mat.tolist()))
        print("Distortion Coefficient is : {}".format(data.dist_coeff.tolist()))
        print("Reprojection Error is : {}".format(data.reproj_err))

        return data

    def calib_ex(self, objectPoints, imgPoints, point_id_list, mtx, dist, check_mode=False,
                 camera_type="normal", rotate=0):
        end_point = np.array([(m_global.bW + 1) * m_global.bSize, (m_global.bH + 1) * m_global.bSize, 0])
        if rotate == 1:  # 顺转90
            objectPoints[:, :, 0:2] = np.flip(objectPoints[:, :, 0:2], 2)
            objectPoints[:, :, 1] = end_point[1] - objectPoints[:, :, 1]
        elif rotate == 2:  # 顺转180
            objectPoints = end_point - objectPoints
        elif rotate == 3:  # 顺转270
            objectPoints[:, :, 0:2] = np.flip(objectPoints[:, :, 0:2], 2)
            objectPoints[:, :, 0] = end_point[0] - objectPoints[:, :, 0]

        if camera_type == "fisheye":
            img_shape = (2960, 1664)
            return self.calib_ex_fisheye(imgPoints, objectPoints, point_id_list, mtx, dist, img_shape,
                                         check_mode)
        else:
            img_shape = (1920, 1080)
            return self.calib_ex_normal(imgPoints, objectPoints, point_id_list, mtx, dist, img_shape, check_mode)

    def calib_ex_fisheye(self, imgPoints, objectPoints, point_id_list, mtx, dist, img_shape, check_mode=False):
        point_dict = {}
        dist_e = np.zeros_like(dist)
        new_size = (img_shape[1], img_shape[0])
        # 畸变校正
        new_camera_matrix = np.multiply(mtx, [[0.6, 1, 1], [1, 0.6, 1], [1, 1, 1]])

        temp_imgPoints = copy.deepcopy(imgPoints)
        # temp_imgPoints = np.reshape(temp_imgPoints, (-1, 2))
        cv2.fisheye.undistortPoints(temp_imgPoints, mtx, dist, temp_imgPoints, P=mtx)

        ret, rvecs, tvecs = cv2.solvePnP(objectPoints, temp_imgPoints, mtx, dist_e)
        # print(f"rvecs:\n{rvecs}")
        # print(f"tvecs:\n{tvecs}")

        point_dict_perspec = {}
        imgPoints_perspec = copy.deepcopy(imgPoints)
        mtx_p = mtx.copy()
        mtx_p[0, 0] *= 0.6
        mtx_p[1, 1] *= 0.6
        cv2.fisheye.undistortPoints(imgPoints_perspec, mtx, dist, imgPoints_perspec, P=mtx_p)

        if check_mode:  # 检查模式
            rvecs_mat, _ = cv2.Rodrigues(rvecs)
            cv2.invert(rvecs_mat, rvecs_mat)
            tvecs_1 = np.dot(rvecs_mat, tvecs)
            # print(tvecs_1)

            temp_imgPoints = copy.deepcopy(imgPoints)
            cv2.fisheye.undistortPoints(temp_imgPoints, mtx, dist, temp_imgPoints, rvecs_mat)
            for j in range(temp_imgPoints.shape[0]):
                points = temp_imgPoints[j][0]
                point_id = point_id_list[j]
                points[0] = (points[0] - 1 * tvecs_1[0] / 1000) * (tvecs_1[2] / 1000) + 0.1
                points[1] = (points[1] - 1 * tvecs_1[1] / 1000) * (tvecs_1[2] / 1000) + 0.1
                point_dict[f"{point_id}"] = points
                point_dict_perspec[f"{point_id}"] = imgPoints_perspec[j][0]

        return ret, rvecs, tvecs, point_dict, point_dict_perspec

    def calib_ex_normal(self, imgPoints, objectPoints, point_id_list, mtx, dist, img_shape, check_mode=False):
        point_dict = {}
        dist_e = np.zeros_like(dist)
        new_size = (img_shape[1], img_shape[0])
        # 畸变校正
        new_camera_matrix = np.multiply(mtx, [[0.6, 1, 1], [1, 0.6, 1], [1, 1, 1]])

        temp_imgPoints = copy.deepcopy(imgPoints)
        # temp_imgPoints = np.reshape(temp_imgPoints, (-1, 2))
        cv2.undistortPoints(temp_imgPoints, mtx, dist, temp_imgPoints, P=mtx)

        ret, rvecs, tvecs = cv2.solvePnP(objectPoints, temp_imgPoints, mtx, dist_e)
        # print(f"rvecs:\n{rvecs}")
        # print(f"tvecs:\n{tvecs}")

        point_dict_perspec = {}
        imgPoints_perspec = copy.deepcopy(imgPoints)
        mtx_p = mtx.copy()
        mtx_p[0, 0] *= 0.8
        mtx_p[1, 1] *= 0.8
        cv2.undistortPoints(imgPoints_perspec, mtx, dist, imgPoints_perspec, P=mtx_p)

        if check_mode:  # 检查模式
            rvecs_mat, _ = cv2.Rodrigues(rvecs)
            cv2.invert(rvecs_mat, rvecs_mat)
            tvecs_1 = np.dot(rvecs_mat, tvecs)
            # print(tvecs_1)

            temp_imgPoints = copy.deepcopy(imgPoints)
            cv2.undistortPoints(temp_imgPoints, mtx, dist, temp_imgPoints, rvecs_mat)
            for j in range(temp_imgPoints.shape[0]):
                points = temp_imgPoints[j][0]
                point_id = point_id_list[j]
                points[0] = (points[0] - 1 * tvecs_1[0] / 1000) * (tvecs_1[2] / 1000) + 0.1
                points[1] = (points[1] - 1 * tvecs_1[1] / 1000) * (tvecs_1[2] / 1000) + 0.1
                point_dict[f"{point_id}"] = points
                point_dict_perspec[f"{point_id}"] = imgPoints_perspec[j][0]

        return ret, rvecs, tvecs, point_dict, point_dict_perspec
