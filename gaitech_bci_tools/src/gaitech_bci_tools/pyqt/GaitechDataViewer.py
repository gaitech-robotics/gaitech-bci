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
Gaitech BCI Data Viewer Widget
"""
import sys, os, math, time
import numpy as np
from bisect import bisect_left
from PyQt4 import QtCore, QtGui
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'interface'))
from H10CDataViewer import Ui_H10CDataViewer
from GaitechDialogs import GaiTechDataMakerDialog

import pyqtgraph as pg
pg.setConfigOption('foreground', 'k')   # Global Settingss


########## Class GaitechDataViewerWidget ##########
# For channels 0 : Common Ref, 1 : Average Ref, 2 : Longitudinal-Bipolar, 3 : Transverse-Bipolar
class GaitechDataViewerWidget(QtGui.QWidget):
    """
    Gaitech Data Viewer Widget for H10C Data
    """
    # Signals Emitted
    sigLoadNew = QtCore.pyqtSignal(QtGui.QWidget, unicode)  # Emitted when Load Data is clicked
    sigSaveData = QtCore.pyqtSignal(QtGui.QWidget, dict, unicode)  # Emitted to Save data in some format
    # Signals Catched
    sigDeviceStatus = QtCore.pyqtSignal(str)              # Name of device connected to
    sigConnectionStatus = QtCore.pyqtSignal(int)          # Status of device being connected to
    sigConnectiviyStatus = QtCore.pyqtSignal(float, float)   # Loss information of connection
    sigLoadData = QtCore.pyqtSignal(dict, unicode)               # New data to display in UI
    sigSaveDone = QtCore.pyqtSignal(unicode)  # Emitted when saving complete
    sigMarker = QtCore.pyqtSignal(list)                 # Receive New Events
    sigData = QtCore.pyqtSignal(dict)                   # Receive New Data
    sigMode = QtCore.pyqtSignal(int)                    # On Mode Changed
    sigStream = QtCore.pyqtSignal(bool)                 # On forcefully setting streaming

    def __init__(self, parent=None, live=False):
        """
        Initialize Gaitech DataViewer Widget
        :param parent:
        """
        super(GaitechDataViewerWidget, self).__init__(parent)
        self.ui = Ui_H10CDataViewer()
        self.ui.setupUi(self)
        self.ui.plotter.setBackground(None)
        self.ui.plotter.setViewportUpdateMode(QtGui.QGraphicsView.FullViewportUpdate)
        ############ Data Members ###################
        self.plots = []             # Plot Items
        self.plotdata = []          # Plot data items
        self.live = live            # Type of widget
        self.data = dict()          # Main data storage object
        self._dataYdisplay = False  # Internally used to decide whether to display data values on mouse hovering
        self.__markerlines = []     # To store marker lines for display purpose
        self._flagaddmarker = False # Internally used to decide whether to add new marker
        self._flageditmarker = False# Internally used to decide whether to edit marker
        self._flagstreamon = False  # Internally used to check if streaming is on
        self._idxolddata = [0, 0]   # Internally used to optimize display
        self.__livelastdisp = time.time()   # Internally used for live display end update @60Hz max
        self.__datacacheinmem = 2000  # Cache Data that is not in view
        self.__dataupdatechkval = 1000 # To update cache when view change
        self.__livescrolling = False # Internally Used flag for live scrolling
        self.__lastsavedir = ''     # To keep save file dialog directory
        ####### Initialize Other Stuff #############
        self._initializeforlive() # Initialize according to live attribute
        if self.live:
            self.__datacacheinmem = 800
            self.__dataupdatechkval = 500
        self._connectothersignals() # Connect Signals
        self._loadicons()   # Load Display Resources
        self._setchnls(0)   # Default Mode initialization
        self._loadmarkerstable() # Default initialization

    def _initializeforlive(self):
        """
        Initialize UI Depending upon whether live or not
        :return:
        """
        if self.live:
            # TODO other stuff
            self.ui.btnLoad.setVisible(False)
            # Connect signals for device status etc.
            self.sigDeviceStatus.connect(self._devname_status)
            self.sigConnectionStatus.connect(self._devconn_status)
            self.sigConnectiviyStatus.connect(self._devsig_status)
            self.ui.btnRecord.clicked.connect(self._streamingonoff)
            self.sigMarker.connect(self._onNewMarker)
            self.sigData.connect(self._onNewData)
            self.sigMode.connect(self._onNewMode)
            self.sigStream.connect(self._onStreamChange)
        else:
            # TODO other stuff
            self.ui.gbDataRec.setTitle('Data Load/Save')
            self.ui.btnLoad.clicked.connect(self._loaddatadialog)
            self.ui.btnRecord.setVisible(False)
            self.ui.lbldconstant.setVisible(False)
            self.ui.lblDName.setVisible(False)
            self.ui.lblDSig.setVisible(False)
            self.sigLoadData.connect(self.loadOfflineData)
        self.sigSaveDone.connect(self._savingcomplete)

    @QtCore.pyqtSlot(str)
    def _devname_status(self, dname):
        """
        Handle signal to update Device Name to UI
        :return: None
        """
        self.ui.lblDName.setText(dname)

    @QtCore.pyqtSlot(float, float)
    def _devsig_status(self, _l1, _l2):
        """
        Handle signal to update Device Signal Loss Status
        :param _l1:
        :param _l2:
        :return:
        """
        _loss = 100.0 - (100.0*_l1)
        self.ui.lblDSig.setPixmap(self.__icon_sigstrength[1])
        self.ui.lblDSig.setToolTip("%.2f%%" % _loss)
        if _loss < 1:
            if self.__icon_sigstrength[0] is not None:
                self.ui.lblDSig.setPixmap(self.__icon_sigstrength[0])
        elif _loss < 33:
            if self.__icon_sigstrength[1] is not None:
                self.ui.lblDSig.setPixmap(self.__icon_sigstrength[1])
        elif _loss < 66:
            if self.__icon_sigstrength[2] is not None:
                self.ui.lblDSig.setPixmap(self.__icon_sigstrength[2])
        else:
            if self.__icon_sigstrength[3] is not None:
                self.ui.lblDSig.setPixmap(self.__icon_sigstrength[3])

    @QtCore.pyqtSlot(int)
    def _devconn_status(self, sts):
        """
        Handle signale to update device connectivity status
        :param sts: 0 : connecting, 1 : connected, 2 : disconnecting, 3 : disconnected
        :return:
        """
        if sts == 0:
            self.ui.lblDName.setStyleSheet("color:'orange';")
        elif sts == 1:
            self.ui.lblDName.setStyleSheet("color:'green';")
        elif sts == 2:
            self.ui.lblDName.setStyleSheet("color:'orange';")
        elif sts == 3:
            self.ui.lblDName.setStyleSheet("color:'red';")
            ### If live and streaming on stop streaming ###
            if self.live and self._flagstreamon:
                self._streamingonoff()
        else:
            self.ui.lblDName.setStyleSheet('')

    ####################################################

    def _setchnls(self, mode):
        """
        Setup UI depending upon mode
        :param mode: 0 : Common Ref, 1 : Average Ref, 2 : Longitudinal-Bipolar, 3 : Transverse-Bipolar
        :return:
        """
        ##### Clear Stuff #########
        for i in reversed(range(self.ui.gbChannels.layout().count())):
            widgetToRemove = self.ui.gbChannels.layout().itemAt(i).widget()
            # remove it from the layout list
            self.ui.gbChannels.layout().removeWidget(widgetToRemove)
            if isinstance(widgetToRemove, QtGui.QCheckBox):
                widgetToRemove.stateChanged.disconnect()
            # remove it from the gui
            widgetToRemove.setParent(None)
        # Clear Data of markers etc in memory #
        self._manualclear()
        # Clear Every thing that is plotted #
        self._clear_plotter()
        ##### Set levels ####
        if mode == 0:
            _maxYRange = 0.4
            _maxY = 0.195
        else:
            _maxYRange = 0.8
            _maxY = 0.39
        if self.live:
            _maxX = 5
            _minX = 1.0
        else:
            _maxX = 30
            _minX = 0.1
        ### Marker Plot ###
        self.plotdata.append(pg.ScatterPlotItem(size=24, symbol='s'))
        self.plots.append(pg.PlotItem(enableMenu=False))
        self.plots[-1].channelvisible = True
        self.plots[-1].setLabel('top', text='Time', units='sec')
        self.plots[-1].showAxis('top')
        self.plots[-1].buttonsHidden = True  # We dont want to use it
        self.plots[-1].setLimits(xMin=0.0, yMin=-1, yMax=1,
                                         minXRange=_minX, maxXRange=_maxX)
        self.plots[-1].setLabel('left', text='Mark')
        self.plots[-1].setMouseEnabled(y=False)
        self.plots[-1].showGrid(x=True, alpha=0.5)
        self.plots[-1].addItem(self.plotdata[0])
        self.plots[-1].display_text = pg.TextItem(text='', color='k')
        self.plots[-1].display_text.setZValue(5)
        self.plots[-1].display_text.hide()
        self.plots[-1].addItem(self.plots[-1].display_text)
        ### Other Plots ###
        _cbxs = self.__init_checkboxes(mode)
        #### Add to Layout #############
        if len(_cbxs) > 0:
            for _i in range(len(_cbxs)):
                _cbxs[_i].setChecked(True)
                _cbxs[_i].setToolTip('Enable/Disable display of %s' % str(_cbxs[_i].text()))
                ### Add Signal handler ####
                _cbxs[_i].stateChanged.connect(self._dispchnlchkchanged)
                self.ui.gbChannels.layout().addWidget(_cbxs[_i], _i/2, _i%2)
                # Add Plots
                if len(self.plots) > 0:
                    _prevplot = self.plots[-1]
                else:
                    _prevplot = None
                self.plots.append(pg.PlotItem(enableMenu=False))
                # Link X axis
                if _prevplot is not None:
                    self.plots[-1].setXLink(_prevplot)
                self.plots[-1].channelname = str(_cbxs[_i].text()) # For future enable disabling
                self.plots[-1].channelvisible = True
                self.plots[-1].setMenuEnabled(False)
                self.plots[-1].addLine(y=0)
                self.plots[-1].addLegend(offset=(1, 0))
                self.plots[-1].setLabel('left', units='V')
                #self.plots[-1].showGrid(y=True, alpha=0.5)
                self.plots[-1].setLabel('bottom', text='Time', units='sec')
                self.plots[-1].autoBtn.clicked.disconnect() # We want to hack it
                self.plots[-1].autoBtn.clicked.connect(self._autobtn_y_showAll)

                self.plots[-1].setLimits(xMin=0.0, yMin=-_maxY, yMax=_maxY,
                                         minXRange=_minX, maxXRange=_maxX,
                                         minYRange=0.006, maxYRange=_maxYRange)
                self.plotdata.append(self.plots[-1].plot(name=str(_cbxs[_i].text()), pen='b'))
                self.plotdata[-1].channelname = str(_cbxs[_i].text())
                self.plotdata[-1].setDownsampling(None, True, 'peak')
                self.plots[-1].sigXRangeChanged.connect(self._plot_x_range_changed)
                ## Add helper display Values on data points when in zoomed mode ##
                self.plots[-1].display_text = pg.TextItem(text='', color='k')
                self.plots[-1].display_text.setZValue(5)
                self.plots[-1].display_text.hide()
                self.plots[-1].addItem(self.plots[-1].display_text, ignorebounds=True)

            self._showXaxisOnlyOnLast()

    def _autobtn_y_showAll(self):
        """
        Hack Plot Item Auto Button to Rescale Only Y Axis
        :return:
        """
        if hasattr(self.sender().parentItem(), 'channelname') and hasattr(self.sender(), 'mode'):
            _parentitem = self.sender().parentItem()
            if self.sender().mode == 'auto':
                _parentitem.enableAutoRange(y=True)
                self.sender().hide()
            else:
                _parentitem.disableAutoRange()

    @QtCore.pyqtSlot(pg.InfiniteLine)
    def _markerlinemoved(self, obj):
        """
        Callback to Marker lines moved
        :param obj: Infinite line object
        :return:
        """
        if not hasattr(obj, 'markerNum') or obj.markerNum == -1:
            return
        _mid = obj.markerNum
        _txval, _idx = self._find_nearest_time_in_data(obj.getXPos())
        if _idx != -1 and 'markers' in self.data:
            _newvals = (self.data['markers'][_mid][0], _txval,
                        self.data['markers'][_mid][2], self.data['markers'][_mid][3])
            self.data['markers'][_mid] = _newvals
            self._plotmarkersandverlines()
            self.ui.twMarkers.item(_mid, 1).setText("%.3f" % _txval)

    @QtCore.pyqtSlot(pg.GraphicsScene)
    def _onMouseClickedPlot(self, obj):
        """
        Callback to add new marker points
        :param obj:
        :return:
        """
        if self._flagaddmarker and obj.currentItem != self.plotdata[0] and \
                        obj.currentItem == self.plots[0].getAxis('top') and obj.button() == QtCore.Qt.LeftButton:
            _actpos = self.plotdata[0].mapFromScene(obj.scenePos())
            _txval, _idx = self._find_nearest_time_in_data(_actpos.x())
            if _idx != -1 and 'markers' in self.data:
                _origpos = 0 # Insert after this position
                for _i in range(len(self.data['markers'])):
                    if self.data['markers'][_i][1] < _txval:
                        _origpos = _i+1
                _mname = self._generate_random_marker_name()
                _mnew = (_mname, _txval, 'Event', '')
                self.data['markers'].insert(_origpos, _mnew)
                self._loadmarkerstable()
            obj.accept()
        else:
            obj.ignore()

    @QtCore.pyqtSlot(QtCore.QPointF)
    def _onMouseMoveDisplayText(self, pos):
        """
        On Mouse hover display marker text or if enabled data values
        :param pos:
        :return:
        """
        ### For Displaying Markers Info ###
        _actpos = self.plotdata[0].mapFromScene(pos)
        _p1 = self.plotdata[0].pointsAt(_actpos)
        if len(_p1) != 0:
            self.plots[0].setYRange(-1.0, 1.0)
            _xval = _p1[0].pos()[0]
            _mname = None
            # Search for value in markers #
            if 'markers' in self.data:
                for _elem in self.data['markers']:
                    if _elem[1] == _xval:
                        _mname = _elem[0]
                        break
            if _mname is not None:
                self.plots[0].display_text.setText(_mname)
                __yr = _actpos.y()
                self.plots[0].display_text.setPos(_xval, __yr)
                self.plots[0].display_text.show()
            else:
                self.plots[0].display_text.hide()
        else:
            self.plots[0].display_text.hide()
        ### For Displaying Data Info ###
        if not self._dataYdisplay:
            for _i in range(1, len(self.plots)):
                if self.plots[_i].display_text.isVisible():
                    self.plots[_i].display_text.hide()
        else:
            _txval, _idx = self._find_nearest_time_in_data(_actpos.x())
            _showvalsmin = []
            _idxmin = 0
            try:
                for _i in range(1, len(self.plotdata)):
                    if self.plots[_i].channelvisible:
                        _showvalsmin.append(self.data['data'][self.plotdata[_i].channelname][_idx] -
                                            (self.plotdata[_i].mapFromScene(pos)).y())
                    else:
                        _showvalsmin.append(1000)
                _showvalsmin = [a*a for a in _showvalsmin]
                _, _idxmin = min((val, idx) for (idx, val) in enumerate(_showvalsmin))
                _idxmin += 1    # Adjust for markers plot
                _yvaltodisp = self.data['data'][self.plotdata[_idxmin].channelname][_idx]
                #_txval = self.plotdata[_idxmin].getData()[0][_idx]
                _yactual = self.plotdata[_idxmin].mapFromScene(pos).y()
                _yrange = self.plots[_idxmin].viewRange()[1]
                if (_yactual >= _yrange[0]) and _yactual <= _yrange[1]:
                    self.plots[_idxmin].display_text.setText("%.3f mV"% (_yvaltodisp*1000.0) )
                    self.plots[_idxmin].display_text.setPos(_txval, _yvaltodisp)
                    self.plots[_idxmin].display_text.show()
                else:
                    self.plots[_idxmin].display_text.hide()
            except:
                pass    # In case something funny happens
            ## Hide for all others ##
            for _i in range(1, len(self.plots)):
                if _i != _idxmin:
                    if self.plots[_i].display_text.isVisible():
                        self.plots[_i].display_text.hide()

    @QtCore.pyqtSlot(pg.ViewBox, tuple)
    def _plot_x_range_changed(self, obj, _range_change_data):
        """
        Slot to handle X-Range Change, to display symbols only when feasible
        :param obj: Viewbox object
        :param _range_change_data:
        :return:
        """
        if self.__livescrolling:
            # Don't Allow for values popup since data is being scrolled very fast
            _chnlname = obj.parentItem().channelname
            self._dataYdisplay = False
            for _pltdataitm in self.plotdata:
                if GaitechDataViewerWidget.__set_symbol_plotdata_None(_pltdataitm, _chnlname):
                    break
        elif hasattr(obj.parentItem(), 'channelname'):
            _chnlname = obj.parentItem().channelname
            _diff = _range_change_data[1] - _range_change_data[0]
            _widthpix = obj.screenGeometry().width()
            if (_diff != 0.0) and ((float(_widthpix) / (_diff*1000.0)) >= 8.0):
                self._dataYdisplay = True
                for _pltdataitm in self.plotdata:
                    if GaitechDataViewerWidget.__set_symbol_plotdata(_pltdataitm, _chnlname):
                        break
            else:
                self._dataYdisplay = False
                for _pltdataitm in self.plotdata:
                    if GaitechDataViewerWidget.__set_symbol_plotdata_None(_pltdataitm, _chnlname):
                        break

    @QtCore.pyqtSlot(pg.ViewBox, tuple)
    def _load_only_data_in_range(self, obj, _rng):
        _, _idx1 = self._find_nearest_time_in_data(_rng[0])
        _, _idx2 = self._find_nearest_time_in_data(_rng[1])
        if _idx1 == -1 or _idx2 == -1:
            self._idxolddata = [0, 0]
            return
        _idx1orig = _idx1
        _idx2orig = _idx2
        if _idx1-self.__datacacheinmem < 0:
            _idx1 = 0
        else:
            _idx1 = _idx1-self.__datacacheinmem
        if _idx2 + self.__datacacheinmem >= len(self.data['time']):
            _idx2 = len(self.data['time'])-1
        else:
            _idx2 = _idx2 + self.__datacacheinmem
        ######## Differnet Tests ########
        _force = False
        if not self.live:
            if self._idxolddata[0] == 0 and self._idxolddata[1] == 0:
                _force = True
            if _idx2orig == _idx2 and self._idxolddata[1] != _idx2:
                _force = True
        if np.abs(self._idxolddata[1]-_idx2) > self.__dataupdatechkval or\
                        np.abs(self._idxolddata[0]-_idx1) > self.__dataupdatechkval or _force:
            self._idxolddata = [_idx1, _idx2]
            ### Load Only Portion of Data in plots ###
            for _pltdata in self.plotdata:
                if hasattr(_pltdata, 'channelname'):
                    _chnlname = _pltdata.channelname
                    if _chnlname in self.data['data']:
                        _pltdata.clear()
                        _pltdata.setData(x=self.data['time'][_idx1:_idx2+1],
                                         y=self.data['data'][_chnlname][_idx1:_idx2+1])
            ### Load Only Portion of Markers in plots ###
            self._plotmarkersandverlines()

    def _update_data_loaded_recently(self):
        _orig = self._idxolddata[1]
        self._idxolddata[1] = len(self.data['time'])-1
        _origdiff = self._idxolddata[1] - _orig
        if self._idxolddata[1] - self._idxolddata[0] > 100:
            self._idxolddata[0] = self._idxolddata[0]+_origdiff
        ### Load Only Portion of Data in plots ###
        for _pltdata in self.plotdata:
            if hasattr(_pltdata, 'channelname'):
                _chnlname = _pltdata.channelname
                if _chnlname in self.data['data']:
                    if (self._idxolddata[1] - self._idxolddata[0]) > 5: # Only display data when it has a min size
                        _pltdata.setData(x=self.data['time'][self._idxolddata[0]: self._idxolddata[1]+1],
                                     y=self.data['data'][_chnlname][self._idxolddata[0]:self._idxolddata[1]+1])
        ### Load Only Portion of Markers in plots ###
        ## self._plotmarkersandverlines()  Don't because it is heavy here

    def _showXaxisOnlyOnLast(self):
        """
        Show X-Axis only for last Plot and Add plots to plotter
        :return:
        """
        _totalvisible = 0
        for _plt in self.plots:
            _plt.hideAxis('bottom')
            # disconnect range change if already connected #
            try:
                _plt.sigXRangeChanged.disconnect(self._load_only_data_in_range)
            except TypeError as e:
                pass
            ###################################
            if hasattr(_plt, 'channelvisible') and _plt.channelvisible:
                _totalvisible += 1
        for _i in reversed(range(len(self.plots))):
            if hasattr(self.plots[_i], 'channelvisible') and self.plots[_i].channelvisible:
                if hasattr(self.plots[_i], 'channelname'):
                    self.plots[_i].showAxis('bottom')
                # Connect Range Change to It only #
                self.plots[_i].sigXRangeChanged.connect(self._load_only_data_in_range)
                break
        self.ui.plotter.clear()
        self.ui.plotter.update()
        if _totalvisible > 1:
            self.plots[0].setMaximumHeight(80)
        else:
            self.plots[0].setMaximumHeight(-1)

        self.ui.plotter.currentRow = 0
        self.ui.plotter.currentColumn = 0
        for _plt in self.plots:
            if hasattr(_plt, 'channelvisible') and _plt.channelvisible:
                self.ui.plotter.addItem(_plt, self.ui.plotter.nextRow(), 0)
                # Clear Marker Lines that are not needed #
                _allitms = _plt.getViewBox().allChildItems()
                for _itm in _allitms:
                    if isinstance(_itm, pg.InfiniteLine) and hasattr(_itm, 'markerNum') and _itm.markerNum == -1:
                        _plt.getViewBox().removeItem(_itm)
                # End of patch for ghost lines #

        self.ui.plotter.update()
        ### Update Mouse Hover ##
        for _i in range(len(self.plotdata)):
            if hasattr(self.plots[_i], 'channelvisible') and self.plots[_i].channelvisible:
                # disconnect if already connected #
                try:
                    self.plotdata[_i].scene().sigMouseMoved.disconnect(self._onMouseMoveDisplayText)
                except TypeError as e:
                    pass
                self.plotdata[_i].scene().sigMouseMoved.connect(self._onMouseMoveDisplayText)
        # Mouse Click for First #
        # disconnect if already connected #
        try:
            self.plotdata[0].scene().sigMouseClicked.disconnect(self._onMouseClickedPlot)
        except TypeError as e:
            pass
        self.plotdata[0].scene().sigMouseClicked.connect(self._onMouseClickedPlot)

    def _dispchnlchkchanged(self, nstate):
        """
        Show hide plots depending upon selected channels
        :param nstate: ignored
        :return:
        """
        _txt = str(self.sender().text())
        _state = self.sender().isChecked()
        for _plt in self.plots:
            if hasattr(_plt, 'channelname') and _plt.channelname == _txt:
                if hasattr(_plt,'channelvisible'):
                    _plt.channelvisible = _state
        self._showXaxisOnlyOnLast()

    ################ UI Buttons Callbacks ####################

    def _streamingonoff(self):
        """
        Handle start and stop of streaming data
        :return: None
        """
        if str(self.ui.btnRecord.text()) == 'Start Recording':
            if self.__icon_streaming_started is not None:
                self.ui.btnRecord.setIcon(self.__icon_streaming_started)
            self.ui.btnRecord.setText('Stop Recording')
            self.ui.btnRecord.setToolTip('Stop streaming data from device')
            self.ui.btnSave.setEnabled(False)
            self._flagstreamon = True
        else:
            if self.__icon_streaming_ready is not None:
                self.ui.btnRecord.setIcon(self.__icon_streaming_ready)
            self.ui.btnRecord.setText('Start Recording')
            self.ui.btnRecord.setToolTip('Start streaming data from device')
            self.ui.btnSave.setEnabled(True)
            self._flagstreamon = False

    def _loaddatadialog(self):
        """
        Emit Signal that will call dialog box to open
        :return: None
        """
        dlg = QtGui.QFileDialog()
        dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
        dlg.setFilter("ROS Bag (*.bag)")
        if dlg.exec_():
            _fname = unicode(dlg.selectedFiles()[0])
            _bname = os.path.basename(unicode(_fname))
            _dir = os.path.dirname(unicode(_fname))
            self.__lastsavedir = _dir
            self._manualclear()
            self.setWindowTitle('Loading %s ...' % _bname)
            self.ui.gbDataRec.setEnabled(False)
            self.sigLoadNew.emit(self, _fname)

    def _manualclear(self):
        """
        Callback to clear button, clears display and data in memory
        :return: None
        """
        # Stop Streaming #
        if self._flagstreamon:
            self._streamingonoff()
        if self.live:
            self.setWindowTitle('Live Data Viewer')
        else:
            self.setWindowTitle('Offline Data')
        self.data = dict()
        for _plt in self.plotdata:
            _plt.clear()
        for (_p, _l) in self.__markerlines:
            _p.removeItem(_l)
        self.__markerlines = []
        self.ui.twMarkers.clearContents()
        self.ui.twMarkers.setRowCount(0)
        for _plt in self.plots:
            _plt.setLimits(xMin=0.0)
        ### Clear Data in Memory ###
        self.data = dict()
        self._dataYdisplay = False
        self._flagaddmarker = False
        self._flageditmarker = False
        self.ui.tbtnEdit.setChecked(False)
        self.ui.tbtnAddMarker.setChecked(False)
        self.ui.tbtnEdit.setEnabled(True)
        self.ui.tbtnAddMarker.setEnabled(True)
        if len(self.plots) > 0:
            self.plots[0].getViewBox().setCursor(QtCore.Qt.ArrowCursor)
        self._idxolddata = [0, 0]
        # TODO if anything else to clear

    def _clear_plotter(self):
        """
        Clear Plot elements
        :return:
        """
        for _plt in self.plots:
            _plt.clear()
        for _pltdata in self.plotdata:
            _pltdata.clear()
        self.ui.plotter.clear()
        self.ui.plotter.update()
        self.plots = []
        self.plotdata = []

    def _savedatadialog(self):
        """
        Open Dialog to save data
        :return: None
        """
        if self.data is not None and 'data' in self.data and 'time' in self.data and len(self.data['time']) > 0:
            _fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save Data', self.__lastsavedir ,selectedFilter='*.bag')
            if _fileName:
                _bname = os.path.basename(unicode(_fileName))
                _dir = os.path.dirname(unicode(_fileName))
                _fnamesext = _bname.split('.')
                self.__lastsavedir = _dir
                if (len(_fnamesext) > 1 and _fnamesext[-1] != 'bag') or (len(_fnamesext) == 1):
                    _bname = '%s.bag' % _bname
                    _fname = os.path.join(_dir, _bname)
                else:
                    _fname = unicode(_fileName)
                self.ui.gbDataRec.setEnabled(False)
                self.ui.twMarkers.setEnabled(False)
                self.setWindowTitle('Saving data to %s ...' % _bname)
                self.sigSaveData.emit(self, self.data, _fname)

    def _gotostartofplot(self):
        """
        Callback to goto start of data button
        :return: None
        """
        if 'data' in self.data and 'time' in self.data and len(self.data['time']) > 0 and (len(self.plots) > 0):
            _origXRange = self.plots[-1].viewRange()[0]
            _origXrangeDiff = _origXRange[1] - _origXRange[0]
            # Get Minimum of X in data
            _initxrange = self.data['time'][0]
            if _initxrange != _origXRange[0]:
                self.plots[-1].setXRange(_initxrange, _initxrange + _origXrangeDiff, padding=0)

    def _gotoendofplot(self):
        """
        Callback to goto end of data button
        :return: None
        """
        if 'data' in self.data and 'time' in self.data and len(self.data['time']) > 0 and (len(self.plots) > 0):
            _origXRange = self.plots[-1].viewRange()[0]
            _origXrangeDiff = _origXRange[1] - _origXRange[0]
            # Get Minimum of X in data
            _endxrange = self.data['time'][-1]
            if _endxrange != _origXRange[1]:
                self.plots[-1].setXRange(_endxrange - _origXrangeDiff, _endxrange, padding=0)

    def _select_add_marker(self):
        """
        Callback to add marker tool button
        :return:
        """
        self._flagaddmarker = self.ui.tbtnAddMarker.isChecked()
        if self._flagaddmarker:
            if self.ui.tbtnEdit.isChecked():
                self.ui.tbtnEdit.setChecked(False)
            if self.ui.tbtnEdit.isEnabled():
                self.ui.tbtnEdit.setEnabled(False)
            self.plots[0].getViewBox().setCursor(QtCore.Qt.CrossCursor)
        else:
            if not self.ui.tbtnEdit.isEnabled():
                self.ui.tbtnEdit.setEnabled(True)
            self.plots[0].getViewBox().setCursor(QtCore.Qt.ArrowCursor)

    def _select_edit_marker(self):
        """
        Callback to edit marker tool button
        :return:
        """
        self._flageditmarker = self.ui.tbtnEdit.isChecked()
        if self._flageditmarker:
            if self.ui.tbtnAddMarker.isChecked():
                self.ui.tbtnAddMarker.setChecked(False)
            if self.ui.tbtnAddMarker.isEnabled():
                self.ui.tbtnAddMarker.setEnabled(False)
            # Enable marker line editing #
            for (_p, _l) in self.__markerlines:
                _l.setMovable(True)
        else:
            for (_p, _l) in self.__markerlines:
                _l.setMovable(False)
            if not self.ui.tbtnAddMarker.isEnabled():
                self.ui.tbtnAddMarker.setEnabled(True)

    def _show_fullscreen(self):
        """
        Callback to edit marker tool button
        :return:
        """
        if self.ui.tbtnFullScreen.isChecked():
            self.ui.plotter.setParent(None)
            self.ui.plotter.showFullScreen()
        else:
            self.ui.plotter.showNormal()
            self.ui.verticalLayout_2.insertWidget(1, self.ui.plotter)

    @QtCore.pyqtSlot(QtGui.QKeyEvent)
    def _on_fullscreen_esc(self, event):
        """
        Handle ESC Key to exit from full screen
        :param event:
        :return:
        """
        if self.ui.tbtnFullScreen.isChecked():
            if event.key() == QtCore.Qt.Key_Escape:
                self.ui.tbtnFullScreen.setChecked(False)
                self._show_fullscreen()
                event.accept()
            elif event.key() == QtCore.Qt.Key_Home:
                self._gotostartofplot()
            elif event.key() == QtCore.Qt.Key_End:
                self._gotoendofplot()
            else:
                event.ignore()
        else:
            event.ignore()

    ################ Initializing Functions #########################

    def _loadicons(self):
        """
        Load Icons from disk and display them
        :return: None
        """
        try:
            self.ui.tbtnStart.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                               'resources', 'if_player_start_379.png')))
        except:
            print 'Debugging : Unable to add goto start icon'
        try:
            self.ui.tbtnEnd.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources', 'if_player_end_373.png')))
        except:
            print 'Debugging : Unable to add goto end icon'
        try:
            self.ui.tbtnEdit.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                              'resources', 'if_comment_edit_40745.png')))
        except:
            print 'Debugging : Unable to add edit icon'

        try:
            self.ui.tbtnAddMarker.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                   'resources', 'if_add_290.png')))
        except:
            print 'Debugging : Unable to add add-marker icon'
        try:
            self.ui.tbtnFullScreen.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                    'resources', 'if_window_fullscreen_428.png')))
        except:
            print 'Debugging : Unable to add fullscreen icon'
        try:
            self.ui.btnSave.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources', 'if_filesave_326.png')))
        except:
            print 'Debugging : Unable to add file save icon'
        try:
            self.ui.btnClear.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                              'resources', 'if_history_clear_1979.png')))
        except:
            print 'Debugging : Unable to add clear history icon'

        try:
            self.ui.btnLoad.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources', 'if_icon-58-document-upload_314515.png')))
        except:
            print 'Debugging : Unable to add load icon'
        try:
            self.__icon_streaming_ready = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                   'resources', 'if_button_grey_record_50040.png'))
        except:
            self.__icon_streaming_ready = None
            print 'Unable to add streaming ready icon'
        try:
            self.__icon_streaming_started = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                     'resources', 'if_button_green_record_50030.png'))
        except:
            self.__icon_streaming_started = None
            print 'Unable to add streaming ready icon'
        if self.__icon_streaming_ready is not None:
            self.ui.btnRecord.setIcon(self.__icon_streaming_ready)
        # Edit Remove Icon #
        try:
            self.__icon_edit = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'if_comment_edit_40745.png'))
        except:
            print 'Unable to add edit icon'
        try:
            self.__icon_remove = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                          'resources', 'if_fileclose_320.png'))
        except:
            print 'Unable to add remove icon'
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'
        # Load Signal Strength Icons #
        self.__icon_sigstrength = []
        try:
            self.__icon_sigstrength.append(QtGui.QPixmap(os.path.join(
                os.path.dirname(__file__), '..', 'interface',
                'resources', 'if_signal-wifi-1-bar_326605.png')).scaledToHeight(32))
        except:
            self.__icon_sigstrength.append(None)
            print 'Unable to add sig strength 0 icon'
        try:
            self.__icon_sigstrength.append(QtGui.QPixmap(os.path.join(
                os.path.dirname(__file__), '..', 'interface',
                'resources', 'if_signal-wifi-2-bar_326607.png')).scaledToHeight(32))
        except:
            self.__icon_sigstrength.append(None)
            print 'Unable to add sig strength 1 icon'
        try:
            self.__icon_sigstrength.append(QtGui.QPixmap(os.path.join(
                os.path.dirname(__file__), '..', 'interface',
                'resources', 'if_signal-wifi-3-bar_326610.png')).scaledToHeight(32))
        except:
            self.__icon_sigstrength.append(None)
            print 'Unable to add sig strength 2 icon'
        try:
            self.__icon_sigstrength.append(QtGui.QPixmap(os.path.join(
                os.path.dirname(__file__), '..', 'interface',
                'resources', 'if_signal-wifi-4-bar_326612.png')).scaledToHeight(32))
        except:
            self.__icon_sigstrength.append(None)
            print 'Unable to add sig strength 3 icon'

    def _connectothersignals(self):
        """
        Connect Signals for UI buttons etc.
        :return: None
        """
        self.ui.btnClear.clicked.connect(self._manualclear)
        self.ui.btnSave.clicked.connect(self._savedatadialog)
        self.ui.tbtnStart.clicked.connect(self._gotostartofplot)
        self.ui.tbtnEnd.clicked.connect(self._gotoendofplot)
        self.ui.tbtnAddMarker.clicked.connect(self._select_add_marker)
        self.ui.tbtnEdit.clicked.connect(self._select_edit_marker)
        self.ui.tbtnFullScreen.clicked.connect(self._show_fullscreen)
        self.ui.twMarkers.cellClicked.connect(self._on_marker_table_clicked)
        self.ui.plotter.keyPressEvent = self._on_fullscreen_esc
        # todo if any other feature

    ######## Markers Editing and Display ################

    @QtCore.pyqtSlot(int, int)
    def _on_marker_table_clicked(self, _row, _col):
        """
        Adjust to display so that this marker is in view
        :param _row:
        :param _col:
        :return: None
        """
        if 'markers' not in self.data:
            return
        if _row < 0 or _row >= len(self.data['markers']):
            return
        if 'time' not in self.data:
            return
        if len(self.plots) == 0:
            return
        _tm = self.data['markers'][_row][1]
        _xdisp = self.plots[-1].viewRange()[0]
        _xrange = _xdisp[1] - _xdisp[0]
        _xrangehalf = _xrange / 2.0
        _xmin = self.data['time'][0]
        _xmax = self.data['time'][-1]
        if (_xrangehalf + _tm) > _xmax:
            _r2 = _xmax
        else:
            _r2 = _xrangehalf + _tm
        if (_r2 - _xrange) < _xmin:
            _r1 = _xmin
        else:
            _r1 = _r2 - _xrange
        self.plots[-1].setXRange(_r1, _r2)

    def _plotmarkersandverlines(self):
        """
        Plot Markers on plot and vertical lines showing them
        :return:
        """
        # Clear Markers Plots #
        self.plotdata[0].clear()
        for (_p, _l) in self.__markerlines:
            _p.removeItem(_l)
            if _l.scene() is None:
                _l.markerNum = -1
        self.__markerlines = []
        # Draw Markers Lines #
        if 'markers' in self.data:
            for _i in range(len(self.data['markers'])):
                ## Add Data to plot of markers ##
                _row = self.data['markers'][_i]
                if (_row[1] >= self.data['time'][self._idxolddata[0]]) and \
                        (_row[1] <= self.data['time'][self._idxolddata[1]]):
                    self.plotdata[0].addPoints(x=[_row[1]], y=[0.0])
                    for _plt in self.plots:
                        _lin = _plt.addLine(x=_row[1], z=2, pen='r')
                        if self._flageditmarker:
                            _lin.setMovable(True)
                        else:
                            _lin.setMovable(False)
                        _lin.sigPositionChangeFinished.connect(self._markerlinemoved)
                        _lin.setHoverPen(pg.mkPen(width=5, color='g'))
                        # Setup Bounds for editing #
                        if _i-1 >= 0:
                            _minlinbound = self.data['markers'][_i -1][1]+0.001
                        else:
                            _minlinbound = self.data['time'][0]
                        if _i+1 < len(self.data['markers']):
                            _maxlinbound = self.data['markers'][_i + 1][1] - 0.001
                        else:
                            _maxlinbound = self.data['time'][-1]    # TODO Update on New Data
                        _lin.setBounds((_minlinbound, _maxlinbound))
                        _lin.markerNum = _i
                        ############################
                        self.__markerlines.append((_plt, _lin))

    def _loadmarkerstable(self):
        """
        Load markers that are displayed in UI
        :return: None
        """
        # Clear Markers Table #
        self.ui.twMarkers.clearContents()
        # Load Markers Table #
        if 'markers' in self.data:
            self.ui.twMarkers.setRowCount(len(self.data['markers']))
            for _i in range(len(self.data['markers'])):
                _row = self.data['markers'][_i]
                self.ui.twMarkers.setItem(_i, 0, QtGui.QTableWidgetItem('%s'%_row[0]))
                self.ui.twMarkers.item(_i, 0).setToolTip('%s'%_row[0])
                self.ui.twMarkers.setItem(_i, 1, QtGui.QTableWidgetItem("%.3f" % _row[1]))
                _btnedit = QtGui.QToolButton()
                if self.__icon_edit is not None:
                    _btnedit.setIcon(self.__icon_edit)
                else:
                    _btnedit.setText('E')
                _btnrem = QtGui.QToolButton()
                if self.__icon_remove is not None:
                    _btnrem.setIcon(self.__icon_remove)
                else:
                    _btnrem.setText('R')
                _btnedit.setFixedSize(32, 32)
                _btnrem.setFixedSize(32, 32)
                _btnedit.setToolTip('Edit this marker')
                _btnrem.setToolTip('Remove this marker')
                _btnedit.marker_row = _i
                _btnrem.marker_row = _i
                _btnedit.clicked.connect(self._edit_marker)
                _btnrem.clicked.connect(self._remove_marker)
                _lyt = QtGui.QHBoxLayout()
                _lyt.setContentsMargins(0, 0, 0, 0)
                _lyt.addWidget(_btnedit)
                _lyt.addWidget(_btnrem)
                _lyt.setSizeConstraint(QtGui.QBoxLayout.SetFixedSize)
                _cwdg = QtGui.QWidget()
                _cwdg.setLayout(_lyt)
                self.ui.twMarkers.setCellWidget(_i, 2, _cwdg)
        else:
            self.ui.twMarkers.setRowCount(0)
        # Adjust Contents #
        self.ui.twMarkers.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.ui.twMarkers.resizeColumnToContents(1)
        self.ui.twMarkers.resizeColumnToContents(2)
        # Show in plots #
        self._plotmarkersandverlines()

    def _remove_marker(self):
        """
        Removes Marker and update display
        :return: None
        """
        _rowtorem = self.sender().marker_row
        try:
            self.data['markers'].pop(_rowtorem)
        except:
            print 'Debugging : Error on Marker Removal, Fix it if it shows'
        self._loadmarkerstable()

    def _edit_marker(self):
        """
        Callback to edit markers when clicked in markers table
        :return: None
        """
        if not hasattr(self.sender(), 'marker_row'):
            return # Signal Sender not our button
        _marker_row = self.sender().marker_row
        if _marker_row >= len(self.data['markers']):
            return # Marker No longer Existing, Something went Wrong
        # Construct Marker Data for dialog #
        _marker_data = {'marker': self.data['markers'][_marker_row][0], 'time': self.data['markers'][_marker_row][1],
                        'event': self.data['markers'][_marker_row][2], 'remark': self.data['markers'][_marker_row][3]}
        ## Construct Markers List ##
        _marker_list = [_mrk[0] for _mrk in self.data['markers']]
        ## Display Dialog for Editing ##
        _dlgmarker = GaiTechDataMakerDialog(markerlist=_marker_list, data=_marker_data)
        if _dlgmarker.exec_() == QtGui.QDialog.Accepted and _dlgmarker.isModified():
            _dmrkmod = _dlgmarker.getData()
            self.data['markers'][_marker_row] = (_dmrkmod['marker'], _dmrkmod['time'],
                                                 _dmrkmod['event'], _dmrkmod['remark'])
            # Update On Table
            self.ui.twMarkers.item(_marker_row, 0).setText('%s' % _dmrkmod['marker'])
            self.ui.twMarkers.item(_marker_row, 0).setToolTip('%s' % _dmrkmod['marker'])

    #####################################################

    def _find_nearest_time_in_data(self, tsearch):
        """
        Searches to find nearest valid value of time in data
        :param tsearch: time to search
        :return: (actual_value, idx)
        """
        if 'time' not in self.data:
            return 0.0, -1
        _pos = bisect_left(self.data['time'], tsearch)
        if _pos == 0:
            return self.data['time'][0], 0
        if _pos == len(self.data['time']):
            return self.data['time'][-1], len(self.data['time']) - 1
        _before = self.data['time'][_pos - 1]
        _after = self.data['time'][_pos]
        if (_after - tsearch) < (tsearch - _before):
            return _after, _pos
        else:
            return _before, _pos - 1

    def _generate_random_marker_name(self):
        """
        Generates a new random marker id
        :return:
        """
        if 'markers' not in self.data:
            return 'marker_000001'
        _marker_list = [_mrk[0] for _mrk in self.data['markers']]
        import random
        _mrk = 'marker_000001'
        while _mrk in _marker_list:
            __i = random.randint(0, 999999)
            _mrk = 'marker_%06d' % __i
        return _mrk

    @QtCore.pyqtSlot(bool)
    def _onStreamChange(self, _val):
        """
        Forcefully set streaming setting for Live Data
        :param _val: True or False
        :return:
        """
        if self.live:
            if _val and not self._flagstreamon:
                self._streamingonoff()
            elif not _val and self._flagstreamon:
                self._streamingonoff()

    @QtCore.pyqtSlot(unicode)
    def _savingcomplete(self, _fn):
        """
        Callback to saving complete event
        :param _fn:
        :return:
        """
        if self.live:
            self.setWindowTitle('Live Data Viewer')
        else:
            self.setWindowTitle(_fn)
        self.ui.gbDataRec.setEnabled(True)
        self.ui.twMarkers.setEnabled(True)

    @QtCore.pyqtSlot(dict, unicode)
    def loadOfflineData(self, offlinedata, _fn):
        """
        Loads Offline Data for Display ( only for offline )
        offlinedata = {mode:'Common Reference|Average Reference|Longitudinal-Bipolar|Transverse-Bipolar',
         data=dict(depending upon mode), time= np.array, markers=[(id, time, event, note), ...]}

        Common Reference : data = {Fp1:np.array, Fp2: np.array, F7: np.array, F8: np.array, T3: np.array, T4: np.array
        T5 : np.array, T6: np.array, O1:np.array}
        Average Reference : data = {Fp1-Avg:np.array, Fp2-Avg: np.array, F7-Avg: np.array, F8-Avg: np.array,
        T3-Avg: np.array, T4-Avg: np.array, T5-Avg: np.array, T6-Avg: np.array, O1-Avg: np.array, O2-Avg: np.array}
        Longitudinal-Bipolar: data = {Fp1-F7: np.array, Fp2-F8: np.array, F7-T3: np.array, T8-T4: np.array,
        T3-T5: np.array, T4-T6: np.array, T5-O1: np.array, T6-O2: np.array}
        Transverse-Bipolar : data = {Fp1-Fp2: np.array, F7-F8: np.array, T3-T4: np.array, T5-T6:np.array,
        O1-O2: np.array}

        if there is any discrepency in data elements and time the minimum data will be used for all cases
        For Events whose time is more than that of data, they will be ignored

        :return: None
        """
        self.ui.gbDataRec.setEnabled(True)
        ### Clear Data ####
        self._manualclear()
        # Internally Data is stored in python list instead of numpy list for compatibility with live data
        ###### Load Data #######
        # MODE #
        if 'mode' in offlinedata:
            if offlinedata['mode'] == 'Common Reference':
                self._setchnls(0)
            elif offlinedata['mode'] == 'Average Reference':
                self._setchnls(1)
            elif offlinedata['mode'] == 'Longitudinal-Bipolar':
                self._setchnls(2)
            elif offlinedata['mode'] == 'Transverse-Bipolar':
                self._setchnls(3)
            else:
                raise ValueError('mode unknown')
            self.data['mode'] = offlinedata['mode']
        else:
            raise ValueError('mode not set in data')
        # Time #
        if 'time' in offlinedata and isinstance(offlinedata['time'], np.ndarray) and offlinedata['time'].shape[0] > 0:
            self.data['time'] = offlinedata['time'].tolist()
        elif 'time' in offlinedata and isinstance(offlinedata['time'], list) and len(offlinedata['time']) > 0:
            self.data['time'] = offlinedata['time']
        else:
            raise ValueError('time in data not present')
        _mintime = self.data['time'][0]
        _maxtime = self.data['time'][-1]
        # Initialize dict item for data #
        self.data['data'] = dict()
        # Load Markers #
        if 'markers' in offlinedata:
            self.data['markers'] = offlinedata['markers']
        else:
            self.data['markers'] = []   # Dont raise errors as markers are optional
        self._loadmarkerstable()
        # Draw Plots #
        for _pltdata in self.plotdata:
            if hasattr(_pltdata, 'channelname'):
                _chnlname = _pltdata.channelname
                if _chnlname in offlinedata['data']:
                    if isinstance(offlinedata['data'][_chnlname], np.ndarray):
                        self.data['data'][_chnlname] = offlinedata['data'][_chnlname].tolist()
                    elif isinstance(offlinedata['data'][_chnlname], list):
                        self.data['data'][_chnlname] = offlinedata['data'][_chnlname]
        # Add Plot Time Limits #
        _dispXMaxTime = _mintime + 30.0
        if _dispXMaxTime > _maxtime:
            _dispXMaxTime = _maxtime
        for _plt in self.plots:
            _plt.setLimits(xMin=_mintime, xMax=_maxtime)
            _plt.setXRange(_mintime, _dispXMaxTime)
        if _fn is not None and _fn != '':
            self.setWindowTitle('%s' % _fn)

    @QtCore.pyqtSlot(int)
    def _onNewMode(self, md):
        """
        Handle to mode change event
        :param md: mode
        :return:
        """
        if self._flagstreamon:
            self._streamingonoff()
        self._setchnls(md)

    @QtCore.pyqtSlot(list)
    def _onNewMarker(self, evnt):
        """
        Handle New Markers
        :param evnt: markers=[(id, time, event, note), ...]
        :return: None
        """
        if not self._flagstreamon:
            return
        if evnt is None or not isinstance(evnt, list):
            return
        if 'markers' not in self.data:
            self.data['markers'] = []
        _marker_list = [_mrk[0] for _mrk in self.data['markers']]
        for _mrk in evnt:
            if _mrk[0] in _marker_list:
                _mname = self._generate_random_marker_name()
                _me = (_marker_list, _mrk[1], _mrk[2], _mrk[3])
            else:
                _me = _mrk
            self.data['markers'].append(_me)
        #### Update Markers Table ####
        self._loadmarkerstable()

    @QtCore.pyqtSlot(dict)
    def _onNewData(self, _data):
        """
        Handle New Data
        :param _data: {mode:'Common Reference|Average Reference|Longitudinal-Bipolar|Transverse-Bipolar',
         data=dict(depending upon mode, same format as offline data but python list), time= list}
        :return: None
        """
        if not self._flagstreamon:
            return
        if _data is None:
            return
        if 'mode' not in _data or _data['mode'] is None:
            return
        if 'time' not in _data or _data['time'] is None or not isinstance(_data['time'], list):
            return
        if 'data' not in _data or _data['data'] is None or not isinstance(_data['data'], dict):
            return
        if str(self.ui.lblDMode.text()) != _data['mode']:
            print 'Debugging : Mode Different From That of Live Data Receiving'
            return
        ### Verify that data contains all the fields as in plotdata ###
        _verifyData = True
        for _plt in self.plotdata:
            if hasattr(_plt, 'channelname'):
                if _plt.channelname not in _data['data']:
                    _verifyData = False
                    break
        if not _verifyData:
            return
        if 'mode' not in self.data:
            self.data['mode'] = _data['mode']
        elif self.data['mode'] != _data['mode']:
            print 'Debugging : This message should never be triggered, mode different'
            return
        _dataupdated = False
        _len = len(_data['time'])
        _origXRange = self.plots[-1].viewRange()[0]
        _origXrangeDiff = _origXRange[1] - _origXRange[0]
        _rideatend = False
        if 'time' in self.data and isinstance(self.data['time'], list):
            if np.abs(self.data['time'][-1] - _origXRange[1]) < 0.5:
                _rideatend = True
        if 'time' not in self.data:
            _rideatend = True
        ### Load Data if earlier present ###
        if 'time' in self.data and isinstance(self.data['time'], list) and 'data' in self.data and \
                isinstance(self.data['data'], dict) and (set(self.data['data'].keys()) == set(_data['data'].keys())):
            if _len > 0:    # There is time data
                _dataGood = True
                # Test Data is numpy array and has same length #
                for _k in _data['data']:
                    if not isinstance(_data['data'][_k], list) or len(_data['data'][_k]) != _len:
                        _dataGood = False
                        break
                ##
                if _dataGood:
                    # All Good Append Data #
                    self.data['time'].extend(_data['time'])
                    for _k in self.data['data']:
                        self.data['data'][_k].extend(_data['data'][_k])
                    _dataupdated = True
        ### Create Empty Data fields if not present earlier ###
        if 'time' not in self.data and 'data' not in self.data and _len > 0:
            _datagoodinit = True
            ### Initialize Data if got a valid one ###
            for _k in _data['data']:
                if not isinstance(_data['data'][_k], list) or len(_data['data'][_k]) != _len:
                    _datagoodinit = False
                    break
            if _datagoodinit:
                self.data['time'] = _data['time']
                self.data['data'] = _data['data']
                self.data['markers'] = []   # Initialize Markers
                ### Add A New Marker For Showing Streaming Started ### TODO
                _dataupdated = True
        ### Update Views Etc. ###
        if _dataupdated:
            _mintime = self.data['time'][0]
            _maxtime = self.data['time'][-1]
            for _plt in self.plots:
                if (_maxtime - _mintime) > 1.0:
                    _plt.setLimits(xMin=_mintime, xMax=_maxtime)
                else:
                    _plt.setLimits(xMin=_mintime, xMax=_mintime+1.0)
            if self.isVisible() and _rideatend and (time.time() - self.__livelastdisp) >= (1.0/90.0):
                self.__livescrolling = True
                self.__livelastdisp = time.time()
                _dispsttime = _maxtime - _origXrangeDiff
                if _dispsttime < self.data['time'][0]:
                    _dispsttime = self.data['time'][0]
                self._update_data_loaded_recently()
                self.plots[-1].setXRange(_dispsttime, _maxtime, padding=0.0)
            else:
                self.__livescrolling = False

    # Helping Functions #
    def __init_checkboxes(self, _mode):
        _cbxs = []
        if _mode == 0:
            self.ui.lblDMode.setText('Common Reference')
            _cbxs.append(QtGui.QCheckBox('Fp1'))
            _cbxs.append(QtGui.QCheckBox('Fp2'))
            _cbxs.append(QtGui.QCheckBox('F7'))
            _cbxs.append(QtGui.QCheckBox('F8'))
            _cbxs.append(QtGui.QCheckBox('T3'))
            _cbxs.append(QtGui.QCheckBox('T4'))
            _cbxs.append(QtGui.QCheckBox('T5'))
            _cbxs.append(QtGui.QCheckBox('T6'))
            _cbxs.append(QtGui.QCheckBox('O1'))
            _cbxs.append(QtGui.QCheckBox('O2'))
        elif _mode == 1:
            self.ui.lblDMode.setText('Average Reference')
            _cbxs.append(QtGui.QCheckBox('Fp1-Avg'))
            _cbxs.append(QtGui.QCheckBox('Fp2-Avg'))
            _cbxs.append(QtGui.QCheckBox('F7-Avg'))
            _cbxs.append(QtGui.QCheckBox('F8-Avg'))
            _cbxs.append(QtGui.QCheckBox('T3-Avg'))
            _cbxs.append(QtGui.QCheckBox('T4-Avg'))
            _cbxs.append(QtGui.QCheckBox('T5-Avg'))
            _cbxs.append(QtGui.QCheckBox('T6-Avg'))
            _cbxs.append(QtGui.QCheckBox('O1-Avg'))
            _cbxs.append(QtGui.QCheckBox('O2-Avg'))
        elif _mode == 2:
            self.ui.lblDMode.setText('Longitudinal-Bipolar')
            _cbxs.append(QtGui.QCheckBox('Fp1-F7'))
            _cbxs.append(QtGui.QCheckBox('Fp2-F8'))
            _cbxs.append(QtGui.QCheckBox('F7-T3'))
            _cbxs.append(QtGui.QCheckBox('F8-T4'))
            _cbxs.append(QtGui.QCheckBox('T3-T5'))
            _cbxs.append(QtGui.QCheckBox('T4-T6'))
            _cbxs.append(QtGui.QCheckBox('T5-O1'))
            _cbxs.append(QtGui.QCheckBox('T6-O2'))
        elif _mode == 3:
            self.ui.lblDMode.setText('Transverse-Bipolar')
            _cbxs.append(QtGui.QCheckBox('Fp1-Fp2'))
            _cbxs.append(QtGui.QCheckBox('F7-F8'))
            _cbxs.append(QtGui.QCheckBox('T3-T4'))
            _cbxs.append(QtGui.QCheckBox('T5-T6'))
            _cbxs.append(QtGui.QCheckBox('O1-O2'))
        else:
            self.ui.lblDMode.setText('Unknown Mode')
        return _cbxs

    @staticmethod
    def __set_symbol_plotdata_None(_pltitm, chnlname):
        if hasattr(_pltitm, 'channelname') and _pltitm.channelname == chnlname:
            if _pltitm.opts['symbol'] is not None:
                _pltitm.setSymbol(None)
            return True
        return False

    @staticmethod
    def __set_symbol_plotdata(_pltitm, chnlname):
        if hasattr(_pltitm, 'channelname') and _pltitm.channelname == chnlname:
            if _pltitm.opts['symbol'] is None:
                _pltitm.setSymbol('d')
            return True
        return False

