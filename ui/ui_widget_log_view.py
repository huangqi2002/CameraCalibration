# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'widget_log_view.ui'
#
# Created by: PyQt5 UI code generator 5.15.9
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_WidgetLogView(object):
    def setupUi(self, WidgetLogView):
        WidgetLogView.setObjectName("WidgetLogView")
        WidgetLogView.resize(674, 450)
        self.verticalLayout = QtWidgets.QVBoxLayout(WidgetLogView)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.textEdit_log = QtWidgets.QTextEdit(WidgetLogView)
        self.textEdit_log.setMaximumSize(QtCore.QSize(16777215, 16777215))
        self.textEdit_log.setObjectName("textEdit_log")
        self.verticalLayout.addWidget(self.textEdit_log)

        self.retranslateUi(WidgetLogView)
        QtCore.QMetaObject.connectSlotsByName(WidgetLogView)

    def retranslateUi(self, WidgetLogView):
        _translate = QtCore.QCoreApplication.translate
        WidgetLogView.setWindowTitle(_translate("WidgetLogView", "日志"))
