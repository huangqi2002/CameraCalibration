#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- coding: UTF-8 -*-
'''
@Project ：PyQt5基础.py
@File    ：measure_Line.py
@Author  ：南山叶
@Date    ：2021/4/28 10:51
@Describe: 说明 直线绘制测量并显示长度
'''

# -*- coding: utf-8 -*-
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

#绘制直线
class MyLabel(QLabel):
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0
    flag = False
    sendmsg2 = pyqtSignal(int, int,int,int)
    list = {}
    i = 0
    res = False

    # 鼠标点击事件
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.flag = True
            self.x0 = event.x()
            self.y0 = event.y()
            self.i += 1
        if event.button() == Qt.RightButton:
            self.list.clear()
            self.x0 = 0
            self.y0 = 0
            self.x1 = 0
            self.y1 = 0
            self.update()

    # 鼠标释放事件
    def mouseReleaseEvent(self, event):
        self.flag = False

    # 鼠标移动事件
    def mouseMoveEvent(self, event):
        if self.flag:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()
    # 绘制事件
    def paintEvent(self, event):
        super(MyLabel,self).paintEvent(event)
        painter = QPainter(self)
        painter.begin(self)
        painter.setPen(QPen(Qt.red, 1, Qt.SolidLine))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        # 画预设图例
        painter.drawLine(40,60,100,60)
        painter.drawText(50,50,'10厘米')

        if self.res == True:
            # 设置参数
            self.list[self.i] = [self.x0, self.y0, self.x1, self.y1]
            # 画鼠标直线
            for data in self.list.values():
                if data != [0,0,0,0]:
                    painter.drawRect(QRect(QPoint(data[0] - 3, data[1] - 3), QSize(6, 6)))
                    painter.drawLine(data[0],data[1],data[2],data[3])
                    painter.drawRect(QRect(QPoint(data[2] - 3, data[3] - 3), QSize(6, 6)))

                    # 中心坐标处显示长度
                    length = round(((data[0]-data[2])**2+(data[1]-data[3])**2)**0.5,1)
                    painter.drawText(int(data[0] + (data[2] - data[0]) / 2 - 20), int(20 + max(data[1], data[3])),
                             str(length) + 'cm')
        else:
            # 画鼠标直线
            for data in self.list.values():
                if data != [0, 0, 0, 0]:
                    painter.drawRect(QRect(QPoint(data[0]-3, data[1]-3), QSize(6, 6)))
                    painter.drawLine(data[0], data[1], data[2], data[3])
                    painter.drawRect(QRect(QPoint(data[2] - 3, data[3] - 3), QSize(6, 6)))

                    # 中心坐标处显示长度
                    length = round(((data[0] - data[2]) ** 2 + (data[1] - data[3]) ** 2) ** 0.5, 1)
                    painter.drawText(int(data[0] + (data[2] - data[0]) / 2 - 20), int(20 + max(data[1], data[3])),
                                     str(length) + 'cm')
        painter.end()


class MenuDemo(QMainWindow):
    # 初始化MenuDemo子类
    def __init__(self):
        super(MenuDemo, self).__init__()
        font = QFont()
        #font.setFamily("Arial")  # 字体
        font.setPointSize(12)  # 字体大小
        self.setFont(font)
        self.setWindowTitle("图像处理")
        # 宽×高
        self.resize(800, 600)
        # 最小窗口尺寸
        self.setMinimumSize(800,600)
        # 全局布局
        alllayout = QHBoxLayout()

        self.lab = MyLabel()
        self.lab.setStyleSheet("QLabel{background:black;}")
        self.lab.setMinimumSize(600,500)

        self.btn = QPushButton('直线')
        self.btn.setStyleSheet("QPushButton{background:white;}")
        self.btn.clicked.connect(self.remove)
        # 添加控件
        alllayout.addWidget(self.lab)
        alllayout.addWidget(self.btn)
        widget = QWidget()
        widget.setLayout(alllayout)
        self.setCentralWidget(widget)

    def remove(self):
        if self.lab.res == True:
            self.btn.setStyleSheet("QPushButton{background:white;}")
            self.lab.res = False
        else:
            self.btn.setStyleSheet("QPushButton{background:yellow;}")
            self.lab.res = True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("mark.ico"))  # 窗口图标设置
    #主窗口
    demo = MenuDemo()
    # 显示窗口
    demo.show()
    sys.exit(app.exec_())
