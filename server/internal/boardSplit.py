import numpy as np
import cv2
import os
from cv2 import threshold, waitKey
from numpy import dtype, uint8
import time


def getBoardPosition(imgPath, boardSize, boardCnt, outPath, count):
    inImg = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)
    if inImg is None:
        print("Imread error!")
    (imgHigh, imgWith) = inImg.shape
    ret = True
    margin = 0.2
    # dstRect = []

    grayHigh = 1080
    grayWith = 1920
    factor = min(imgWith / grayWith, imgHigh / grayHigh)
    # factorWith = imgWith / grayWith
    # factorHigh = imgHigh / grayHigh
    gray = cv2.resize(inImg, (int(imgWith / factor), int(imgHigh / factor)))
    # inImg_clone = inImg.copy()
    m_time = time.time()
    idI = 0
    while (ret):
        # 寻找并绘制每个棋盘格的角点
        ret, corners = cv2.findChessboardCorners(gray, boardSize, None)
        if ret:
            # 在图像上绘制第一个棋盘格的角点
            x, y, w, h = cv2.boundingRect(corners)
            gray[y:y + h, x:x + w] = 0
            black_rect = [int(y * factor), int((y + h) * factor), int(x * factor), int((x + w) * factor)]
            x = x - margin * w
            if x < 0:
                x = 0

            w = (1 + 2 * margin) * w
            if x + w > imgWith:
                w = imgWith - x

            y = y - margin * h
            if y < 0:
                y = 0
            h = (1 + 2 * margin) * h
            if y + h > imgHigh:
                h = imgHigh - y
            rect = (x, y, w, h)
            rectSize = rect[2] * rect[3]
            if rectSize > 1000 and rect[2] < rect[3] * 2 and rect[3] < rect[2] * 2:
                # dstRect.append(rect)
                # 保存图片
                outImg = np.zeros((imgHigh, imgWith), dtype=uint8)
                subRect = tuple(int(item * factor) for item in rect)
                x, y, w, h = subRect
                outImg[y:y + h, x:x + w] = \
                    inImg[y:y + h, x:x + w]
                cv2.imwrite(os.path.join(outPath, "chessboard_" + str(count) + "_" + str(idI) + ".jpg"), outImg)
                idI += 1
            inImg[black_rect[0]:black_rect[1], black_rect[2]:black_rect[3]] = 0
        else:
            break
    # m_time = time.time() - m_time
    # for idI in range(len(dstRect)):
    #     outImg = np.zeros((imgHigh, imgWith), dtype=uint8)
    #     subRect = tuple(int(item * factor) for item in dstRect[idI])
    #     x, y, w, h = subRect
    #     # x = int(x * factor)
    #     # w = int(w * factor)
    #     # y = int(y * factor)
    #     # h = int(h * factor)
    #     # inRectImg = inImg[subRect[1]:subRect[1]+subRect[3], subRect[0]:subRect[0]+subRect[2]]
    #     # outRectImg = outImg[subRect[1]:subRect[1]+subRect[3], subRect[0]:subRect[0]+subRect[2]]
    #     outImg[y:y + h, x:x + w] = \
    #         inImg[y:y + h, x:x + w]
    #     # cv2.imshow("asdas", cropped_image)
    #     # cv2.waitKey(100)
    #     cv2.imwrite(os.path.join(outPath, "chessboard_" + str(count) + "_" + str(idI) + ".jpg"), outImg)

# def getBoardPosition(imgPath, boardSize, boardCnt, outPath, count):
#     inImg = cv2.imread(imgPath, cv2.IMREAD_GRAYSCALE)
#     if inImg is None:
#         print("Imread error!")
#     (imgHigh, imgWith) = inImg.shape
#     resizeImg = cv2.resize(inImg, (imgWith // 2, imgHigh // 2))
#     blurImg = cv2.GaussianBlur(resizeImg, (3, 3), 0, 0)
#     ret, thdImg = threshold(blurImg, 120, 255, cv2.THRESH_BINARY)
#     contours, hierarchy = cv2.findContours(thdImg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
#
#     # # 在原始图像上绘制轮廓
#     # colorImg = cv2.cvtColor(resizeImg, cv2.COLOR_GRAY2BGR)  # 转换为彩色图像以便绘制轮廓
#     # cv2.drawContours(colorImg, contours, -1, (0, 255, 0), 2)  # 绘制所有轮廓
#     #
#     # # 显示结果
#     # cv2.imshow('Contours', colorImg)
#     # cv2.waitKey(0)
#     # cv2.destroyAllWindows()
#
#     dstRect = []
#     for idI in range(len(contours)):
#         top = resizeImg.shape[0]
#         bom = 0
#         left = resizeImg.shape[1]
#         right = 0
#         for inJ in range(len(contours[idI])):
#             point = contours[idI][inJ]
#             left = point[0, 0] if point[0, 0] < left else left
#             right = point[0, 0] if point[0, 0] > right else right
#             top = point[0, 1] if point[0, 1] < top else top
#             bom = point[0, 1] if point[0, 1] > bom else bom
#         rect = (left, top, right - left, bom - top)
#         rectSize = rect[2] * rect[3]
#         # print(rectSize)
#         # print("\n")
#         if rectSize > 5000 and rect[2] < rect[3] * 2 and rect[3] < rect[2] * 2:
#             dstRect.append(rect)
#
#     for idI in range(len(dstRect)):
#         outImg = np.zeros((imgHigh, imgWith), dtype=uint8)
#         subRect = [i * 2 for i in dstRect[idI]]
#         # inRectImg = inImg[subRect[1]:subRect[1]+subRect[3], subRect[0]:subRect[0]+subRect[2]]
#         # outRectImg = outImg[subRect[1]:subRect[1]+subRect[3], subRect[0]:subRect[0]+subRect[2]]
#         outImg[subRect[1]:subRect[1] + subRect[3], subRect[0]:subRect[0] + subRect[2]] = \
#             inImg[subRect[1]:subRect[1] + subRect[3], subRect[0]:subRect[0] + subRect[2]]
#         cropped_image = inImg[subRect[1]:subRect[1] + subRect[3], subRect[0]:subRect[0] + subRect[2]]
#         # cv2.imshow("asdas", cropped_image)
#         # cv2.waitKey(100)
#         ret, corners = cv2.findChessboardCorners(cropped_image, (11, 8), None)
#         if ret:
#             cv2.imwrite(os.path.join(outPath, "chessboard_" + str(count) + "_" + str(idI) + ".jpg"), outImg)

# getBoardPosition("E:/program/ISP/stitch/1.jpg", (11,8), 6, "E:/program/ISP/stitch")
