# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './Ui/VideoExperimentBuilder.ui'
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

class Ui_VideoExperimentBuilder(object):
    def setupUi(self, VideoExperimentBuilder):
        VideoExperimentBuilder.setObjectName(_fromUtf8("VideoExperimentBuilder"))
        VideoExperimentBuilder.resize(800, 480)
        VideoExperimentBuilder.setMinimumSize(QtCore.QSize(800, 480))
        self.gridLayout = QtGui.QGridLayout(VideoExperimentBuilder)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.splitter = QtGui.QSplitter(VideoExperimentBuilder)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName(_fromUtf8("splitter"))
        self.layoutWidget = QtGui.QWidget(self.splitter)
        self.layoutWidget.setObjectName(_fromUtf8("layoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.layoutWidget)
        self.verticalLayout.setMargin(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gVideo = QtGui.QGraphicsView(self.layoutWidget)
        self.gVideo.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gVideo.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gVideo.setObjectName(_fromUtf8("gVideo"))
        self.verticalLayout.addWidget(self.gVideo)
        self.verticalLayout_2 = QtGui.QVBoxLayout()
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.tbPlayPause = QtGui.QToolButton(self.layoutWidget)
        self.tbPlayPause.setMinimumSize(QtCore.QSize(32, 32))
        self.tbPlayPause.setIconSize(QtCore.QSize(32, 32))
        self.tbPlayPause.setAutoRaise(True)
        self.tbPlayPause.setObjectName(_fromUtf8("tbPlayPause"))
        self.horizontalLayout.addWidget(self.tbPlayPause)
        self.tbStop = QtGui.QToolButton(self.layoutWidget)
        self.tbStop.setMinimumSize(QtCore.QSize(32, 32))
        self.tbStop.setIconSize(QtCore.QSize(32, 32))
        self.tbStop.setAutoRaise(True)
        self.tbStop.setObjectName(_fromUtf8("tbStop"))
        self.horizontalLayout.addWidget(self.tbStop)
        self.tbAddMarker = QtGui.QToolButton(self.layoutWidget)
        self.tbAddMarker.setMinimumSize(QtCore.QSize(32, 32))
        self.tbAddMarker.setIconSize(QtCore.QSize(32, 32))
        self.tbAddMarker.setAutoRaise(True)
        self.tbAddMarker.setObjectName(_fromUtf8("tbAddMarker"))
        self.horizontalLayout.addWidget(self.tbAddMarker)
        self.lblTime = QtGui.QLabel(self.layoutWidget)
        self.lblTime.setText(_fromUtf8(""))
        self.lblTime.setObjectName(_fromUtf8("lblTime"))
        self.horizontalLayout.addWidget(self.lblTime)
        self.sliderMovie = QtGui.QSlider(self.layoutWidget)
        self.sliderMovie.setMinimumSize(QtCore.QSize(32, 32))
        self.sliderMovie.setOrientation(QtCore.Qt.Horizontal)
        self.sliderMovie.setObjectName(_fromUtf8("sliderMovie"))
        self.horizontalLayout.addWidget(self.sliderMovie)
        self.lblETA = QtGui.QLabel(self.layoutWidget)
        self.lblETA.setText(_fromUtf8(""))
        self.lblETA.setObjectName(_fromUtf8("lblETA"))
        self.horizontalLayout.addWidget(self.lblETA)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.pbtnOpen = QtGui.QPushButton(self.layoutWidget)
        self.pbtnOpen.setMinimumSize(QtCore.QSize(0, 40))
        self.pbtnOpen.setMaximumSize(QtCore.QSize(16777215, 60))
        self.pbtnOpen.setObjectName(_fromUtf8("pbtnOpen"))
        self.horizontalLayout_2.addWidget(self.pbtnOpen)
        self.pbtnEdit = QtGui.QPushButton(self.layoutWidget)
        self.pbtnEdit.setMinimumSize(QtCore.QSize(0, 40))
        self.pbtnEdit.setObjectName(_fromUtf8("pbtnEdit"))
        self.horizontalLayout_2.addWidget(self.pbtnEdit)
        self.pbtnSave = QtGui.QPushButton(self.layoutWidget)
        self.pbtnSave.setMinimumSize(QtCore.QSize(0, 40))
        self.pbtnSave.setMaximumSize(QtCore.QSize(16777215, 60))
        self.pbtnSave.setObjectName(_fromUtf8("pbtnSave"))
        self.horizontalLayout_2.addWidget(self.pbtnSave)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.verticalLayout.addLayout(self.verticalLayout_2)
        self.tblEvents = QtGui.QTableWidget(self.splitter)
        self.tblEvents.setMinimumSize(QtCore.QSize(240, 0))
        self.tblEvents.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.tblEvents.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.tblEvents.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tblEvents.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.tblEvents.setShowGrid(False)
        self.tblEvents.setObjectName(_fromUtf8("tblEvents"))
        self.tblEvents.setColumnCount(3)
        self.tblEvents.setRowCount(0)
        item = QtGui.QTableWidgetItem()
        self.tblEvents.setHorizontalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tblEvents.setHorizontalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tblEvents.setHorizontalHeaderItem(2, item)
        self.tblEvents.verticalHeader().setVisible(False)
        self.gridLayout.addWidget(self.splitter, 0, 0, 1, 1)

        self.retranslateUi(VideoExperimentBuilder)
        QtCore.QMetaObject.connectSlotsByName(VideoExperimentBuilder)

    def retranslateUi(self, VideoExperimentBuilder):
        VideoExperimentBuilder.setWindowTitle(_translate("VideoExperimentBuilder", "Video Experiment Builder", None))
        self.tbPlayPause.setToolTip(_translate("VideoExperimentBuilder", "Play/Pause Video", None))
        self.tbPlayPause.setText(_translate("VideoExperimentBuilder", "P", None))
        self.tbStop.setToolTip(_translate("VideoExperimentBuilder", "Stop Video", None))
        self.tbStop.setText(_translate("VideoExperimentBuilder", "S", None))
        self.tbAddMarker.setToolTip(_translate("VideoExperimentBuilder", "Add Event", None))
        self.tbAddMarker.setText(_translate("VideoExperimentBuilder", "T", None))
        self.pbtnOpen.setToolTip(_translate("VideoExperimentBuilder", "Open Video for experiment", None))
        self.pbtnOpen.setText(_translate("VideoExperimentBuilder", "Open Video", None))
        self.pbtnEdit.setToolTip(_translate("VideoExperimentBuilder", "Edit already built experiment", None))
        self.pbtnEdit.setText(_translate("VideoExperimentBuilder", "Edit Experiment", None))
        self.pbtnSave.setToolTip(_translate("VideoExperimentBuilder", "Save experiment", None))
        self.pbtnSave.setText(_translate("VideoExperimentBuilder", "Save Experiment", None))
        item = self.tblEvents.horizontalHeaderItem(0)
        item.setText(_translate("VideoExperimentBuilder", "Time", None))
        item = self.tblEvents.horizontalHeaderItem(1)
        item.setText(_translate("VideoExperimentBuilder", "Event", None))

