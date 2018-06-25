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
Widget related to settings for device
"""
import sys, os
from PyQt4 import QtCore, QtGui
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'interface'))
from H10CSettings import Ui_H10CSettings
from GaitechDialogs import GaiTechLicenceDialog


######### Class Gaitech Settings Widget ######
class GaitechSettings(QtGui.QWidget):
    """
    Gaitech Settings Widget for Avertus H10C Devices
    """
    ## Signals Emitted ##
    sigScanDevices = QtCore.pyqtSignal(QtGui.QWidget)  # Signal Emitted by Gaitech Settings to initiate Scan
    sigConnectDevice = QtCore.pyqtSignal(QtGui.QWidget, str,
                    int)  # Signal Emitted by Gaitech Settings to start Connection 0 Connect 1 Disconnect
    sigRefModeChange = QtCore.pyqtSignal(int)  # Signal Emitted by Gaitech Settings on refmode change
    sigLicenceModified = QtCore.pyqtSignal(list) # Signal Emitted by Gaitech Settings when licence changed
    sigFilterModified = QtCore.pyqtSignal(dict) # Signal Emitted by Gaitech Settings on filter applied
    sigScanNodes = QtCore.pyqtSignal(QtGui.QWidget) # Signal Emitted by Gaitech Settings to search running gaitech_bci
    sigNodeModified = QtCore.pyqtSignal(str) # Signal Emitted whenever active node is changed
    ## Signals Catched ##
    sigScanReceived = QtCore.pyqtSignal(list)       # Signal Received by Gaitech Settings on scan_results
    sigNodesReceived = QtCore.pyqtSignal(list)      # Signal Received by Gaitech Settings for running gaitech_bci
    sigConnectionStatus = QtCore.pyqtSignal(int)      # 0 connecting, 1 connected, 2 disconnecting, 3 disconnected
    sigConnectivityStatus = QtCore.pyqtSignal(float, float) # Signal Received by Gaitech Settings for loss information
    sigLicenceUpdated = QtCore.pyqtSignal(list) # Signal Received by Gaitech Settings when licence updated from outside
    sigFilterUpdated = QtCore.pyqtSignal(list) # Signal Received by Gaitech Settings when filter params recv from outside
    sigRefModeUpdated = QtCore.pyqtSignal(int) # Reference mode update from outside, to be received by Gaitech Settings
    sigDeviceInitialize = QtCore.pyqtSignal(str) # Initialize UI based on device name
    sigElectrodeUpdated = QtCore.pyqtSignal(dict) # Electrode connectivity information received
    ##

    def __init__(self, parent=None):
        """
        Initialize Gaitech Settings widget
        :param parent: parent widget of Gaitech settings, default=None
        """
        super(GaitechSettings, self).__init__(parent)
        self.ui = Ui_H10CSettings()
        self.ui.setupUi(self)
        # Initialize Data Members #
        self._allnodes = []      # All gaitech_bci ROS Nodes currently Running
        self._lkeys = []         # LKeys for Licence Dialog
        self._nearbydevices = [] # An array of tuples (Devname, licenced_bool)
        self._activedevice = {'dev': 'None', 'conn': 3, 'ref': 0, 'loss1': 0.0, 'loss2': 0.0, 'selectable': True,
                              'locked': False}
        self._filtersettings = {'high':10.0, 'low':100.0, 'nlow':49.0, 'nhigh':50.0, 'locked': False}
        self._electrodestatus = {'Fp1': 0.0, 'Fp2': 0.0, 'F7': 0.0, 'F8': 0.0, 'T3': 0.0, 'T4': 0.0,
                                 'T5': 0.0, 'T6': 0.0, 'O1': 0.0, 'O2': 0.0}
        self._activenode = None
        self.__updatinglist = False
        self.__updatingnodelist = False
        self.__updatingrefmode = False
        self.__image_drawn = None
        self.__image_circle_size = 40
        self.scene = QtGui.QGraphicsScene(None)
        # inital tooltips and load resources #
        self.ui.cmbDevName.setToolTip('Select device to connect to')
        self.ui.btnConnDiscon.setToolTip('Connect to device')
        self._initialize_ui()
        # Initialize Other Stuff #
        self._loadNearByDevices(self._nearbydevices)
        self._update_active_device_ui()
        self._update_filter_settings()
        # Connect Events #
        self._connectcallbacks()
        # Initial State Emit #
        self._enable_All_Interface(False)
        self.ui.gbROS.setChecked(True)
        self.ui.cmbNode.setEnabled(False)
        self._draw_device_ui()

    def _connectcallbacks(self):
        """
        Connect call back functions to respective events
        :return: None
        """
        self.ui.btnScan.clicked.connect(self._scan_nearby)
        self.ui.btnConnDiscon.clicked.connect(self._connect_device)
        self.ui.btnLKey.clicked.connect(self.lkey_dialog)
        self.ui.btnNode.clicked.connect(self._search_nodes)
        self.ui.btnboxFilter.clicked.connect(self._fiter_btn_pressed)
        self.ui.dspinLow.valueChanged.connect(self._test_filter_update_range)
        self.ui.dspinHigh.valueChanged.connect(self._test_filter_update_range)
        self.ui.dspinNLow.valueChanged.connect(self._test_filter_update_range)
        self.ui.dspinNHigh.valueChanged.connect(self._test_filter_update_range)
        self.ui.graphicsView.resizeEvent = self._gDispElecResizeEvent  # Hook resize event
        # Active device changed
        self.ui.cmbDevName.currentIndexChanged.connect(self._active_device_changed)
        self.ui.cmbRefMode.currentIndexChanged.connect(self._refmode_changed)
        self.ui.cmbNode.currentIndexChanged.connect(self._active_node_changed)
        # Connect Signals
        self.sigDeviceInitialize.connect(self._devinitialize)
        self.sigScanReceived.connect(self._loadNearByDevices)
        self.sigConnectionStatus.connect(self._updateconnectionstatus)
        self.sigRefModeUpdated.connect(self._refmodeupdated)
        self.sigConnectivityStatus.connect(self._updateLoss)
        self.sigLicenceUpdated.connect(self._licencekeysupdated)
        self.sigFilterUpdated.connect(self._filterupdated)
        self.sigNodesReceived.connect(self._nodeupdated)
        self.sigElectrodeUpdated.connect(self._onelectrodeupdate)

    def getActiveMode(self):
        """
        Returns current active mode
        :return:
        """
        return self._activedevice['ref']

    def getConnectionStatus(self):
        """
        Returns current connection status
        :return:
        """
        return self._activedevice['conn']

    def getActiveDevice(self):
        """
        Returns active device
        :return:
        """
        return self._activedevice['dev']

    def getLicenceKeys(self):
        """
        Get stored licence keys
        :return:
        """
        return self._lkeys

    @QtCore.pyqtSlot(str)
    def _devinitialize(self, _dname):
        """
        Initialize UI based on device name
        :param _dname:
        :return:
        """
        self.sigScanReceived.emit([(_dname, True)])
        _posidx = self.ui.cmbDevName.findText(_dname)
        if _posidx != -1:
            self.ui.cmbDevName.setCurrentIndex(_posidx)
            self._update_active_device_ui()

    @QtCore.pyqtSlot(list)
    def _loadNearByDevices(self, devices):
        """
        Loads nearby devices in _nearbydevices data members and updates the ui
        :param devices: An array of (dev, licvalid) tuples
        :return: None
        """
        self._nearbydevices = []
        self._activedevice['locked'] = False
        for _dev in devices:
            if len(_dev) == 2:
                self._nearbydevices.append((_dev[0], _dev[1]))
        _mdl = QtGui.QStandardItemModel()
        for _dev in self._nearbydevices:
            _itm = QtGui.QStandardItem()
            _itm.setText('Avertus - %s'%_dev[0])
            _itm.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

            if _dev[1]:
                _itm.setForeground(QtCore.Qt.darkGreen)
                _itm.setToolTip('You can connect to this device')
            else:
                _itm.setForeground(QtCore.Qt.red)
                _itm.setToolTip('No Licence Key for this device')
            _mdl.appendRow(_itm)
        self.ui.ldevView.setModel(_mdl)
        if len(self._nearbydevices) > 0:
            self.ui.ldevView.setToolTip('')
        else:
            self.ui.ldevView.setToolTip('No devices found nearby!')
        ## Re-Enable Scan Button ##
        self.ui.btnScan.setEnabled(True)
        # Update Connectable Devices #
        self._update_connectable_devices()

    @QtCore.pyqtSlot(int)
    def _updateconnectionstatus(self, sts):
        """
        Update connection information to ui
        :param sts: device sts number showing current status 0:connecting,1:connected,2:disconnecting,3:disconnected
        :return:
        """
        self._activedevice['conn'] = sts
        if sts == 0:
            self._activedevice['selectable'] = False
        elif sts == 1:
            self._activedevice['selectable'] = False
            self._activedevice['loss1'] = 0.0
            self._activedevice['loss2'] = 0.0
        elif sts == 2:
            self._activedevice['selectable'] = False
        elif sts == 3:
            self._activedevice['selectable'] = True
        self._update_active_device_ui()

    @QtCore.pyqtSlot(float, float)
    def _updateLoss(self, l1, l2):
        """
        Update loss information in ui
        :param l1: loss in latest 1 minutes
        :param l2: overall connection loss
        :return:
        """
        self._activedevice['loss1'] = l1
        self._activedevice['loss2'] = l2
        self._update_active_device_ui()

    @QtCore.pyqtSlot(dict)
    def _onelectrodeupdate(self, _elecinfo):
        """
        Show electrode information on UI
        :param _elecinfo: dictionary with electrode information
        :return:
        """
        self._electrodestatus['Fp1'] = _elecinfo['Fp1']
        self._electrodestatus['Fp2'] = _elecinfo['Fp2']
        self._electrodestatus['T3'] = _elecinfo['T3']
        self._electrodestatus['T4'] = _elecinfo['T4']
        self._electrodestatus['T5'] = _elecinfo['T5']
        self._electrodestatus['T6'] = _elecinfo['T6']
        self._electrodestatus['F7'] = _elecinfo['F7']
        self._electrodestatus['F8'] = _elecinfo['F8']
        self._electrodestatus['O1'] = _elecinfo['O1']
        self._electrodestatus['O2'] = _elecinfo['O2']
        self._draw_device_ui()

    @QtCore.pyqtSlot(list)
    def _licencekeysupdated(self, lkeys):
        """
        Signal Received when licence keys are updated from outside
        :param lkeys: list of licence keys
        :return: None
        """
        self._lkeys = lkeys

    @QtCore.pyqtSlot(list)
    def _filterupdated(self, newparams):
        """
        Signal Recevied when filter settings are updated from outside
        :param newparams: list with members [ low_filter, high_filter, notch_low_filter, notch_high_filter ]
        :return: None
        """
        if len(newparams) == 4:
            try:
                self._filtersettings['high'] = float(newparams[0])
                self._filtersettings['low'] = float(newparams[1])
                self._filtersettings['nlow'] = float(newparams[2])
                self._filtersettings['nhigh'] = float(newparams[3])
            except (TypeError, ValueError):
                print 'Debugging : New parameters for filter setting received by UI Error'
            self._update_filter_settings()

    @QtCore.pyqtSlot(int)
    def _refmodeupdated(self, md):
        """
        Handle reference mode updated from outside signal
        :param md:
        :return:
        """
        if md < 4:
            self._activedevice['ref'] = md
            self.__updatingrefmode = True
            self.ui.cmbRefMode.setCurrentIndex(self._activedevice['ref'])
            self.__updatingrefmode = False
            self._draw_device_ui()

    @QtCore.pyqtSlot(list)
    def _nodeupdated(self, newnodes):
        self._allnodes = newnodes
        self.ui.btnNode.setEnabled(True)
        if len(self._allnodes) > 0:
            self.__updatingnodelist = True
            self.ui.cmbNode.clear()
            for _nname in self._allnodes:
                self.ui.cmbNode.addItem(_nname)
            self.__updatingnodelist = False
            # Set Old Item if possible
            if self._activenode is not None:
                _posidx = self.ui.cmbNode.findText(self._activenode)
                if _posidx != -1:
                    self.ui.cmbNode.setCurrentIndex(_posidx)
                else:
                    self.ui.cmbNode.setCurrentIndex(0)
                    self._active_node_changed()
            else:
                self.ui.cmbNode.setCurrentIndex(0)
                self._active_node_changed()
            self._enable_All_Interface(True)
            self.ui.cmbNode.setEnabled(True)
            self.ui.cmbNode.setToolTip('Select gaitech_bci node')
        else:
            # No Valid Node Found #
            self.ui.cmbNode.setToolTip('No gaitech_bci node found')
            self.ui.cmbNode.setEnabled(False)
            self.ui.cmbNode.clear()
            self._activenode = None
            self.sigNodeModified.emit('')

    def _update_connectable_devices(self):
        """
        Update Connectable devices in combo list
        :return:
        """
        self.__updatinglist = True
        self.ui.cmbDevName.clear()
        self.ui.cmbDevName.addItem('None')
        for _dev in self._nearbydevices:
            if _dev[1]:
                self.ui.cmbDevName.addItem(_dev[0])
        # Set Old Item if possible
        _posidx = self.ui.cmbDevName.findText(self._activedevice['dev'])
        self.__updatinglist = False
        if _posidx != -1:
            self.ui.cmbDevName.setCurrentIndex(_posidx)
            self._update_active_device_ui()
        else:
            # Active device disappeared, disconnected and so on
            print 'Debugging : Device Disappeared after scan -- connection information lost'
            self._activedevice['dev'] = 'None'
            self._activedevice['loss1'] = 0.0
            self._activedevice['loss2'] = 0.0
            self.ui.cmbDevName.setCurrentIndex(0)
            self.sigConnectionStatus.emit(3)

    def _active_device_changed(self):
        """
        Handle Active Device Selection
        :return:
        """
        if self.__updatinglist:
            return
        if self.ui.cmbDevName.currentIndex() != -1:
            if self._activedevice['dev'] != str(self.ui.cmbDevName.currentText()):
                print 'Debugging : Active Device Selection Changed to %s' % str(self.ui.cmbDevName.currentText())
                # device changed handle appropriately
                self._activedevice['dev'] = str(self.ui.cmbDevName.currentText())
                self._activedevice['loss1'] = 0.0
                self._activedevice['loss2'] = 0.0
                self._update_active_device_ui()

    def _active_node_changed(self):
        """
        Handle Active Node Selection
        :return:
        """
        if self.__updatingnodelist:
            return
        if self.ui.cmbNode.currentIndex() != -1:
            if self._activenode is None or \
                    (self._activenode is not None and self._activenode != str(self.ui.cmbNode.currentText())):
                print 'Debugging : Active Node Selection Changed to %s' % str(self.ui.cmbNode.currentText())
                self._activenode = str(self.ui.cmbNode.currentText())
                ### Clear Other Connections etc ### PATCHED : Disconnect on active node change
                #if self._activedevice['dev'] != 'None' and self._activedevice['conn'] == 1:
                #    self._connect_device() # Force Disconnection
                ### Emit Signal for active node changed
                self.sigNodeModified.emit(self._activenode)

    def _update_filter_settings(self, lockonly=False):
        """
        Update values displayed by filter settings
        :param lockonly: Flag to update only lockstate
        :return: None
        """
        if not lockonly:
            self.ui.dspinHigh.setValue(self._filtersettings['high'])
            self.ui.dspinLow.setValue(self._filtersettings['low'])
            self.ui.dspinHigh.setValue(self._filtersettings['high'])        # Redoing for updated min/max range
            self.ui.dspinNHigh.setValue(self._filtersettings['nhigh'])
            self.ui.dspinNLow.setValue(self._filtersettings['nlow'])
            self.ui.dspinNHigh.setValue(self._filtersettings['nhigh'])      # Redoing for updated min/max range

        if self._filtersettings['locked']:
            if self.ui.dspinHigh.isEnabled():
                self.ui.dspinHigh.setEnabled(False)
            if self.ui.dspinLow.isEnabled():
                self.ui.dspinLow.setEnabled(False)
            if self.ui.dspinNHigh.isEnabled():
                self.ui.dspinNHigh.setEnabled(False)
            if self.ui.dspinNLow.isEnabled():
                self.ui.dspinNLow.setEnabled(False)
            if self.ui.btnboxFilter.isEnabled():
                self.ui.btnboxFilter.setEnabled(False)
        else:
            if not self.ui.dspinHigh.isEnabled():
                self.ui.dspinHigh.setEnabled(True)
            if not self.ui.dspinLow.isEnabled():
                self.ui.dspinLow.setEnabled(True)
            if not self.ui.dspinNHigh.isEnabled():
                self.ui.dspinNHigh.setEnabled(True)
            if not self.ui.dspinNLow.isEnabled():
                self.ui.dspinNLow.setEnabled(True)
            if not self.ui.btnboxFilter.isEnabled():
                self.ui.btnboxFilter.setEnabled(True)

    def _refmode_changed(self):
        """
        Handle user selection of reference mode and emit signal
        :return: None
        """
        if self.__updatingrefmode:
            return
        if self.ui.cmbRefMode.currentIndex() == 0:
            self._activedevice['ref'] = 0
        elif self.ui.cmbRefMode.currentIndex() == 1:
            self._activedevice['ref'] = 1
        elif self.ui.cmbRefMode.currentIndex() == 2:
            self._activedevice['ref'] = 2
        elif self.ui.cmbRefMode.currentIndex() == 3:
            self._activedevice['ref'] = 3
        self._draw_device_ui()
        self.sigRefModeChange.emit(self._activedevice['ref'])

    def _update_active_device_ui(self):
        """
        Update UI related to Active Device which is stored in _activedevice member
        :return:
        """
        if not self._activedevice['selectable']:
            if self.ui.cmbDevName.isEnabled():
                self.ui.cmbDevName.setEnabled(False)
                self.ui.cmbDevName.setToolTip('Disconnect first to change device')
        else:
            if not self.ui.cmbDevName.isEnabled():
                self.ui.cmbDevName.setEnabled(True)
                self.ui.cmbDevName.setToolTip('Select device to connect to')
        # Related to connection status
        if self._activedevice['conn'] == 0:
            if str(self.ui.btnConnDiscon.text()) != 'Connecting':
                self.ui.btnConnDiscon.setText('Connecting')
                self.ui.btnConnDiscon.setToolTip('Connecting to device')
            if self.ui.btnConnDiscon.isEnabled():
                self.ui.btnConnDiscon.setEnabled(False)
        elif self._activedevice['conn'] == 1:
            if str(self.ui.btnConnDiscon.text()) != 'Disconnect':
                self.ui.btnConnDiscon.setText('Disconnect')
                self.ui.btnConnDiscon.setToolTip('Disconnect from device')
            if not self._activedevice['locked'] and not self.ui.btnConnDiscon.isEnabled():
                self.ui.btnConnDiscon.setEnabled(True)
        elif self._activedevice['conn'] == 2:
            if str(self.ui.btnConnDiscon.text()) != 'Disconnecting':
                self.ui.btnConnDiscon.setText('Disconnecting')
                self.ui.btnConnDiscon.setToolTip('Disconnecting from device')
            if self.ui.btnConnDiscon.isEnabled():
                self.ui.btnConnDiscon.setEnabled(False)
        elif self._activedevice['conn'] == 3:
            if str(self.ui.btnConnDiscon.text()) != 'Connect':
                self.ui.btnConnDiscon.setText('Connect')
                self.ui.btnConnDiscon.setToolTip('Connect to device')
            if not self._activedevice['locked'] and not self.ui.btnConnDiscon.isEnabled():
                self.ui.btnConnDiscon.setEnabled(True)

        if self._activedevice['dev'] == 'None':
            if self.ui.btnConnDiscon.isEnabled(): # Always disable button
                self.ui.btnConnDiscon.setEnabled(False)
            if self.ui.cmbRefMode.isEnabled():
                self.ui.cmbRefMode.setEnabled(False)
        else:
            if not self.ui.cmbRefMode.isEnabled():
                self.ui.cmbRefMode.setEnabled(True)
        # Update loss information
        self.ui.lblSigLoss.setText('%0.2f%%'%self._activedevice['loss1'])
        # For Locked State #
        if self._activedevice['locked']:
            self.ui.btnConnDiscon.setEnabled(False)
            self.ui.cmbRefMode.setEnabled(False)
            self.ui.cmbDevName.setEnabled(False)

        # Filter Options only available when active device is not locked and connected #
        if not self._activedevice['locked'] and self._activedevice['conn'] == 1:
            self._filtersettings['locked'] = False
            self._update_filter_settings(lockonly=True)
        else:
            self._filtersettings['locked'] = True
            self._update_filter_settings(lockonly=True)

    def _enable_All_Interface(self, status=True):
        """
        Enable/Disable interface for all non-ROS options
        :param status: flag to enable/disable
        :return: None
        """
        self.ui.gbActiveDevices.setEnabled(status)
        self.ui.gbNearbyDevices.setEnabled(status)
        self.ui.gbFiltering.setEnabled(status)

    def _scan_nearby(self):
        """
        Emit Signal to scan nearby devices, and disable scan button
        :return: None
        """
        self.ui.btnScan.setEnabled(False)
        self._activedevice['locked'] = True
        self._update_active_device_ui()
        self.sigScanDevices.emit(self)

    def _connect_device(self):
        """
        Emit Signal to connect to device
        :return:
        """
        if str(self.ui.btnConnDiscon.text()) == 'Connect':
            self.sigConnectionStatus.emit(0)
            _typ = 0
        else:
            self.sigConnectionStatus.emit(2)
            _typ = 1
        self._update_active_device_ui()
        self.sigConnectDevice.emit(self, self._activedevice['dev'], _typ)

    def lkey_dialog(self):
        """
        Handling of Update Licence Key Button, opens dialog to modify licence
        emits licence_modified signal if licence keys are modified
        :return: None
        """
        dlglic = GaiTechLicenceDialog(lkeys=self._lkeys)
        if dlglic.exec_() == QtGui.QDialog.Accepted and dlglic.isModified():
            self._lkeys = dlglic.getLkeys()
            self.sigLicenceModified.emit(self._lkeys)

    def _fiter_btn_pressed(self, btn):
        """
        Emit Signals with latest value of filter settings when applied or Reset to old values
        :param btn:
        :return:
        """
        if str(btn.text()) == 'Apply':
            # Set Filter Options
            self._filtersettings['high'] = self.ui.dspinHigh.value()
            self._filtersettings['low'] = self.ui.dspinLow.value()
            self._filtersettings['nhigh'] = self.ui.dspinNHigh.value()
            self._filtersettings['nlow'] = self.ui.dspinNLow.value()
            # Emit Signal #
            self.sigFilterModified.emit(self._filtersettings)
        elif str(btn.text()) == 'Reset':
            # Reset Filter Options
            self._update_filter_settings()

    def _test_filter_update_range(self, _newval):
        """
        Update the min max of filter settings
        :param _newval: ignored
        :return: None
        """
        self.ui.dspinLow.setMinimum(self.ui.dspinHigh.value()+0.01)
        self.ui.dspinHigh.setMaximum(self.ui.dspinLow.value()-0.01)
        self.ui.dspinNHigh.setMinimum(self.ui.dspinNLow.value() + 0.01)
        self.ui.dspinNLow.setMaximum(self.ui.dspinNHigh.value() - 0.01)

    def _search_nodes(self):
        """
        Emit Signal to search running nodes for gaitech_bci Node
        :return:
        """
        self.ui.cmbNode.setEnabled(False)
        self.ui.btnNode.setEnabled(False)
        self._enable_All_Interface(False)
        self.sigScanNodes.emit(self)

    def _draw_device_ui(self):
        """
        Draw electrode status on graphics widget
        :return:
        """
        def _givebrush(num):
            brush = QtGui.QBrush(QtCore.Qt.SolidPattern)
            _clr = QtGui.QColor()
            _clr.setHsvF(0.33 * (float(num)/100.0), 1.0, 1.0)
            brush.setColor(_clr)
            return brush

        _drawn = False
        self.scene.clear()
        if self._activedevice['ref'] == 1 and self.__image_be_avg is not None:
            _drawn = True
            self.__image_drawn = self.__image_be_avg
        elif self._activedevice['ref'] == 2 and self.__image_be_lb is not None:
            _drawn = True
            self.__image_drawn = self.__image_be_lb
        elif self._activedevice['ref'] == 3 and self.__image_be_tb is not None:
            _drawn = True
            self.__image_drawn = self.__image_be_tb
        elif self.__image_be_common is not None:
            _drawn = True
            self.__image_drawn = self.__image_be_common
        if _drawn:
            painter = QtGui.QPainter()
            painter.begin(self.__image_drawn)
            # Range is 0 to 100 #
            painter.setBrush(_givebrush(self._electrodestatus['Fp1']))
            painter.drawEllipse(QtCore.QPointF(81, 76), self.__image_circle_size, self.__image_circle_size)   # Fp1
            painter.setBrush(_givebrush(self._electrodestatus['F7']))
            painter.drawEllipse(QtCore.QPointF(81, 296), self.__image_circle_size, self.__image_circle_size)  # F7
            painter.setBrush(_givebrush(self._electrodestatus['T3']))
            painter.drawEllipse(QtCore.QPointF(81, 516), self.__image_circle_size, self.__image_circle_size)  # T3
            painter.setBrush(_givebrush(self._electrodestatus['T5']))
            painter.drawEllipse(QtCore.QPointF(81, 736), self.__image_circle_size, self.__image_circle_size)  # T5
            painter.setBrush(_givebrush(self._electrodestatus['O1']))
            painter.drawEllipse(QtCore.QPointF(81, 956), self.__image_circle_size, self.__image_circle_size)  # O1
            painter.setBrush(_givebrush(self._electrodestatus['Fp2']))
            painter.drawEllipse(QtCore.QPointF(1821, 76), self.__image_circle_size, self.__image_circle_size)  # Fp2
            painter.setBrush(_givebrush(self._electrodestatus['F8']))
            painter.drawEllipse(QtCore.QPointF(1821, 296), self.__image_circle_size, self.__image_circle_size)  # F8
            painter.setBrush(_givebrush(self._electrodestatus['T4']))
            painter.drawEllipse(QtCore.QPointF(1821, 516), self.__image_circle_size, self.__image_circle_size)  # T4
            painter.setBrush(_givebrush(self._electrodestatus['T6']))
            painter.drawEllipse(QtCore.QPointF(1821, 736), self.__image_circle_size, self.__image_circle_size)  # T6
            painter.setBrush(_givebrush(self._electrodestatus['O2']))
            painter.drawEllipse(QtCore.QPointF(1821, 956), self.__image_circle_size, self.__image_circle_size)  # O2
            painter.end()
            self.scene.addPixmap(self.__image_drawn.scaled(self.ui.graphicsView.size()))
            self.scene.update()
            self.ui.graphicsView.setScene(self.scene)

    def _gDispElecResizeEvent(self, event):
        """
        Update Electrode UI on resize
        :param event:
        :return:
        """
        if self.__image_drawn is not None:
            self.scene.clear()
            self.scene.addPixmap(self.__image_drawn.scaled(self.ui.graphicsView.size()))
            self.scene.update()
            self.ui.graphicsView.setScene(self.scene)
        QtGui.QGraphicsView.resizeEvent(self.ui.graphicsView, event)

    def _initialize_ui(self):
        """
        Load Icons and graphics
        :return:
        """
        try:
            self.ui.btnScan.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources','if_bluetooth-searching_326512.png')))
        except:
            print 'Debugging : Unable to load bluetooth-searching icon'
        try:
            self.ui.btnNode.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources','if_sync-01_186384.png')))
        except:
            print 'Debugging : Unable to load bluetooth-searching icon'
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'
        try:
            self.__image_be_common = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                'resources', 'brainelectrode_common.png'))
        except:
            print 'Debugging : Unable to load brainelectrode common background'
            self.__image_be_common = None
        try:
            self.__image_be_avg = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                             'resources', 'brainelectrode_average.png'))
        except:
            print 'Debugging : Unable to load brainelectrode average background'
            self.__image_be_avg = None
        try:
            self.__image_be_lb = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                            'resources', 'brainelectrode_lpolar.png'))
        except:
            print 'Debugging : Unable to load brainelectrode longitudinal background'
            self.__image_be_lb = None
        try:
            self.__image_be_tb = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                            'resources', 'brainelectrode_tpolar.png'))
        except:
            print 'Debugging : Unable to load brainelectrode longitudinal background'
            self.__image_be_tb = None


