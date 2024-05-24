# import math
# import time
#
# import cv2
# import numpy as np
#
# # 1920,
# #         1080,
# #         3792.787155321691,
# #         0.0,
# #         948.3051734110876,
# #         0.0,
# #         4336.966040554097,
# #         559.323725077574,
# #         0.0,
# #         0.0,
# #         1.0,
# #         -0.1123595515195841,
# #         40.98170357341583,
# #         0.025394897540883185,
# #         0.034654253327854,
# #         -627.4883483566468
#
# camera_mat = [[3792.787155321691, 0.0, 948.3051734110876]
#     , [0.0, 4336.966040554097, 559.323725077574]
#     , [0.0, 0.0, 1.0]]
#
#
# def repre_err():
#     imgPath = ""
#     boardSize = (11, 8)
#     inImg = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)
#     if inImg is None:
#         print("Imread error!")
#     (imgHigh, imgWith) = inImg.shape
#     ret = True
#     margin = 0.2
#     # dstRect = []
#
#     grayHigh = 1080
#     grayWith = 1920
#     factor = min(imgWith / grayWith, imgHigh / grayHigh)
#     # factorWith = imgWith / grayWith
#     # factorHigh = imgHigh / grayHigh
#     gray = cv2.resize(inImg, (int(imgWith / factor), int(imgHigh / factor)))
#     # inImg_clone = inImg.copy()
#     m_time = time.time()
#
#     reproj_err = []
#     corners_list = []
#     board_list = []
#     BOARD = np.array([[(j * 50, i * 50, 0.)]
#                       for i in range(8)
#                       for j in range(11)], dtype=np.float32)
#
#     idI = 0
#     while ret:
#         # 寻找并绘制每个棋盘格的角点
#         ret, corners = cv2.findChessboardCorners(gray, boardSize, None)
#         if ret:
#             corners_list.append(corners)
#             board_list.append(BOARD)
#             # 在图像上绘制第一个棋盘格的角点
#             x, y, w, h = cv2.boundingRect(corners)
#             gray[y:y + h, x:x + w] = 0
#
#             black_rect = [int(y * factor), int((y + h) * factor), int(x * factor), int((x + w) * factor)]
#             x = x - margin * w
#             if x < 0:
#                 x = 0
#
#             w = (1 + 2 * margin) * w
#             if x + w > imgWith:
#                 w = imgWith - x
#
#             y = y - margin * h
#             if y < 0:
#                 y = 0
#             h = (1 + 2 * margin) * h
#             if y + h > imgHigh:
#                 h = imgHigh - y
#             rect = (x, y, w, h)
#             rectSize = rect[2] * rect[3]
#             if rectSize > 1000 and rect[2] < rect[3] * 2 and rect[3] < rect[2] * 2:
#                 # dstRect.append(rect)
#                 # 保存图片
#                 outImg = np.zeros((imgHigh, imgWith), dtype=np.uint8)
#                 subRect = tuple(int(item * factor) for item in rect)
#                 x, y, w, h = subRect
#                 outImg[y:y + h, x:x + w] = \
#                     inImg[y:y + h, x:x + w]
#                 idI += 1
#             inImg[black_rect[0]:black_rect[1], black_rect[2]:black_rect[3]] = 0
#         else:
#             break
#
#     for i in range(len(corners_list)):
#         corners_reproj, _ = cv2.fisheye.projectPoints(board_list[i], rvecs[i], tvecs[i], camera_mat,
#                                                       dist_coeff)
#         err = cv2.norm(corners_reproj, corners_list[i], cv2.NORM_L2) / len(corners_reproj)
#         reproj_err.append(err)
#
#     return True
