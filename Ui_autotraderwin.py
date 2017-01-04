# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'autotraderwin.ui'
#
# Created by: PyQt5 UI code generator 5.7
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AutoTraderWin(object):
    def setupUi(self, AutoTraderWin):
        AutoTraderWin.setObjectName("AutoTraderWin")
        AutoTraderWin.resize(800, 600)
        self.textBrowser = QtWidgets.QTextBrowser(AutoTraderWin)
        self.textBrowser.setGeometry(QtCore.QRect(20, 20, 761, 261))
        self.textBrowser.setObjectName("textBrowser")
        self.pushButton_start = QtWidgets.QPushButton(AutoTraderWin)
        self.pushButton_start.setGeometry(QtCore.QRect(20, 300, 200, 200))
        self.pushButton_start.setObjectName("pushButton_start")
        self.pushButton_stop = QtWidgets.QPushButton(AutoTraderWin)
        self.pushButton_stop.setGeometry(QtCore.QRect(250, 300, 200, 200))
        self.pushButton_stop.setObjectName("pushButton_stop")
        self.pushButton_test = QtWidgets.QPushButton(AutoTraderWin)
        self.pushButton_test.setGeometry(QtCore.QRect(480, 300, 200, 200))
        self.pushButton_test.setObjectName("pushButton_test")

        self.retranslateUi(AutoTraderWin)
        QtCore.QMetaObject.connectSlotsByName(AutoTraderWin)

    def retranslateUi(self, AutoTraderWin):
        _translate = QtCore.QCoreApplication.translate
        AutoTraderWin.setWindowTitle(_translate("AutoTraderWin", "AutoTrader"))
        self.pushButton_start.setText(_translate("AutoTraderWin", "Start"))
        self.pushButton_stop.setText(_translate("AutoTraderWin", "Stop"))
        self.pushButton_test.setText(_translate("AutoTraderWin", "test"))
