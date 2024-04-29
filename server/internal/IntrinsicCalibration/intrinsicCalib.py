import argparse
import cv2
import numpy as np
import os
from server.aruco_vz import aruco_tool

# from server.external.lib3rd.load_lib import chess_board_sdk


parser = argparse.ArgumentParser(description="Camera Intrinsic Calibration")
parser.add_argument('-input', '--INPUT_TYPE', default='camera', type=str, help='Input Source: camera/video/image')
parser.add_argument('-type', '--CAMERA_TYPE', default='fisheye', type=str, help='Camera Type: fisheye/normal')
parser.add_argument('-id', '--CAMERA_ID', default=1, type=int, help='Camera ID')
parser.add_argument('-path', '--INPUT_PATH', default='./data/', type=str, help='Input Video/Image Path')
parser.add_argument('-video', '--VIDEO_FILE', default='video.mp4', type=str,
                    help='Input Video File Name (eg.: video.mp4)')
parser.add_argument('-image', '--IMAGE_FILE', default='img_raw', type=str,
                    help='Input Image File Name Prefix (eg.: img_raw)')
parser.add_argument('-mode', '--SELECT_MODE', default='auto', type=str, help='Image Select Mode: auto/manual')
parser.add_argument('-fw', '--FRAME_WIDTH', default=1280, type=int, help='Camera Frame Width')
parser.add_argument('-fh', '--FRAME_HEIGHT', default=1024, type=int, help='Camera Frame Height')
parser.add_argument('-bw', '--BOARD_WIDTH', default=7, type=int, help='Chess Board Width (corners number)')
parser.add_argument('-bh', '--BOARD_HEIGHT', default=6, type=int, help='Chess Board Height (corners number)')
parser.add_argument('-b_auto', '--BOARD_AUTO', default=False, type=bool,
                    help='Chess Board Size Self-Adaptation(corners ''number)')
parser.add_argument('-size', '--SQUARE_SIZE', default=10, type=int, help='Chess Board Square Size (mm)')
parser.add_argument('-num', '--CALIB_NUMBER', default=3, type=int, help='Least Required Calibration Frame Number')
parser.add_argument('-delay', '--FRAME_DELAY', default=12, type=int, help='Capture Image Time Interval (frame number)')
parser.add_argument('-subpix', '--SUBPIX_REGION', default=5, type=int, help='Corners Subpix Optimization Region')
parser.add_argument('-fps', '--CAMERA_FPS', default=20, type=int, help='Camera Frame per Second(FPS)')
parser.add_argument('-fs', '--FOCAL_SCALE', default=0.5, type=float, help='Camera Undistort Focal Scale')
parser.add_argument('-ss', '--SIZE_SCALE', default=1, type=float, help='Camera Undistort Size Scale')
parser.add_argument('-store', '--STORE_FLAG', default=False, type=bool, help='Store Captured Images (Ture/False)')
parser.add_argument('-store_path', '--STORE_PATH', default='./data/', type=str, help='Path to Store Captured Images')
parser.add_argument('-crop', '--CROP_FLAG', default=False, type=bool,
                    help='Crop Input Video/Image to (fw,fh) (Ture/False)')

parser.add_argument('-aruco_dictionary_size', '--ARUCO_DIC_SIZE', default=5, type=int,
                    help='aruco dictionary size')
parser.add_argument('-aruco_dictionary_num', '--ARUCO_DIC_NUM', default=1000, type=int,
                    help='aruco dictionary num')
parser.add_argument('-aruco_board_num', '--ARUCO_BOARD_NUM', default=10, type=int,
                    help='aruco board num')
parser.add_argument('-aruco_board_spacer', '--ARUCO_BOARD_SPACER', default=1, type=int,
                    help='aruco board spacer')

parser.add_argument('-resize', '--RESIZE_FLAG', default=False, type=bool,
                    help='Resize Input Video/Image to (fw,fh) (Ture/False)')
parser.add_argument('-aruco', '--ARUCO_FLAG', default=False, type=bool,
                    help='ARUCO board (Ture/False)')

args = parser.parse_args()


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


class Fisheye:
    def __init__(self):
        self.data = CalibData()
        self.inited = False
        # self.BOARD = np.array([[(j * args.SQUARE_SIZE, i * args.SQUARE_SIZE, 0.)]
        #                        for i in range(args.BOARD_HEIGHT)
        #                        for j in range(args.BOARD_WIDTH)], dtype=np.float32)
        self.board = []

    def update(self, corners, frame_size):
        # board = [self.BOARD] * len(corners)
        if not self.inited:
            self._update_init(self.board, corners, frame_size)
            self.inited = True
        else:
            self._update_refine(self.board, corners, frame_size)
        self._calc_reproj_err(corners)
        self._get_undistort_maps()

    def _update_init(self, board, corners, frame_size):
        data = self.data
        data.type = "FISHEYE"
        data.camera_mat = np.array(
            [[1062.267560, 0.000000, 1501.057278], [0.000000, 1062.212564, 867.887492], [0.000000, 0.000000, 1.000000]])
        data.dist_coeff = np.array([[-0.018123981144576858], [-0.0026101267970621823], [0.0006215782316954739], [-0.00030905667520437564]])
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.fisheye.calibrate(
            board, corners, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.fisheye.CALIB_FIX_SKEW | cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 1e-6))
        data.ok = data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff)

    def _update_refine(self, board, corners, frame_size):
        data = self.data
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.fisheye.calibrate(
            board, corners, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.fisheye.CALIB_FIX_SKEW | cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC | cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 10, 1e-6))
        data.ok = data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff)

    def _calc_reproj_err(self, corners):
        if not self.inited: return
        data = self.data
        data.reproj_err = []
        for i in range(len(corners)):
            corners_reproj, _ = cv2.fisheye.projectPoints(self.board[i], data.rvecs[i], data.tvecs[i], data.camera_mat,
                                                          data.dist_coeff)
            err = cv2.norm(corners_reproj, corners[i], cv2.NORM_L2) / len(corners_reproj)
            data.reproj_err.append(err)

    def _get_camera_mat_dst(self, camera_mat):
        camera_mat_dst = camera_mat.copy()
        camera_mat_dst[0][0] *= args.FOCAL_SCALE
        camera_mat_dst[1][1] *= args.FOCAL_SCALE
        camera_mat_dst[0][2] = args.FRAME_WIDTH / 2 * args.SIZE_SCALE
        camera_mat_dst[1][2] = args.FRAME_HEIGHT / 2 * args.SIZE_SCALE
        return camera_mat_dst

    def _get_undistort_maps(self):
        data = self.data
        camera_mat_dst = self._get_camera_mat_dst(data.camera_mat)
        data.map1, data.map2 = cv2.fisheye.initUndistortRectifyMap(
            data.camera_mat, data.dist_coeff, np.eye(3, 3), camera_mat_dst,
            (int(args.FRAME_WIDTH * args.SIZE_SCALE), int(args.FRAME_HEIGHT * args.SIZE_SCALE)), cv2.CV_16SC2)


class Normal:
    def __init__(self):
        self.data = CalibData()
        self.inited = False
        # self.BOARD = np.array([[(j * args.SQUARE_SIZE, i * args.SQUARE_SIZE, 0.)]
        #                        for i in range(args.BOARD_HEIGHT)
        #                        for j in range(args.BOARD_WIDTH)], dtype=np.float32)
        self.board = []

    def update(self, corners, frame_size):
        # board = [self.BOARD] * len(corners)
        if not self.inited:
            self._update_init(self.board, corners, frame_size)
            self.inited = True
        else:
            self._update_refine(self.board, corners, frame_size)
        self._calc_reproj_err(corners)
        self._get_undistort_maps()

    def _update_init(self, board, corners, frame_size):
        data = self.data
        data.type = "NORMAL"
        data.camera_mat = np.array(
            [[1345.159861, 0.000000, 973.776987], [0.000000, 1344.626518, 541.407299], [0.000000, 0.000000, 1.000000]])
        data.dist_coeff = np.array(
            [[-0.404256259818931], [0.21922420928359876], [-0.00016181802429342013], [-7.126641144546051e-05],
             [-0.06924570764420157]])
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.calibrateCamera(
            board, corners, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 30, 1e-6))
        data.ok = data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff)

    def _update_refine(self, board, corners, frame_size):
        data = self.data
        data.ok, data.camera_mat, data.dist_coeff, data.rvecs, data.tvecs = cv2.calibrateCamera(
            board, corners, frame_size, data.camera_mat, data.dist_coeff,
            flags=cv2.CALIB_USE_INTRINSIC_GUESS,
            criteria=(cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_COUNT, 10, 1e-6))
        data.ok = data.ok and cv2.checkRange(data.camera_mat) and cv2.checkRange(data.dist_coeff)

    def _calc_reproj_err(self, corners):
        if not self.inited: return
        data = self.data
        data.reproj_err = []
        for i in range(len(corners)):
            corners_reproj, _ = cv2.projectPoints(self.board[i], data.rvecs[i], data.tvecs[i], data.camera_mat,
                                                  data.dist_coeff)
            err = cv2.norm(corners_reproj, corners[i], cv2.NORM_L2) / len(corners_reproj)
            data.reproj_err.append(err)

    def _get_camera_mat_dst(self, camera_mat):
        camera_mat_dst = camera_mat.copy()
        camera_mat_dst[0][0] *= args.FOCAL_SCALE
        camera_mat_dst[1][1] *= args.FOCAL_SCALE
        camera_mat_dst[0][2] = args.FRAME_WIDTH / 2 * args.SIZE_SCALE
        camera_mat_dst[1][2] = args.FRAME_HEIGHT / 2 * args.SIZE_SCALE
        return camera_mat_dst

    def _get_undistort_maps(self):
        data = self.data
        camera_mat_dst = self._get_camera_mat_dst(data.camera_mat)
        data.map1, data.map2 = cv2.initUndistortRectifyMap(
            data.camera_mat, data.dist_coeff, np.eye(3, 3), camera_mat_dst,
            (int(args.FRAME_WIDTH * args.SIZE_SCALE), int(args.FRAME_HEIGHT * args.SIZE_SCALE)), cv2.CV_16SC2)


class InCalibrator:
    def __init__(self, camera):
        if camera == 'fisheye':
            self.camera = Fisheye()
        elif camera == 'normal':
            self.camera = Normal()
        else:
            raise Exception("camera should be fisheye/normal")
        self.corners = []
        # self.board = []
        self.single_board = np.array([[(j * args.SQUARE_SIZE, i * args.SQUARE_SIZE, 0.)]
                                      for i in range(args.BOARD_HEIGHT)
                                      for j in range(args.BOARD_WIDTH)], dtype=np.float32)

    @staticmethod
    def get_args():
        return args

    def get_corners(self, img):
        ok, corners = cv2.findChessboardCorners(img, (args.BOARD_WIDTH, args.BOARD_HEIGHT),
                                                flags=cv2.CALIB_CB_ADAPTIVE_THRESH | cv2.CALIB_CB_NORMALIZE_IMAGE | cv2.CALIB_CB_FAST_CHECK)
        if ok:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            corners = cv2.cornerSubPix(gray, corners, (args.SUBPIX_REGION, args.SUBPIX_REGION), (-1, -1),
                                       (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01))
        return ok, corners

    def get_aruco_corners(self, img, save_path=None):
        aruco_tool.set_aruco_dictionary(args.ARUCO_DIC_SIZE, args.ARUCO_DIC_NUM)
        aruco_tool.set_charuco_board((args.BOARD_WIDTH + 1,
                                      (args.BOARD_HEIGHT + 1) * args.ARUCO_BOARD_NUM + args.ARUCO_BOARD_SPACER * (
                                                  args.ARUCO_BOARD_NUM - 1)))

        ret_img_bool = False
        if save_path is not None:
            ret_img_bool = True

        objPoints, imgPoints, charucoIds, ret_img = aruco_tool.charuco_detect(img, ret_img_bool)

        threshold = args.BOARD_WIDTH * (args.BOARD_HEIGHT + 1 + args.ARUCO_BOARD_SPACER)
        # 初始化一个列表来存储十个组
        temp_obj_point_list = [np.empty((0, 1, 3)) for _ in range(args.ARUCO_BOARD_NUM)]
        temp_img_point_list = [np.empty((0, 1, 2)) for _ in range(args.ARUCO_BOARD_NUM)]

        # 将 objPoints 和 charucoIds 进行 zip，得到每个点对应的 charucoId
        points_with_charuco_ids = zip(objPoints, imgPoints, charucoIds)

        # 分组并筛选出满足条件的非空组
        for obj_point, img_point, ids in points_with_charuco_ids:
            if ids is not None and 0 <= ids[0] < threshold * args.ARUCO_BOARD_NUM:
                temp_ids = ids[0] // threshold
                temp_obj_point_list[temp_ids] = np.vstack([temp_obj_point_list[temp_ids],  (obj_point[0].reshape(1, 1,-1) / 0.25 * args.SQUARE_SIZE)])
                temp_img_point_list[temp_ids] = np.vstack([temp_img_point_list[temp_ids], img_point[0].reshape(1, 1,-1)])

        # 过滤掉为空的组
        obj_point_ndarray = [arr.astype(np.float32) for arr in temp_obj_point_list if arr.size > 0]
        for group in obj_point_ndarray:
            first_element_points = group[0].copy()  # 获取第一个元素的值
            for i in range(0, len(group)):  # 遍历除第一个元素外的其他元素
                points = group[i]
                group[i] = points - first_element_points

        img_point_ndarray = [arr.astype(np.float32) for arr in temp_img_point_list if arr.size > 0]

        if ret_img_bool:
            # temp_img = cv2.resize(ret_img, (800, 600))
            # cv2.imshow("ret_img", temp_img)
            # cv2.waitKey(0)
            cv2.imwrite(save_path, ret_img)

        ok = False
        if len(obj_point_ndarray) > 0:
            ok = True
        return ok, obj_point_ndarray, img_point_ndarray

    def draw_corners(self, img):
        ok, corners = self.get_corners(img)
        cv2.drawChessboardCorners(img, (args.BOARD_WIDTH, args.BOARD_HEIGHT), corners, ok)
        return img

    def undistort(self, img):
        data = self.camera.data
        return cv2.remap(img, data.map1, data.map2, cv2.INTER_LINEAR)

    def calibrate(self, img):
        if len(self.corners) >= args.CALIB_NUMBER:
            self.camera.update(self.corners, img.shape[1::-1])
        return self.camera.data

    def single_board_set(self, bw, bh):
        self.single_board = np.array([[(j * args.SQUARE_SIZE, i * args.SQUARE_SIZE, 0.)]
                                      for i in range(bh)
                                      for j in range(bw)], dtype=np.float32)

    def __call__(self, raw_frame, filepath=None):
        result = None
        # 是否使用aruco板
        if args.ARUCO_FLAG:
            ok, objPoints, imgPoints = self.get_aruco_corners(raw_frame, filepath)
            result = self.camera.data
            if ok:
                self.corners.extend(imgPoints)  # 角点像素坐标
                self.camera.board.extend(objPoints)  # 角点世界坐标
                result = self.calibrate(raw_frame)

        else:
            # chess_board_sdk.find_chessboard(raw_frame, 0.5, filepath)
            ok, corners = self.get_corners(raw_frame)
            result = self.camera.data
            if ok:
                self.corners.append(corners)  # 角点像素坐标
                self.camera.board.append(self.single_board)  # 角点世界坐标
                result = self.calibrate(raw_frame)
                if filepath is not None:
                    cv2.drawChessboardCorners(raw_frame, (args.BOARD_WIDTH, args.BOARD_HEIGHT), corners, ok)
                    cv2.imwrite(filepath, raw_frame)
        return result


def centerCrop(img, width, height):
    if img.shape[1] < width or img.shape[0] < height:
        raise Exception("CROP size should be smaller than original size")
    img = img[round((img.shape[0] - height) / 2): round((img.shape[0] - height) / 2) + height,
          round((img.shape[1] - width) / 2): round((img.shape[1] - width) / 2) + width]
    return img


def get_images(PATH, NAME):
    filePath = [os.path.join(PATH, x) for x in os.listdir(PATH)
                if any(x.endswith(extension) for extension in ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG'])
                ]
    filenames = [filename for filename in filePath if NAME in filename]
    if len(filenames) == 0:
        raise Exception("from {} read images failed".format(PATH))
    return filenames


class CalibMode():
    def __init__(self, calibrator, input_type, mode):
        self.calibrator = calibrator
        self.input_type = input_type
        self.mode = mode

    def imgPreprocess(self, img):
        if args.CROP_FLAG:
            img = centerCrop(img, args.FRAME_WIDTH, args.FRAME_HEIGHT)
        elif args.RESIZE_FLAG:
            img = cv2.resize(img, (args.FRAME_WIDTH, args.FRAME_HEIGHT))
        return img

    def setCamera(self, cap):
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter.fourcc('M', 'J', 'P', 'G'))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, args.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, args.FRAME_HEIGHT)
        cap.set(cv2.CAP_PROP_FPS, args.CAMERA_FPS)
        return cap

    def runCalib(self, raw_frame, display_raw=False, display_undist=False, filepath=None):
        calibrator = self.calibrator
        raw_frame = self.imgPreprocess(raw_frame)
        result = calibrator(raw_frame, filepath)
        if display_raw or display_undist:
            raw_frame = calibrator.draw_corners(raw_frame)
        if display_raw:
            cv2.namedWindow("raw_frame", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow("raw_frame", raw_frame)
        if len(calibrator.corners) > args.CALIB_NUMBER and display_undist:
            undist_frame = calibrator.undistort(raw_frame)
            cv2.namedWindow("undist_frame", flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow("undist_frame", undist_frame)
            # cv2.waitKey(1000)
        return result

    def imageAutoMode(self):
        filenames = get_images(args.INPUT_PATH, args.IMAGE_FILE)
        result = CalibData()
        if len(filenames) != 0:
            for filename in filenames:
                print(filename)
                raw_frame = cv2.imread(filename)
                result = self.runCalib(raw_frame, filepath=filename)
                # key = cv2.waitKey(1)
                # if key == 27: break
            cv2.destroyAllWindows()
        return result

    def imageManualMode(self):
        filenames = get_images(args.INPUT_PATH, args.IMAGE_FILE)
        for filename in filenames:
            print(filename)
            raw_frame = cv2.imread(filename)
            raw_frame = self.imgPreprocess(raw_frame)
            img = raw_frame.copy()
            img = self.calibrator.draw_corners(img)
            display = "raw_frame: press SPACE to SELECT, other key to SKIP, press ESC to QUIT"
            cv2.namedWindow(display, flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow(display, img)
            key = cv2.waitKey(0)
            if key == 32:
                result = self.runCalib(raw_frame, display_raw=False)
            if key == 27: break
        cv2.destroyAllWindows()
        return result

    def videoAutoMode(self):
        cap = cv2.VideoCapture(args.INPUT_PATH + args.VIDEO_FILE)
        if not cap.isOpened():
            raise Exception("from {} read video failed".format(args.INPUT_PATH + args.VIDEO_FILE))
        frame_id = 0
        while True:
            ok, raw_frame = cap.read()
            raw_frame = self.imgPreprocess(raw_frame)
            if frame_id % args.FRAME_DELAY == 0:
                if args.STORE_FLAG:
                    cv2.imwrite(args.STORE_PATH + 'img_raw{}.jpg'.format(len(self.calibrator.corners)), raw_frame)
                result = self.runCalib(raw_frame)
                print(len(self.calibrator.corners))
            frame_id += 1
            key = cv2.waitKey(1)
            if key == 27: break
        cap.release()
        cv2.destroyAllWindows()
        return result

    def videoManualMode(self):
        cap = cv2.VideoCapture(args.INPUT_PATH + args.VIDEO_FILE)
        if not cap.isOpened():
            raise Exception("from {} read video failed".format(args.INPUT_PATH + args.VIDEO_FILE))
        while True:
            key = cv2.waitKey(1)
            ok, raw_frame = cap.read()
            raw_frame = self.imgPreprocess(raw_frame)
            display = "raw_frame: press SPACE to capture image"
            cv2.namedWindow(display, flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow(display, raw_frame)
            if key == 32:
                if args.STORE_FLAG:
                    cv2.imwrite(args.STORE_PATH + 'img_raw{}.jpg'.format(len(self.calibrator.corners)), raw_frame)
                result = self.runCalib(raw_frame)
                print(len(self.calibrator.corners))
            if key == 27: break
        cap.release()
        cv2.destroyAllWindows()
        return result

    def cameraAutoMode(self):
        cap = cv2.VideoCapture(args.CAMERA_ID)
        if not cap.isOpened():
            raise Exception("from {} read video failed".format(args.CAMERA_ID))
        cap = self.setCamera(cap)
        frame_id = 0
        start_flag = False
        while True:
            key = cv2.waitKey(1)
            ok, raw_frame = cap.read()
            raw_frame = self.imgPreprocess(raw_frame)
            if key == 32: start_flag = True
            if key == 27: break
            if not start_flag:
                cv2.putText(raw_frame, 'press SPACE to start!', (args.FRAME_WIDTH // 4, args.FRAME_HEIGHT // 2),
                            cv2.FONT_HERSHEY_COMPLEX, 1.5, (0, 0, 255), 2)
                cv2.imshow("raw_frame", raw_frame)
                continue
            if frame_id % args.FRAME_DELAY == 0:
                if args.STORE_FLAG:
                    cv2.imwrite(args.STORE_PATH + 'img_raw{}.jpg'.format(len(self.calibrator.corners)), raw_frame)
                result = self.runCalib(raw_frame)
                print(len(self.calibrator.corners))
            frame_id += 1
        cap.release()
        cv2.destroyAllWindows()
        return result

    def cameraManualMode(self):
        cap = cv2.VideoCapture(args.CAMERA_ID)
        if not cap.isOpened():
            raise Exception("from {} read video failed".format(args.CAMERA_ID))
        cap = self.setCamera(cap)
        while True:
            key = cv2.waitKey(1)
            ok, raw_frame = cap.read()
            raw_frame = self.imgPreprocess(raw_frame)
            display = "raw_frame: press SPACE to capture image"
            cv2.namedWindow(display, flags=cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
            cv2.imshow(display, raw_frame)
            if key == 32:
                if args.STORE_FLAG:
                    cv2.imwrite(args.STORE_PATH + 'img_raw{}.jpg'.format(len(self.calibrator.corners)), raw_frame)
                result = self.runCalib(raw_frame)
                print(len(self.calibrator.corners))
            if key == 27: break
        cap.release()
        cv2.destroyAllWindows()
        return result

    def __call__(self):
        input_type = self.input_type
        mode = self.mode
        if input_type == 'image' and mode == 'auto':
            result = self.imageAutoMode()
        if input_type == 'image' and mode == 'manual':
            result = self.imageManualMode()
        if input_type == 'video' and mode == 'auto':
            result = self.videoAutoMode()
        if input_type == 'video' and mode == 'manual':
            result = self.videoManualMode()
        if input_type == 'camera' and mode == 'auto':
            result = self.cameraAutoMode()
        if input_type == 'camera' and mode == 'manual':
            result = self.cameraManualMode()
        return result


def main():
    calibrator = InCalibrator(args.CAMERA_TYPE)
    calib = CalibMode(calibrator, args.INPUT_TYPE, args.SELECT_MODE)
    result = calib()

    if len(calibrator.corners) == 0:
        raise Exception("Calibration failed. Chessboard not found, check the parameters")
    if len(calibrator.corners) < args.CALIB_NUMBER:
        raise Exception("Warning: Calibration images are not enough. At least {} valid images are needed.".format(
            args.CALIB_NUMBER))

    print("Calibration Complete")
    print("Camera Matrix is : {}".format(result.camera_mat.tolist()))
    print("Distortion Coefficient is : {}".format(result.dist_coeff.tolist()))
    print("Reprojection Error is : {}".format(np.mean(result.reproj_err)))
    np.save('camera_{}_K.npy'.format(args.CAMERA_ID), result.camera_mat.tolist())
    np.save('camera_{}_D.npy'.format(args.CAMERA_ID), result.dist_coeff.tolist())


if __name__ == '__main__':
    main()
