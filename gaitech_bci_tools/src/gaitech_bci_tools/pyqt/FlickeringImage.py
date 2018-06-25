#####################################################################
# Software License Agreement (BSD License)
#
#  Copyright (c) 2018, Gaitech Robotics
#  All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#
#   * Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#   * Redistributions in binary form must reproduce the above
#     copyright notice, this list of conditions and the following
#     disclaimer in the documentation and/or other materials provided
#     with the distribution.
#   * Neither the name of the Gaitech Robotics nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
#  FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
#  COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
#  INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
#  BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
#  CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#  LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
#  ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#  POSSIBILITY OF SUCH DAMAGE.
#####################################################################
"""
A Widget to Display an Image with a certain frequency
"""
import sys, os, time
from PyQt4 import QtCore, QtGui
from threading import Thread

ImageUp = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                       'resources','if_arrow137_216455.png'))
ImageDown = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                         'resources','if_arrow132_216451.png'))
ImageLeft = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'interface', 'resources',
                                         'if_chevron12_216466.png'))
ImageRight = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                          'resources','if_arrow138_216456.png'))
ImageStop = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                         'resources','if_close16_216470.png'))


######################################################
######## Class FlickeringImageWidget #################
######################################################
class FlickeringImageWidget(QtGui.QWidget):
    """
    A Widget to display a flickering image
    """
    sigFlicker = QtCore.pyqtSignal(bool)        # Signal emitted when flickering happens
    sigModFlicker = QtCore.pyqtSignal(bool)     # Signal received, to update ui based on flickering
    sigHighlight = QtCore.pyqtSignal()          # Signal received, to highlight ui
    sigHighlightReset = QtCore.pyqtSignal()     # Signal received, to reset highlight

    def __init__(self, parent=None):
        super(FlickeringImageWidget, self).__init__(parent)
        self.scene = QtGui.QGraphicsScene(self)
        self.graphicsView = QtGui.QGraphicsView(self)
        self.graphicsView.setStyleSheet("background: transparent")
        self.graphicsView.setFrameShape(QtGui.QFrame.NoFrame)
        self.graphicsView.setFrameShadow(QtGui.QFrame.Plain)
        self.graphicsView.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        self.graphicsView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.graphicsView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gridlayout = QtGui.QGridLayout()
        self.gridlayout.addWidget(self.graphicsView, 0, 0, 1, 1)
        self.setLayout(self.gridlayout)
        self.setStyleSheet("background: dark red")
        ## Initialize Data Members ##
        self.highlightwait = 2.0
        self.frequency = 10.0
        self.imagepath = None
        self.__image_drawn = None
        self.__cached_image = None
        self._flickerthread = False
        self._waitflickerthread = True
        ## Callbacks etc ##
        self.graphicsView.resizeEvent = self._gDispElecResizeEvent  # Hook resize event
        self.sigModFlicker.connect(self._imageonoff)
        self.sigHighlight.connect(self._onhighlight)
        self.sigHighlightReset.connect(self._onhighlightreset)

    def __del__(self):
        """
        On object destruction
        :return:
        """
        self.stop()

    def closeEvent(self, QCloseEvent):
        """
        Stop flickering on close
        :param QCloseEvent:
        :return:
        """
        self.stop()
        QCloseEvent.accept()

    def changeBackground(self, bg):
        """
        Change the background of image
        :param bg:
        :return:
        """
        self.graphicsView.setStyleSheet("background: %s"%bg)

    def setImage(self, impath, clr=None):
        """
        Set image to flicker
        :param impath:
        :return:
        """
        if os.path.isfile(impath):
            self.stop()
            self.imagepath = impath
            self.__cached_image = QtGui.QPixmap(self.imagepath)
            if clr is not None:
                _pxr = QtGui.QPixmap(self.__cached_image.size())
                _pxr.fill(clr)
                _pxr.setMask(self.__cached_image.createMaskFromColor(QtCore.Qt.transparent))
                self.__cached_image = _pxr
            self._imageonoff(True)
        else:
            self.imagepath = None
            self.__cached_image = None

    def start(self):
        """
        Start Flickering
        :return:
        """
        self.stop()
        self._waitflickerthread = False
        self._flickerthread = True
        Thread(target=self._flicker).start()

    def stop(self):
        """
        Stop Flickering
        :return:
        """
        self._flickerthread = False
        while not self._waitflickerthread:
            time.sleep(0.001)
        # Thread has now stopped #
        self.sigModFlicker.emit(True)

    def setFrequency(self, newfreq):
        """
        Set flickering frequency
        :return:
        """
        self.stop()
        self.frequency = newfreq
        self.start()

    @QtCore.pyqtSlot(bool)
    def _imageonoff(self, sts):
        """
        Show hide image
        :param sts:
        :return:
        """
        if sts:
            if self.__cached_image is not None:
                self.__image_drawn = self.__cached_image
                self._draw_image()
                self.sigFlicker.emit(True)
        else:
            self.__image_drawn = None
            self._draw_image()
            self.sigFlicker.emit(False)

    @QtCore.pyqtSlot()
    def _onhighlight(self):
        """
        On highlight
        :return:
        """
        self.setStyleSheet("background: green")
        Thread(target=self._resethighlight).start()

    @QtCore.pyqtSlot()
    def _onhighlightreset(self):
        """
        Reset highlight
        :return:
        """
        self.setStyleSheet("background: dark red")

    def _draw_image(self):
        """
        Draw Image
        :return:
        """
        self.scene.clear()
        if self.__image_drawn is not None:
            self.scene.addPixmap(self.__image_drawn.scaled(self.graphicsView.size()))
        self.scene.update()
        self.graphicsView.setScene(self.scene)

    def _gDispElecResizeEvent(self, event):
        """
        Update Image on Widget Resize
        :param event:
        :return:
        """
        self._draw_image()
        QtGui.QGraphicsView.resizeEvent(self.graphicsView, event)

    ## Flicker Thread Function ##
    def _flicker(self):
        """
        Flicker based on frequency
        :return:
        """
        _tglprev = True
        _sleeptime = (1.0 / self.frequency) * 0.8
        _sleeptimeoff = (1.0 / self.frequency) * 0.2
        while self._flickerthread:
            self.sigModFlicker.emit(_tglprev)
            _tglprev = not _tglprev     # Toggle Previous
            if _tglprev:
                time.sleep(_sleeptimeoff)      # Sleep for on
            else:
                time.sleep(_sleeptime)      # Sleep for off
        self._waitflickerthread = True

    def _resethighlight(self):
        """
        Reset Highlight
        :return:
        """
        time.sleep(self.highlightwait)
        self.sigHighlightReset.emit()


