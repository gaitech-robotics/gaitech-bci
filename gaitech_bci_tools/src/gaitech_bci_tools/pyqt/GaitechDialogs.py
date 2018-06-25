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
Dialogs related to user-interface
"""

import sys, os, copy, time , string
from PyQt4 import QtCore, QtGui
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'interface'))
from LicenceDialog import Ui_GaitechLicenceDlg
from DataMarkerDialog import Ui_DataMarkerDialog
from AboutGaitechDialog import Ui_AboutGaitechDialog


####### Dialog Licence Viewer/Add/Remove #######
class GaiTechLicenceDialog(QtGui.QDialog):
    def __init__(self, parent=None, lkeys=[]):
        super(GaiTechLicenceDialog,self).__init__( parent)
        self.ui = Ui_GaitechLicenceDlg()
        self.ui.setupUi(self)
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'
        ##### Initialize stuff #####
        self._lkeys = lkeys
        self._initalkeys = copy.deepcopy(lkeys)
        ### Update Initial Display ###
        self._updateLKeyDisplay()

    def getLkeys(self):
        return self._lkeys

    def isModified(self):
        if len(self._lkeys) != len(self._initalkeys):
            return True
        for _t1, _t2 in zip(self._lkeys, self._initalkeys):
            if _t1 != _t2:
                return True
        return False

    def _updateLKeyDisplay(self):
        self.ui.tblLic.clearContents()
        self.ui.tblLic.clear()
        self.ui.tblLic.setRowCount(len(self._lkeys)+1)
        for _rn, _key in zip(range(len(self._lkeys)), self._lkeys):
            lbl = QtGui.QTableWidgetItem(_key)
            lbl.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
            lbl.setToolTip('Double click to edit this licence key')
            self.ui.tblLic.setItem(_rn, 0, lbl)
            btn = QtGui.QToolButton()
            btn.setText('-')
            btn.setStyleSheet("QToolButton{color:'red';font:20pt;}")
            btn.setToolTip('Remove this licence key')
            btn.KeyIndex = _rn          # To keep track of which key to remove
            btn.clicked.connect(self._remove_row)
            self.ui.tblLic.setCellWidget(_rn,1, btn)
        try:
            # Qt4/ Qt5 difference
            _header = self.ui.tblLic.horizontalHeader()
            _header.setResizeMode(0, QtGui.QHeaderView.Stretch)
            _header.setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
        except:
            # Qt4/ Qt5 difference
            _header = self.table.horizontalHeader()
            _header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            _header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        ######### Add New Key Button #######
        btn = QtGui.QToolButton()
        btn.setText('Add New Key')
        btn.setStyleSheet("QToolButton{color:'green';font:16pt;}")
        btn.setToolTip('Add new licence key')
        btn.clicked.connect(self._add_new_key)
        lblEmpty = QtGui.QLabel()
        self.ui.tblLic.setCellWidget(self.ui.tblLic.rowCount()-1, 0, btn)
        self.ui.tblLic.setCellWidget(self.ui.tblLic.rowCount() - 1, 1, lblEmpty)

    def _remove_row(self):
        try:
            _keytorem = self.sender().KeyIndex
            if _keytorem < len(self._lkeys):
                self._resync_keys()
                self._lkeys.pop(_keytorem)
                self._updateLKeyDisplay()
        except:
            pass

    def _add_new_key(self):
        self._resync_keys()
        self._lkeys.append('<Enter Licence Key>')
        self._updateLKeyDisplay()

    def _resync_keys(self):
        _status = -1
        if len(self._lkeys) == self.ui.tblLic.rowCount()-1:
            for _i in range(self.ui.tblLic.rowCount()-1):
                _txt = str(self.ui.tblLic.item(_i, 0).text())
                if len(_txt) != 32:
                    _status = _i
                if not all(c in string.hexdigits for c in _txt):
                    _status = _i
                self._lkeys[_i] = _txt.upper()
        return _status

    def accept(self):
        _sts = self._resync_keys()
        if _sts == -1:
            QtGui.QDialog.accept(self)
        else:
            QtGui.QMessageBox.critical(self, 'Invalid Licence', "Licence %s is incorrect" % self._lkeys[_sts])

    def reject(self):
        self._resync_keys()
        QtGui.QDialog.reject(self)


###### Dialog Data Marker Editor ################
class GaiTechDataMakerDialog(QtGui.QDialog):
    def __init__(self, parent=None, data={'marker':'2332532532', 'time': 0.0,
                                          'event':'Test Event', 'remark':''}, markerlist=[]):
        super(GaiTechDataMakerDialog, self).__init__(parent)
        self.ui = Ui_DataMarkerDialog()
        self.ui.setupUi(self)
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'
        ##### Initialize Stuff #####
        self._data = data
        self._origdata = copy.deepcopy(data)
        self._markerlist = copy.deepcopy(markerlist)
        if self._data['marker'] in self._markerlist:
            self._markerlist.remove(self._data['marker'])
        self._updateUIData()
        ##### Connect Signals #######
        self.ui.leMarker.editingFinished.connect(self._markermod)
        self.ui.leEvent.editingFinished.connect(self._leventmod)
        self.ui.pteRemarks.textChanged.connect(self._remmod)

    def _updateUIData(self):
        self.ui.leMarker.setText(self._data['marker'])
        self.ui.leTime.setText(str(self._data['time']) + ' seconds')
        self.ui.leEvent.setText(self._data['event'])
        self.ui.pteRemarks.setPlainText(self._data['remark'])

    def _leventmod(self):
        if self._data['event'] != str(self.ui.leEvent.text()):
            self._data['event'] = str(self.ui.leEvent.text())

    def _remmod(self):
        self._data['remark'] = str(self.ui.pteRemarks.toPlainText())

    def _markermod(self):
        if self._data['marker'] != str(self.ui.leMarker.text()):
            _temptxt = str(self.ui.leMarker.text())
            if _temptxt in self._markerlist:
                # Cannot Set because marker already present
                self.ui.leMarker.setText(self._origdata['marker'])
            else:
                self._data['marker'] = str(self.ui.leMarker.text())

    def isModified(self):
        if self._data['marker'] != self._origdata['marker']:
            return True
        if self._data['event'] != self._origdata['event']:
            return True
        if self._data['remark'] != self._origdata['remark']:
            return True
        return False

    def getData(self):
        return self._data


############### About Dialog #####################
class GaitechAboutDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(GaitechAboutDialog, self).__init__(parent)
        self.ui = Ui_AboutGaitechDialog()
        self.ui.setupUi(self)
        self.setWindowTitle('About Gaitech')
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
            _pmap = QtGui.QPixmap(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                               'resources', 'gaitech_logo.png')).scaledToHeight(128)
            self.ui.label.setPixmap(_pmap)
        except:
            print 'Debugging: Unable to load gaitech icon'


