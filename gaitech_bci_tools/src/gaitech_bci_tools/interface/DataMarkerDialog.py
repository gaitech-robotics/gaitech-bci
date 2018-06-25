# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './Ui/DataMarkerDialog.ui'
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

class Ui_DataMarkerDialog(object):
    def setupUi(self, DataMarkerDialog):
        DataMarkerDialog.setObjectName(_fromUtf8("DataMarkerDialog"))
        DataMarkerDialog.resize(284, 250)
        self.gridLayout_2 = QtGui.QGridLayout(DataMarkerDialog)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(DataMarkerDialog)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.leMarker = QtGui.QLineEdit(DataMarkerDialog)
        self.leMarker.setObjectName(_fromUtf8("leMarker"))
        self.gridLayout.addWidget(self.leMarker, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(DataMarkerDialog)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.leTime = QtGui.QLineEdit(DataMarkerDialog)
        self.leTime.setEnabled(False)
        self.leTime.setObjectName(_fromUtf8("leTime"))
        self.gridLayout.addWidget(self.leTime, 1, 1, 1, 1)
        self.label_3 = QtGui.QLabel(DataMarkerDialog)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.leEvent = QtGui.QLineEdit(DataMarkerDialog)
        self.leEvent.setObjectName(_fromUtf8("leEvent"))
        self.gridLayout.addWidget(self.leEvent, 2, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.label_4 = QtGui.QLabel(DataMarkerDialog)
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.gridLayout_2.addWidget(self.label_4, 1, 0, 1, 1)
        self.pteRemarks = QtGui.QPlainTextEdit(DataMarkerDialog)
        self.pteRemarks.setObjectName(_fromUtf8("pteRemarks"))
        self.gridLayout_2.addWidget(self.pteRemarks, 2, 0, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(DataMarkerDialog)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout_2.addWidget(self.buttonBox, 3, 0, 1, 1)

        self.retranslateUi(DataMarkerDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), DataMarkerDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), DataMarkerDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(DataMarkerDialog)

    def retranslateUi(self, DataMarkerDialog):
        DataMarkerDialog.setWindowTitle(_translate("DataMarkerDialog", "Edit Marker", None))
        self.label.setText(_translate("DataMarkerDialog", "Marker", None))
        self.leMarker.setToolTip(_translate("DataMarkerDialog", "Enter unique marker identifier", None))
        self.label_2.setText(_translate("DataMarkerDialog", "Time", None))
        self.leTime.setToolTip(_translate("DataMarkerDialog", "Time of the event", None))
        self.label_3.setText(_translate("DataMarkerDialog", "Event", None))
        self.leEvent.setToolTip(_translate("DataMarkerDialog", "Enter name of event to mark", None))
        self.label_4.setText(_translate("DataMarkerDialog", "Remarks", None))
        self.pteRemarks.setToolTip(_translate("DataMarkerDialog", "Enter experiment remarks for this event", None))

