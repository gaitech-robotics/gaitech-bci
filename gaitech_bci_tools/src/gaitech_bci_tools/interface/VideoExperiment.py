# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file './Ui/VideoExperiment.ui'
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

class Ui_VideoExperiment(object):
    def setupUi(self, VideoExperiment):
        VideoExperiment.setObjectName(_fromUtf8("VideoExperiment"))
        VideoExperiment.setWindowModality(QtCore.Qt.ApplicationModal)
        VideoExperiment.resize(800, 512)
        VideoExperiment.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.gridLayout = QtGui.QGridLayout(VideoExperiment)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.label = QtGui.QLabel(VideoExperiment)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.gVideo = QtGui.QGraphicsView(VideoExperiment)
        self.gVideo.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gVideo.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gVideo.setObjectName(_fromUtf8("gVideo"))
        self.gridLayout.addWidget(self.gVideo, 1, 0, 1, 1)
        self.progressBar = QtGui.QProgressBar(VideoExperiment)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName(_fromUtf8("progressBar"))
        self.gridLayout.addWidget(self.progressBar, 2, 0, 1, 1)

        self.retranslateUi(VideoExperiment)
        QtCore.QMetaObject.connectSlotsByName(VideoExperiment)

    def retranslateUi(self, VideoExperiment):
        VideoExperiment.setWindowTitle(_translate("VideoExperiment", "Video Experiment", None))
        self.label.setText(_translate("VideoExperiment", "At any time press SPACE bar to pause and ESC to quit", None))

