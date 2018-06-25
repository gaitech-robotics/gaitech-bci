# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './Ui/LicenceDialog.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_GaitechLicenceDlg(object):
    def setupUi(self, GaitechLicenceDlg):
        GaitechLicenceDlg.setObjectName(_fromUtf8("GaitechLicenceDlg"))
        GaitechLicenceDlg.resize(380, 260)
        GaitechLicenceDlg.setMinimumSize(QtCore.QSize(380, 260))
        self.gridLayout = QtGui.QGridLayout(GaitechLicenceDlg)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.lblPrompt = QtGui.QLabel(GaitechLicenceDlg)
        self.lblPrompt.setAlignment(QtCore.Qt.AlignCenter)
        self.lblPrompt.setObjectName(_fromUtf8("lblPrompt"))
        self.gridLayout.addWidget(self.lblPrompt, 0, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(GaitechLicenceDlg)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.tblLic = QtGui.QTableWidget(GaitechLicenceDlg)
        self.tblLic.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tblLic.setEditTriggers(QtGui.QAbstractItemView.DoubleClicked|QtGui.QAbstractItemView.EditKeyPressed)
        self.tblLic.setAlternatingRowColors(True)
        self.tblLic.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblLic.setShowGrid(False)
        self.tblLic.setWordWrap(False)
        self.tblLic.setColumnCount(2)
        self.tblLic.setObjectName(_fromUtf8("tblLic"))
        self.tblLic.setRowCount(0)
        self.tblLic.horizontalHeader().setVisible(False)
        self.gridLayout.addWidget(self.tblLic, 1, 0, 1, 1)

        self.retranslateUi(GaitechLicenceDlg)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), GaitechLicenceDlg.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), GaitechLicenceDlg.reject)
        QtCore.QMetaObject.connectSlotsByName(GaitechLicenceDlg)

    def retranslateUi(self, GaitechLicenceDlg):
        GaitechLicenceDlg.setWindowTitle(_translate("GaitechLicenceDlg", "Gaitech Licence", None))
        self.lblPrompt.setText(_translate("GaitechLicenceDlg", "Add/Remove Licence Key provided by Gaitech", None))
        self.buttonBox.setToolTip(_translate("GaitechLicenceDlg", "Accept/Reject Changes", None))

