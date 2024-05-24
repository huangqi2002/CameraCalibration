import json
import sys

sys.path.append('D://VZ//camera_calibration//CameraCalibrationTool')
import os
import cv2
import numpy as np
from server.aruco_vz import aruco_tool
from server.internal.IntrinsicCalibration.intrinsicCalib import InCalibrator, CalibMode

# bW = 9
# bH = 6
# aruco_dictionary_num = 5
# bSize = 50
# bSpacer = 1
# bNum = 20
CALIB_NUMBER = 3
file = None
file_dic = {}


# 重写JSONEncoder中的default方法
class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)


class CalibData:
    def __init__(self):
        self.type = None
        self.camera_mat = None
        self.dist_coeff = None
        self.rvecs = None
        self.tvecs = None
        self.map1 = None
        self.map2 = None
        self.reproj_err = None
        self.ok = False
        self.check = True


def get_images(PATH, NAME):
    filePath = [os.path.join(PATH, x) for x in os.listdir(PATH)
                if any(x.endswith(extension) for extension in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'])
                ]
    filenames = [filename for filename in filePath if NAME in filename]
    if len(filenames) == 0:
        raise Exception("from {} read images failed".format(PATH))
    return filenames


def runInCalib_x2(mode, imgPath, imgPrefix, bResize, img_size_x2):
    print("Intrinsic Calibration ......")
    filenames = get_images(imgPath, imgPrefix)
    obj_point_ndarray, img_point_ndarray, point_id_list = [], [], []
    if len(filenames) != 0:
        for i in range(len(filenames)):
            img = cv2.imread(filenames[i])
            bW, bH, aruco_dictionary_num, bSize, bSpacer, bNum = 9, 6, 5, 50, 1, 20
            ok, temp_obj_point_ndarray, temp_img_point_ndarray, temp_point_id_list = get_aruco_corners_x2(img, bW, bH,
                                                                                                          aruco_dictionary_num,
                                                                                                          bSize,
                                                                                                          bSpacer, bNum,
                                                                                                          save_path=imgPath + "imgPrefix.jpg")
            obj_point_ndarray.extend(temp_obj_point_ndarray)
            img_point_ndarray.extend(temp_img_point_ndarray)
            point_id_list.extend(temp_point_id_list)
    if len(obj_point_ndarray) >= CALIB_NUMBER:
        data = CalibData()
        data.type = "NORMAL"
        data.camera_mat = np.array(
            [[1941.3851283184952, 0.0, 1336.6251025674035], [0.0, 1941.3792913218647, 783.6545171521075],
             [0.0, 0.0, 1.0]])
        data.dist_coeff = np.array(
            [[-0.40058073012545786], [0.215397727077163], [3.6482409839156245e-05], [-3.308470420671737e-05],
             [-0.06781766795525941]])

        print(f"corners.size {len(obj_point_ndarray)}")
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.calibrateCamera(
            obj_point_ndarray, img_point_ndarray, img_size_x2, data.camera_mat, data.dist_coeff,
            flags=cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 100, 1e-6))

        if data.ok:
            data.reproj_err = []
            for i in range(len(img_point_ndarray)):
                corners_reproj, _ = cv2.projectPoints(obj_point_ndarray[i], data.rvecs[i], data.tvecs[i],
                                                      data.camera_mat,
                                                      data.dist_coeff)
                err = cv2.norm(corners_reproj, img_point_ndarray[i], cv2.NORM_L2) / len(corners_reproj)
                data.reproj_err.append(err)
            print(f"reproj_err : {np.mean(data.reproj_err)}")

        file_dic[f"{os.path.basename(imgPath)}_camera_mat"] = data.camera_mat
        file_dic[f"{os.path.basename(imgPath)}_dist_coeff"] = data.dist_coeff
        file_dic[f"{os.path.basename(imgPath)}_chessboard_id"] = point_id_list
        file_dic[f"{os.path.basename(imgPath)}_chessboard_img"] = img_point_ndarray
        file_dic[f"{os.path.basename(imgPath)}_chessboard_obj"] = obj_point_ndarray

    return ok


def get_aruco_corners_x2(img, bW=9, bH=6, aruco_dictionary_num=5, bSize=50, bSpacer=1, bNum=20, save_path=None):
    ok, obj_point_ndarray, img_point_ndarray = False, None, None
    aruco_tool.set_aruco_dictionary(aruco_dictionary_num, 1000)
    aruco_tool.set_charuco_board((bW + 1, (bH + 1) * bNum + bSpacer * (bNum - 1)))

    ret_img_bool = False
    if save_path is not None:
        ret_img_bool = True

    objPoints, imgPoints, charucoIds, ret_img = aruco_tool.charuco_detect(img, ret_img_bool)

    if objPoints is None:
        return ok, obj_point_ndarray, img_point_ndarray

    threshold = bW * (bH + 1 + bSpacer)
    # 初始化一个列表来存储十个组
    temp_id_list = [np.empty((0, 1, 1)) for _ in range(bNum)]
    temp_obj_point_list = [np.empty((0, 1, 3)) for _ in range(bNum)]
    temp_img_point_list = [np.empty((0, 1, 2)) for _ in range(bNum)]

    # 将 objPoints 和 charucoIds 进行 zip，得到每个点对应的 charucoId
    points_with_charuco_ids = zip(objPoints, imgPoints, charucoIds)

    # 分组并筛选出满足条件的非空组
    for obj_point, img_point, ids in points_with_charuco_ids:
        if ids is not None and 0 <= ids[0] < threshold * bNum:
            temp_ids = ids[0] // threshold
            temp_id_list[temp_ids] = np.vstack([temp_id_list[temp_ids], np.array(ids[0]).reshape(1, 1, 1)])
            begin_point = np.array([0, (bH + bSpacer + 1) * temp_ids * 0.25, 0])
            temp_obj_point_list[temp_ids] = np.vstack(
                [temp_obj_point_list[temp_ids], ((obj_point[0] - begin_point).reshape(1, 1, -1) / 0.25 * bSize)])
            temp_img_point_list[temp_ids] = np.vstack(
                [temp_img_point_list[temp_ids], img_point[0].reshape(1, 1, -1)])

    # 过滤掉为空的组
    obj_point_ndarray = [arr.astype(np.float32) for arr in temp_obj_point_list if arr.size > 10 * 3]
    point_id_list = [arr.astype(np.float32) for arr in temp_id_list if arr.size > 0]
    # for group in obj_point_ndarray:
    # first_element_points = group[0].copy()  # 获取第一个元素的值
    # first_element_points = np.array([[min(group[:, :, 0])[0], min(group[:, :, 1])[0], 0]])  # 获取第一个元素的值
    # for i in range(0, len(group)):
    #     points = group[i]
    #     group[i] = points - first_element_points

    img_point_ndarray = [arr.astype(np.float32) for arr in temp_img_point_list if arr.size > 10 * 2]

    if ret_img_bool:
        cv2.imwrite(save_path, ret_img)

    if len(obj_point_ndarray) > 0:
        ok = True
    return ok, obj_point_ndarray, img_point_ndarray, point_id_list


def calib_in_aruco():
    mode_normal = "normal"
    precision = 0.9
    img_size_x2 = (2688, 1512)
    aruco_flag = True
    filePath = "x2_test"

    runInCalib_x2(mode_normal, filePath + "/DL", "chessboard", False,
                  img_size_x2)
    runInCalib_x2(mode_normal, filePath + "/DR", "chessboard", False,
                  img_size_x2)
    # if mtxL is None or distortionL is None or reProjectionErrorL is None:
    #     return False, f"L NoBoeardError"
    # elif reProjectionErrorL >= precision:
    #     return False, f"L ReProjectionError: {reProjectionErrorL}"
    # print(f"L ReProjectionError: {reProjectionErrorL}")


def calib_in_aruco_test():
    cmd = f"xcopy /E/Y ..\\m_data\\x2_test\\522 .\\x2_test"
    os.system('chcp 65001')
    os.system(cmd)
    calib_in_aruco()

    with open("x2_test\\result.json", "w", encoding="utf-8") as f:
        file_json = json.dumps(file_dic, indent=4, separators=(', ', ': '), ensure_ascii=False, cls=NumpyArrayEncoder)
        f.write(file_json)
    print(f"calib OK")


def com_img():
    img_1 = cv2.imread("../m_data/hqtest/in_R.jpg")
    img_2 = cv2.imread("../m_data/hqtest/ex_R.jpg")
    img = img_2.copy()
    img[0:600, :, :] = img_1[0:600, :, :]
    # img = cv2.resize(img, (800, 600))
    # cv2.imshow("img", img)
    # cv2.waitKey(0)
    cv2.imwrite("../m_data/hqtest/R.jpg", img)


if __name__ == '__main__':
    # calib_in_aruco_test()
    com_img()
