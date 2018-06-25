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
H10C UI Side interface class
ROS Node
"""
import rospy, sys, os, rosbag, rosnode
from threading import Thread
from std_srvs.srv import Empty
from std_msgs.msg import Header
from gaitech_bci_bringup.srv import *
from gaitech_bci_bringup.msg import AverageReference, CommonReference, DeviceInfo
from gaitech_bci_bringup.msg import LongitudinalBipolar, TransverseBipolar, EEGEvent


############################################################
################### ROS Interface Class ####################
############################################################
class GaitechROSInterfaceNode():
    """
    Class to interface with gaitech_bci node
    """
    def __init__(self, mwref=None, mwsetting=None, mwlive=None):
        rospy.loginfo('Intializing ROS Interface Node')
        self.mainwindow = mwref
        self.settings = mwsetting
        self.live = mwlive
        self.nodename = None
        self.datasub = None
        self.infosub = None
        self.datastarttime = None
        self.datalivupdtime = None
        self.livepacketbuffer = None
        # Subscribe to Event Messages #
        self.eventsub = rospy.Subscriber('~event', EEGEvent, self._oneventmsg)
        rospy.loginfo('Subsrcibed to %s on %s', self.eventsub.type, self.eventsub.name)
        # Callbacks events and data if live window is None #
        self.callbackevent = None   # Assign function
        self.callbackdata = None    # Assign function
        ##### Connect Callbacks ######
        if self.settings is not None:
            self.settings.sigScanDevices.connect(self._performscan)
            self.settings.sigConnectDevice.connect(self._connectdisconnect)
            self.settings.sigRefModeChange.connect(self._refmodechange)
            self.settings.sigLicenceModified.connect(self._licmodified)
            self.settings.sigFilterModified.connect(self._filtermodified)
            self.settings.sigScanNodes.connect(self._scanNodes)
            self.settings.sigNodeModified.connect(self._nodemodified)
            # Scan at startup #
            self._scanNodes(self.settings)

    def _scanNodes(self, wdgname):
        """
        Scan rosnodes that publishes gaitech messages
        :param wdgname:
        :return:
        """
        def _parallel_func(wdg):
            """
            Search all ros nodes for a node with valid pub types
            :param wdg:
            :return:
            """
            _allndoes = rosnode.get_node_names()
            _nnames = []
            for _nname in _allndoes:
                _pubs, _, _ = GaitechROSInterfaceNode.__getpubsubsrv(_nname)
                _isvalid = False
                for _pub in _pubs:
                    if 'gaitech_bci_bringup/TransverseBipolar' in _pub or 'gaitech_bci_bringup/CommonReference' in _pub or \
                            'gaitech_bci_bringup/AverageReference' in _pub or 'gaitech_bci_bringup/LongitudinalBipolar' in _pub:
                        _isvalid = True
                        break
                if _isvalid:
                    _nnames.append(_nname)
            wdg.sigNodesReceived.emit(_nnames)

        Thread(target=_parallel_func, args=(wdgname,)).start()

    def _nodemodified(self, newnodename):
        """
        On Node change update topics and services dict
        :param newnodename:
        :return:
        """
        if newnodename == '':
            ### Cleanup procedure ###
            if self.infosub is not None:
                self.infosub.unregister()
                self.infosub = None
            if self.datasub is not None:
                self.datasub.unregister()
                self.datasub = None
            self.nodename = None
            return
        if self.nodename is None or self.nodename['name'] != newnodename:
            self.nodename = {'name': newnodename, 'init': True, 'info': None, 'common': None, 'average': None,
                             'lb': None, 'tb': None, 'scan': None, 'connect': None, 'disconnect': None,
                             'slicence': None, 'glicence': None, 'sfilter': None, 'gfilter': None, 'gstatus': None}
            ### Cleanup procedure ###
            if self.infosub is not None:
                self.infosub.unregister()
                self.infosub = None
            if self.datasub is not None:
                self.datasub.unregister()
                self.datasub = None
            ### Update services and other stuff ###
            ### Now set the names to proper values whenever possible ###
            _pubs, _, _srvs = GaitechROSInterfaceNode.__getpubsubsrv(self.nodename['name'])
            for _pub in _pubs:
                _parts = _pub.split()
                if len(_parts) < 3:
                    continue
                if _parts[0] != '*':
                    continue
                if 'gaitech_bci_bringup/TransverseBipolar' in _parts[2]:
                    self.nodename['tb'] = _parts[1]
                elif 'gaitech_bci_bringup/LongitudinalBipolar' in _parts[2]:
                    self.nodename['lb'] = _parts[1]
                elif 'gaitech_bci_bringup/CommonReference' in _parts[2]:
                    self.nodename['common'] = _parts[1]
                elif 'gaitech_bci_bringup/AverageReference' in _parts[2]:
                    self.nodename['average'] = _parts[1]
                elif 'gaitech_bci_bringup/DeviceInfo' in _parts[2]:
                    self.nodename['info'] = _parts[1]
            ######### Now for subscribers ################
            for _srv in _srvs:
                _parts = _srv.split()
                if len(_parts) < 2:
                    continue
                if _parts[0] != '*':
                    continue
                if '/scan' in _parts[1]:
                    self.nodename['scan'] = _parts[1]
                elif '/connect' in _parts[1]:
                    self.nodename['connect'] = _parts[1]
                elif '/disconnect' in _parts[1]:
                    self.nodename['disconnect'] = _parts[1]
                elif '/get_status' in _parts[1]:
                    self.nodename['gstatus'] = _parts[1]
                elif '/get_licence' in _parts[1]:
                    self.nodename['glicence'] = _parts[1]
                elif '/get_filter' in _parts[1]:
                    self.nodename['gfilter'] = _parts[1]
                elif '/set_filter' in _parts[1]:
                    self.nodename['sfilter'] = _parts[1]
                elif '/set_licence' in _parts[1]:
                    self.nodename['slicence'] = _parts[1]
            # Update Licence previously stored #
            #self.__updatelicenceafterget()
            self.__updatefilterafterget()
            self.__updatedevnameafterget()
            ### Finally ###
            self.nodename['init'] = False

    def _performscan(self, wdgname):
        """
        Call rosnode to perfrom scan and return results to gui
        :param wdgname:
        :return:
        """
        def _parallel_func(wdg):
            _sproxy = rospy.ServiceProxy(self.nodename['scan'], DeviceScan)
            _res = _sproxy()
            _devs = []
            for _i in range(len(_res.devices)):
                _devs.append((_res.devices[_i], _res.validity[_i]))
            wdg.sigScanReceived.emit(_devs)

        if self.nodename is not None and not self.nodename['init'] and self.nodename['scan'] is not None:
            Thread(target=_parallel_func, args=(wdgname,)).start()
        else:
            wdgname.sigScanReceived.emit([])

    def _connectdisconnect(self, wdgname, dname, dm):
        """
        Ros connect disconnect with device
        :param wdg:
        :param dname:
        :param dm:
        :return:
        """
        def _def_disconnect(wdg, lv, _dname=None):
            if wdg is not None:
                wdg.sigConnectionStatus.emit(3)
            if lv is not None:
                lv.sigConnectionStatus.emit(3)
                if _dname is not None:
                    lv.sigDeviceStatus.emit('Avertus %s' % _dname)
            if self.mainwindow is not None:
                if _dname is not None:
                    self.mainwindow.setWindowTitle('Gaitech H10C Device : Avertus %s' % _dname)
                else:
                    self.mainwindow.setWindowTitle('Gaitech H10C Device')

        def _def_connect(wdg, lv, _dname, _activemode):
            if wdg is not None:
                wdg.sigConnectionStatus.emit(1)
            if lv is not None:
                lv.sigConnectionStatus.emit(1)
                if _dname is not None:
                    lv.sigDeviceStatus.emit('Avertus %s' % _dname)
                self.__subscibetomode(_activemode)
            if self.mainwindow is not None:
                if _dname is not None:
                    self.mainwindow.setWindowTitle('Gaitech H10C Device : Avertus %s' % _dname)
                else:
                    self.mainwindow.setWindowTitle('Gaitech H10C Device')
            # Subscribe to information messages #
            if self.nodename is not None and not self.nodename['init'] and self.nodename['info'] is not None:
                self.infosub = rospy.Subscriber(self.nodename['info'], DeviceInfo, self._oninfomsg)
                rospy.loginfo('Subscribed to : %s', self.nodename['info'])

        def _parallel_func_connect(wdg, _dev, _lv, _activemode):
            _sproxy = rospy.ServiceProxy(self.nodename['connect'], DeviceConnect)
            _spreq = DeviceConnectRequest()
            _spreq.device = str(_dev)
            _res = _sproxy(_spreq)
            if _res.connected:
                _def_connect(wdg, _lv, _dev, _activemode)
            else:
                _def_disconnect(wdg, _lv, _dev)

        def _parallel_func_disconnect(wdg, _dev, _lv):
            _sproxy = rospy.ServiceProxy(self.nodename['disconnect'], Empty)
            _sproxy()
            _def_disconnect(wdg, _lv)

        # Un-register information messages #
        if self.infosub is not None:
            self.infosub.unregister()
            self.infosub = None
            rospy.loginfo('Un-subscribed from information topic')
        if dname == 'None':
            _def_disconnect(wdgname, self.live)
            return
        if self.nodename is None or self.nodename['init']:
            _def_disconnect(wdgname, self.live)
            return
        if dm == 0:
            if self.nodename['connect'] is not None:
                _activemode = wdgname.getActiveMode()
                Thread(target=_parallel_func_connect, args=(wdgname, dname, self.live, _activemode)).start()
            else:
                _def_disconnect(wdgname, self.live)
        else:
            if self.nodename['disconnect'] is not None:
                Thread(target=_parallel_func_disconnect, args=(wdgname, dname, self.live,)).start()
            else:
                _def_disconnect(wdgname, self.live)

    def _refmodechange(self, newmode):
        """
        On mode change
        :param newmode:
        :return:
        """
        if newmode == 0:
            rospy.loginfo('Reference mode changed to Common Reference')
            if self.nodename['common'] is not None:
                rospy.loginfo('Will subscribe to %s', self.nodename['common'])
        elif newmode == 1:
            rospy.loginfo('Reference mode changed to Average Reference')
            if self.nodename['average'] is not None:
                rospy.loginfo('Will subscribe to %s', self.nodename['average'])
        elif newmode == 2:
            rospy.loginfo('Reference mode changed to Longitudinal-Bipolar')
            if self.nodename['lb'] is not None:
                rospy.loginfo('Will subscribe to %s', self.nodename['lb'])
        elif newmode == 3:
            rospy.loginfo('Reference mode changed to Transverse-Bipolar')
            if self.nodename['tb'] is not None:
                rospy.loginfo('Will subscribe to %s', self.nodename['tb'])
        self.__subscibetomode(newmode)

    def _licmodified(self, _newkeys):
        """
        On licence modified update licence by calling appropriate service
        :param _newkeys:
        :return:
        """
        def _parallel_func():
            _sproxy = rospy.ServiceProxy(self.nodename['slicence'], LicenceUpdate)
            _req = LicenceUpdateRequest()
            _req.licences = _newkeys
            _sproxy(_req)

        if self.nodename is not None and not self.nodename['init'] and self.nodename['slicence'] is not None:
            Thread(target=_parallel_func).start()

    def _filtermodified(self, _newvals):
        """
        On filter updated, call appropriate service
        :param _newvals:
        :return:
        """
        def _parallel_func():
            _sproxy = rospy.ServiceProxy(self.nodename['sfilter'], FilterUpdate)
            _sreq = FilterUpdateRequest()
            _sreq.lowpass = _newvals['low']
            _sreq.highpass = _newvals['high']
            _sreq.notchlow = _newvals['nlow']
            _sreq.notchhigh = _newvals['nhigh']
            _sproxy(_sreq)

        if self.nodename is not None and not self.nodename['init'] and self.nodename['sfilter'] is not None:
            Thread(target=_parallel_func).start()

    ##### Subscribers Callback #####
    def _oncmnmsg(self, msg):
        """
        Callback to Common message, passes data to UI
        :param msg:
        :return:
        """
        if self.datastarttime is None:
            self.datastarttime = msg.header.stamp
        if self.datalivupdtime is None:
            self.datalivupdtime = msg.header.stamp
        if self.live is not None:
            if self.livepacketbuffer is not None and self.livepacketbuffer['mode'] != 'Common Reference':
                self.livepacketbuffer = None    # Reset Live Packet Buffer
            # Build Packet Buffer #
            if self.livepacketbuffer is None:
                self.livepacketbuffer = {'mode': 'Common Reference', 'data': dict(),
                                         'time': [(msg.header.stamp - self.datastarttime).to_sec()]}
                self.livepacketbuffer['data']['Fp1'] = [msg.fp1]
                self.livepacketbuffer['data']['Fp2'] = [msg.fp2]
                self.livepacketbuffer['data']['F7'] = [msg.f7]
                self.livepacketbuffer['data']['F8'] = [msg.f8]
                self.livepacketbuffer['data']['T3'] = [msg.t3]
                self.livepacketbuffer['data']['T4'] = [msg.t4]
                self.livepacketbuffer['data']['T5'] = [msg.t5]
                self.livepacketbuffer['data']['T6'] = [msg.t6]
                self.livepacketbuffer['data']['O1'] = [msg.o1]
                self.livepacketbuffer['data']['O2'] = [msg.o2]
            else:
                self.livepacketbuffer['time'].append((msg.header.stamp - self.datastarttime).to_sec())
                self.livepacketbuffer['data']['Fp1'].append(msg.fp1)
                self.livepacketbuffer['data']['Fp2'].append(msg.fp2)
                self.livepacketbuffer['data']['F7'].append(msg.f7)
                self.livepacketbuffer['data']['F8'].append(msg.f8)
                self.livepacketbuffer['data']['T3'].append(msg.t3)
                self.livepacketbuffer['data']['T4'].append(msg.t4)
                self.livepacketbuffer['data']['T5'].append(msg.t5)
                self.livepacketbuffer['data']['T6'].append(msg.t6)
                self.livepacketbuffer['data']['O1'].append(msg.o1)
                self.livepacketbuffer['data']['O2'].append(msg.o2)
            # Update UI every 100 ms #
            if (msg.header.stamp - self.datalivupdtime).to_sec() > 0.1:
                self.live.sigData.emit(self.livepacketbuffer)
                self.datalivupdtime = msg.header.stamp
                self.livepacketbuffer = None
        elif self.callbackdata is not None:
            data = {'mode': 'Common Reference', 'time': msg.header.stamp,
                    'data': [msg.fp1, msg.fp2, msg.f7, msg.f8, msg.t3, msg.t4, msg.t5, msg.t6, msg.o1, msg.o2]}
            self.callbackdata(data)

    def _onavgmsg(self, msg):
        """
        Callback to Avg Msg, passes data to UI
        :param msg:
        :return:
        """
        if self.datastarttime is None:
            self.datastarttime = msg.header.stamp
        if self.datalivupdtime is None:
            self.datalivupdtime = msg.header.stamp
        if self.live is not None:
            if self.livepacketbuffer is not None and self.livepacketbuffer['mode'] != 'Average Reference':
                self.livepacketbuffer = None    # Reset Live Packet Buffer
            ## Build packet suitable for live #
            if self.livepacketbuffer is None:
                self.livepacketbuffer = {'mode': 'Average Reference',  'data': dict(),
                                         'time': [(msg.header.stamp - self.datastarttime).to_sec()]}
                self.livepacketbuffer['data']['Fp1-Avg'] = [msg.fp1_avg]
                self.livepacketbuffer['data']['Fp2-Avg'] = [msg.fp2_avg]
                self.livepacketbuffer['data']['F7-Avg'] = [msg.f7_avg]
                self.livepacketbuffer['data']['F8-Avg'] = [msg.f8_avg]
                self.livepacketbuffer['data']['T3-Avg'] = [msg.t3_avg]
                self.livepacketbuffer['data']['T4-Avg'] = [msg.t4_avg]
                self.livepacketbuffer['data']['T5-Avg'] = [msg.t5_avg]
                self.livepacketbuffer['data']['T6-Avg'] = [msg.t6_avg]
                self.livepacketbuffer['data']['O1-Avg'] = [msg.o1_avg]
                self.livepacketbuffer['data']['O2-Avg'] = [msg.o2_avg]
            else:
                self.livepacketbuffer['time'].append((msg.header.stamp - self.datastarttime).to_sec())
                self.livepacketbuffer['data']['Fp1-Avg'].append(msg.fp1_avg)
                self.livepacketbuffer['data']['Fp2-Avg'].append(msg.fp2_avg)
                self.livepacketbuffer['data']['F7-Avg'].append(msg.f7_avg)
                self.livepacketbuffer['data']['F8-Avg'].append(msg.f8_avg)
                self.livepacketbuffer['data']['T3-Avg'].append(msg.t3_avg)
                self.livepacketbuffer['data']['T4-Avg'].append(msg.t4_avg)
                self.livepacketbuffer['data']['T5-Avg'].append(msg.t5_avg)
                self.livepacketbuffer['data']['T6-Avg'].append(msg.t6_avg)
                self.livepacketbuffer['data']['O1-Avg'].append(msg.o1_avg)
                self.livepacketbuffer['data']['O2-Avg'].append(msg.o2_avg)
            # Update UI every 100 ms #
            if (msg.header.stamp - self.datalivupdtime).to_sec() > 0.1:
                self.live.sigData.emit(self.livepacketbuffer)
                self.datalivupdtime = msg.header.stamp
                self.livepacketbuffer = None
        elif self.callbackdata is not None:
            data = {'mode': 'Average Reference', 'time': msg.header.stamp,
                    'data': [msg.fp1_avg, msg.fp2_avg, msg.f7_avg, msg.f8_avg, msg.t3_avg, msg.t4_avg, msg.t5_avg,
                             msg.t6_avg, msg.o1_avg, msg.o2_avg]}
            self.callbackdata(data)

    def _onlbmsb(self, msg):
        """
        Call back to LB Message, passes data to UI
        :param msg:
        :return:
        """
        if self.datastarttime is None:
            self.datastarttime = msg.header.stamp
        if self.datalivupdtime is None:
            self.datalivupdtime = msg.header.stamp
        if self.live is not None:
            if self.livepacketbuffer is not None and self.livepacketbuffer['mode'] != 'Longitudinal-Bipolar':
                self.livepacketbuffer = None    # Reset Live Packet Buffer
            ## Build packet suitable for live #
            if self.livepacketbuffer is None:
                self.livepacketbuffer = {'mode': 'Longitudinal-Bipolar',  'data': dict(),
                                         'time': [(msg.header.stamp - self.datastarttime).to_sec()]}
                self.livepacketbuffer['data']['Fp1-F7'] = [msg.fp1_fp7]
                self.livepacketbuffer['data']['F7-T3'] = [msg.f7_t3]
                self.livepacketbuffer['data']['T3-T5'] = [msg.t3_t5]
                self.livepacketbuffer['data']['T5-O1'] = [msg.t5_o1]
                self.livepacketbuffer['data']['Fp2-F8'] = [msg.fp2_f8]
                self.livepacketbuffer['data']['F8-T4'] = [msg.f8_t4]
                self.livepacketbuffer['data']['T4-T6'] = [msg.t4_t6]
                self.livepacketbuffer['data']['T6-O2'] = [msg.t6_o2]
            else:
                self.livepacketbuffer['time'].append((msg.header.stamp - self.datastarttime).to_sec())
                self.livepacketbuffer['data']['Fp1-F7'].append(msg.fp1_fp7)
                self.livepacketbuffer['data']['F7-T3'].append(msg.f7_t3)
                self.livepacketbuffer['data']['T3-T5'].append(msg.t3_t5)
                self.livepacketbuffer['data']['T5-O1'].append(msg.t5_o1)
                self.livepacketbuffer['data']['Fp2-F8'].append(msg.fp2_f8)
                self.livepacketbuffer['data']['F8-T4'].append(msg.f8_t4)
                self.livepacketbuffer['data']['T4-T6'].append(msg.t4_t6)
                self.livepacketbuffer['data']['T6-O2'].append(msg.t6_o2)
            # Update UI every 100 ms #
            if (msg.header.stamp - self.datalivupdtime).to_sec() > 0.1:
                self.live.sigData.emit(self.livepacketbuffer)
                self.datalivupdtime = msg.header.stamp
                self.livepacketbuffer = None
        elif self.callbackdata is not None:
            data = {'mode': 'Longitudinal-Bipolar', 'time': msg.header.stamp,
                    'data': [msg.fp1_fp7, msg.f7_t3, msg.t3_t5, msg.t5_o1, msg.fp2_f8, msg.f8_t4, msg.t4_t6, msg.t6_o2]}
            self.callbackdata(data)

    def _ontbmsg(self, msg):
        """
        Call back to TB Message, passes data to UI
        :param msg:
        :return:
        """
        if self.datastarttime is None:
            self.datastarttime = msg.header.stamp
        if self.datalivupdtime is None:
            self.datalivupdtime = msg.header.stamp
        if self.live is not None:
            if self.livepacketbuffer is not None and self.livepacketbuffer['mode'] != 'Transverse-Bipolar':
                self.livepacketbuffer = None    # Reset Live Packet Buffer
            ## Build packet suitable for live #
            if self.livepacketbuffer is None:
                self.livepacketbuffer = {'mode': 'Transverse-Bipolar',  'data': dict(),
                                         'time': [(msg.header.stamp - self.datastarttime).to_sec()]}
                self.livepacketbuffer['data']['Fp1-Fp2'] = [msg.fp1_fp2]
                self.livepacketbuffer['data']['F7-F8'] = [msg.f7_f8]
                self.livepacketbuffer['data']['T3-T4'] = [msg.t3_t4]
                self.livepacketbuffer['data']['T5-T6'] = [msg.t5_t6]
                self.livepacketbuffer['data']['O1-O2'] = [msg.o1_o2]
            else:
                self.livepacketbuffer['time'].append((msg.header.stamp - self.datastarttime).to_sec())
                self.livepacketbuffer['data']['Fp1-Fp2'].append(msg.fp1_fp2)
                self.livepacketbuffer['data']['F7-F8'].append(msg.f7_f8)
                self.livepacketbuffer['data']['T3-T4'].append(msg.t3_t4)
                self.livepacketbuffer['data']['T5-T6'].append(msg.t5_t6)
                self.livepacketbuffer['data']['O1-O2'].append(msg.o1_o2)
            # Update UI every 100 ms #
            if (msg.header.stamp - self.datalivupdtime).to_sec() > 0.1:
                self.live.sigData.emit(self.livepacketbuffer)
                self.datalivupdtime = msg.header.stamp
                self.livepacketbuffer = None
        elif self.callbackdata is not None:
            data = {'mode': 'Transverse-Bipolar', 'time': msg.header.stamp,
                    'data': [msg.fp1_fp2, msg.f7_f8, msg.t3_t4, msg.t5_t6, msg.o1_o2]}
            self.callbackdata(data)

    def _oninfomsg(self, msg):
        """
        Information messages update loss, connection status etc
        :param msg:
        :return:
        """
        if self.nodename is not None and not self.nodename['init'] and msg.device_name != '':
            if msg.device_connected:
                # Update losses #
                if self.live is not None:
                    self.live.sigConnectiviyStatus.emit(msg.loss, 0.0)
                    self.live.sigConnectionStatus.emit(1)
                if self.settings is not None:
                    self.settings.sigConnectivityStatus.emit(msg.loss * 100.0, 0.0)
                    # Update electrode information #
                    _elecinfo = {'Fp1': msg.fp1, 'Fp2': msg.fp2, 'F7': msg.f7, 'F8': msg.f8, 'T3': msg.t3,
                                 'T4': msg.t4, 'T5': msg.t5, 'T6': msg.t6, 'O1': msg.o1, 'O2': msg.o2}
                    self.settings.sigElectrodeUpdated.emit(_elecinfo)
            else:
                if self.settings is not None and self.settings.getActiveDevice() == msg.device_name:
                    self.settings.sigConnectionStatus.emit(3)
                    # Detected disconnect #
                    if self.live is not None:
                        self.live.sigConnectionStatus.emit(3)

    def _oneventmsg(self, msg):
        """
        Call back to EEGEvent Message, passes data to UI
        :param msg:
        :return:
        """
        if self.live is not None and self.datastarttime is not None:
            _marker = (msg.event_id, (msg.header.stamp - self.datastarttime).to_sec(),
                       msg.event_status, msg.event_remark)
            _M = [_marker]
            self.live.sigMarker.emit(_M)
        elif self.live is None and self.callbackevent is not None:
            self.callbackevent(msg)

    def uieventmsg(self, evnt):
        """
        Event messages from UI
        :param evnt:
        :return:
        """
        if self.live is not None and self.datastarttime is not None:
            _marker = (evnt[0], (rospy.Time.now() - self.datastarttime).to_sec(), evnt[1], evnt[2])
            _M = [_marker]
            self.live.sigMarker.emit(_M)
        elif self.live is None and self.callbackevent is not None:
            msg = EEGEvent()
            msg.header.stamp = rospy.Time.now()
            msg.event_id = evnt[0]
            msg.event_remark = evnt[2]
            msg.event_status = evnt[1]
            self.callbackevent(msg)

    ####### Helping Functions ######
    def __subscibetomode(self, mode, forced=False):
        """
        Subscribe to data for mode
        :param mode:
        :return:
        """
        if self.live is not None:
            self.live.sigMode.emit(mode)    # Would flush data
        if self.datasub is not None:
            self.datasub.unregister()
            self.datasub = None
        self.datastarttime = None
        self.datalivupdtime = None
        self.livepacketbuffer = None        # Discard old buffer
        if self.nodename is not None and ((not self.nodename['init']) or forced):
            if mode == 0 and self.nodename['common'] is not None:
                self.datasub = rospy.Subscriber(self.nodename['common'], CommonReference, self._oncmnmsg)
                rospy.loginfo('Subsrcibed to %s', self.nodename['common'])
            elif mode == 1 and self.nodename['average'] is not None:
                self.datasub = rospy.Subscriber(self.nodename['average'], AverageReference, self._onavgmsg)
                rospy.loginfo('Subscribed to %s', self.nodename['average'])
            elif mode == 2 and self.nodename['lb'] is not None:
                self.datasub = rospy.Subscriber(self.nodename['lb'], LongitudinalBipolar, self._onlbmsb)
                rospy.loginfo('Subscribed to %s', self.nodename['lb'])
            elif mode == 3 and self.nodename['tb'] is not None:
                self.datasub = rospy.Subscriber(self.nodename['tb'], TransverseBipolar, self._ontbmsg)
                rospy.loginfo('Subscribed to %s', self.nodename['tb'])

    def __updatelicenceafterget(self):
        """
        Call service to update licence information
        :return:
        """
        if self.nodename is not None and self.nodename['glicence'] is not None:
            _sproxy = rospy.ServiceProxy(self.nodename['glicence'], LicenceInfo)
            _res = _sproxy()
            _lkeys = _res.licences
            if self.settings is not None:
                self.settings.sigLicenceUpdated.emit(_lkeys)

    def __updatefilterafterget(self):
        """
        Call service to update filter paramters from node
        :return:
        """
        if self.nodename is not None and self.nodename['gfilter'] is not None:
            _sproxy = rospy.ServiceProxy(self.nodename['gfilter'], FilterInfo)
            _res = _sproxy()
            if self.settings is not None:
                self.settings.sigFilterUpdated.emit([_res.highpass, _res.lowpass, _res.notchlow, _res.notchhigh])

    def __updatedevnameafterget(self):
        """
        Call service to get status of connected device
        :return:
        """
        if self.nodename is not None and self.nodename['gstatus'] is not None:
            _sproxy = rospy.ServiceProxy(self.nodename['gstatus'], DeviceStatus)
            _res = _sproxy()
            if _res.device != '' and _res.connected:
                if self.mainwindow is not None:
                    self.mainwindow.setWindowTitle('Gaitech H10C Device : Avertus %s' % _res.device)
                # Already connected to some device #
                if self.settings is not None:
                    self.settings.sigDeviceInitialize.emit(_res.device)
                    self.settings.sigConnectionStatus.emit(1)
                if self.live is not None:
                    self.live.sigConnectionStatus.emit(1)
                    self.live.sigDeviceStatus.emit('Avertus %s' % _res.device)
                if self.settings is not None:
                    self.__subscibetomode(self.settings.getActiveMode(), forced=True)
                if self.nodename is not None and self.nodename['info'] is not None:
                    if self.infosub is not None:
                        self.infosub.unregister()
                        self.infosub = None
                    self.infosub = rospy.Subscriber(self.nodename['info'], DeviceInfo, self._oninfomsg)
                    rospy.loginfo('Subscribed to : %s', self.nodename['info'])

    @staticmethod
    def __getpubsubsrv(_nodename):
        """
        Get Pub, Subs and Srvs of ROS Node
        :param _nodename:
        :return:
        """
        try:
            _desc = rosnode.get_node_info_description(_nodename)
        except:
            _desc = ''
        _publines = []
        _sublines = []
        _serlines = []
        _swtch = 0
        for _line in _desc.splitlines():
            if len(_line) > 0:
                if 'Publications' in _line:
                    _swtch = 1
                elif 'Subscriptions' in _line:
                    _swtch = 2
                elif 'Services' in _line:
                    _swtch = 3
                else:
                    if _swtch == 1:
                        _publines.append(str(_line))
                    elif _swtch == 2:
                        _sublines.append(str(_line))
                    elif _swtch == 3:
                        _serlines.append(str(_line))
        return _publines, _sublines, _serlines


#################################
### Helping Functions ###########
#################################
def LoadEEGDataFromBagFile(wdg, _fname):
    """
    Loads Data from Bag file
    :param wdg: Data Viewer Widget or None
    :param _fname: Path of rosbag to load from
    :return: None (if wdg is not None) else returns Data
    """
    def _parallel_func(_wdg, _fn):
        with rosbag.Bag(_fn, 'r') as _bag:
            try:
                rospy.get_rostime()
                rospy.loginfo('Loading data from %s', _fn)
            except rospy.ROSInitException as e:
                print 'Loading data from %s' % _fn
            _msgtypes = _bag.get_type_and_topic_info()[0].keys()
            _isvalid = False
            _hasevent = False
            _mode = -1
            _bagdata = {'mode': '', 'time': [], 'data': dict(), 'markers': []}
            for _msgtyp in _msgtypes:
                if 'gaitech_bci_bringup/EEGEvent' in _msgtyp:
                    _hasevent = True
                if 'gaitech_bci_bringup/TransverseBipolar' in _msgtyp:
                    _mode = 3
                    _bagdata['mode'] = 'Transverse-Bipolar'
                    _bagdata['data'] = {'Fp1-Fp2': [], 'F7-F8': [], 'T3-T4': [], 'T5-T6': [], 'O1-O2': []}
                    _isvalid = True
                if 'gaitech_bci_bringup/LongitudinalBipolar' in _msgtyp:
                    _mode = 2
                    _bagdata['mode'] = 'Longitudinal-Bipolar'
                    _bagdata['data'] = {'Fp1-F7': [], 'F7-T3': [], 'T3-T5': [], 'T5-O1': [], 'Fp2-F8': [],
                                        'F8-T4': [], 'T4-T6': [], 'T6-O2': []}
                    _isvalid = True
                if 'gaitech_bci_bringup/AverageReference' in _msgtyp:
                    _mode = 1
                    _bagdata['mode'] = 'Average Reference'
                    _bagdata['data'] = {'Fp1-Avg': [], 'Fp2-Avg': [], 'F7-Avg': [], 'F8-Avg': [], 'T3-Avg': [],
                                        'T4-Avg': [], 'T5-Avg': [], 'T6-Avg': [], 'O1-Avg': [], 'O2-Avg': []}
                    _isvalid = True
                if 'gaitech_bci_bringup/CommonReference' in _msgtyp:
                    _mode = 0
                    _bagdata['mode'] = 'Common Reference'
                    _bagdata['data'] = {'Fp1': [], 'Fp2': [], 'F7': [], 'F8': [], 'T3': [], 'T4': [],
                                        'T5': [], 'T6': [], 'O1': [], 'O2': []}
                    _isvalid = True
            if _isvalid and _mode != -1:
                # Only load if valid
                # Take topic name based on mode
                _topicdata = None
                _topicevent = None
                for _k, _v in _bag.get_type_and_topic_info()[1].items():
                    if _mode == 0 and 'gaitech_bci_bringup/CommonReference' in _v[0]:
                        _topicdata = _k
                        break
                    if _mode == 1 and 'gaitech_bci_bringup/AverageReference' in _v[0]:
                        _topicdata = _k
                        break
                    if _mode == 2 and 'gaitech_bci_bringup/LongitudinalBipolar' in _v[0]:
                        _topicdata = _k
                        break
                    if _mode == 3 and 'gaitech_bci_bringup/TransverseBipolar' in _v[0]:
                        _topicdata = _k
                        break
                if _hasevent:
                    for _k, _v in _bag.get_type_and_topic_info()[1].items():
                        if 'gaitech_bci_bringup/EEGEvent' in _v[0]:
                            _topicevent = _k
                            break
                if _topicdata is not None:
                    _init_time = rospy.Time(_bag.get_start_time())
                    for _, _msg, _ in _bag.read_messages(topics=[_topicdata]):
                        _tm = (_msg.header.stamp - _init_time).to_sec()
                        if _mode == 0:
                            _bagdata['time'].append(_tm)
                            _bagdata['data']['Fp1'].append(_msg.fp1)
                            _bagdata['data']['Fp2'].append(_msg.fp2)
                            _bagdata['data']['F7'].append(_msg.f7)
                            _bagdata['data']['F8'].append(_msg.f8)
                            _bagdata['data']['T3'].append(_msg.t3)
                            _bagdata['data']['T4'].append(_msg.t4)
                            _bagdata['data']['T5'].append(_msg.t5)
                            _bagdata['data']['T6'].append(_msg.t6)
                            _bagdata['data']['O1'].append(_msg.o1)
                            _bagdata['data']['O2'].append(_msg.o2)
                        elif _mode == 1:
                            _bagdata['time'].append(_tm)
                            _bagdata['data']['Fp1-Avg'].append(_msg.fp1_avg)
                            _bagdata['data']['Fp2-Avg'].append(_msg.fp2_avg)
                            _bagdata['data']['F7-Avg'].append(_msg.f7_avg)
                            _bagdata['data']['F8-Avg'].append(_msg.f8_avg)
                            _bagdata['data']['T3-Avg'].append(_msg.t3_avg)
                            _bagdata['data']['T4-Avg'].append(_msg.t4_avg)
                            _bagdata['data']['T5-Avg'].append(_msg.t5_avg)
                            _bagdata['data']['T6-Avg'].append(_msg.t6_avg)
                            _bagdata['data']['O1-Avg'].append(_msg.o1_avg)
                            _bagdata['data']['O2-Avg'].append(_msg.o2_avg)
                        elif _mode == 2:
                            _bagdata['time'].append(_tm)
                            _bagdata['data']['Fp1-F7'].append(_msg.fp1_fp7)
                            _bagdata['data']['F7-T3'].append(_msg.f7_t3)
                            _bagdata['data']['T3-T5'].append(_msg.t3_t5)
                            _bagdata['data']['T5-O1'].append(_msg.t5_o1)
                            _bagdata['data']['Fp2-F8'].append(_msg.fp2_f8)
                            _bagdata['data']['F8-T4'].append(_msg.f8_t4)
                            _bagdata['data']['T4-T6'].append(_msg.t4_t6)
                            _bagdata['data']['T6-O2'].append(_msg.t6_o2)
                        elif _mode == 3:
                            _bagdata['time'].append(_tm)
                            _bagdata['data']['Fp1-Fp2'].append(_msg.fp1_fp2)
                            _bagdata['data']['F7-F8'].append(_msg.f7_f8)
                            _bagdata['data']['T3-T4'].append(_msg.t3_t4)
                            _bagdata['data']['T5-T6'].append(_msg.t5_t6)
                            _bagdata['data']['O1-O2'].append(_msg.o1_o2)
                    # Load Markers #
                    if _topicevent is not None:
                        for _, _msg, _ in _bag.read_messages(topics=[_topicevent]):
                            _tm = (_msg.header.stamp - _init_time).to_sec()
                            _bagdata['markers'].append((_msg.event_id, _tm, _msg.event_status, _msg.event_remark))
                    # All okay emit signal to load data in ui #
                    # Fix for time 0
                    if (len(_bagdata['time']) > 0) and _bagdata['time'][0] < 0:
                        _bagdata['time'][0] = 0.0
                    try:
                        rospy.get_rostime()
                        rospy.loginfo('Loaded data from %s', _fn)
                    except rospy.ROSInitException as e:
                        print 'Loaded data from %s' % _fn
                    if _wdg is not None:
                        _wdg.sigLoadData.emit(_bagdata, os.path.basename(unicode(_fn)))
                        return None
                    else:
                        return _bagdata

    if wdg is None:
        return _parallel_func(None, _fname)
    else:
        Thread(target=_parallel_func, args=(wdg, _fname)).start()
        return None


def SaveEEGDataToBagFile(wdg, _DATA, _fn):
    """
    Save to Bag File
    :param wdg: Data Viewer Widget or None
    :param _data: Data to Save
    :param _fname: File to Save
    :return: None
    """
    import time

    def _parallel_func(_wdg, _data, _fname):
        try:
            rospy.get_rostime()
            rospy.loginfo('Saving data to %s', _fname)
        except rospy.ROSInitException as e:
            print 'Saving data to %s' % _fname
        with rosbag.Bag(_fname, 'w') as _bag:
            _inittim = rospy.Time(time.time()) - rospy.Time(_data['time'][-1])
            if _data['mode'] == 'Common Reference':
                for _i in range(len(_data['time'])):
                    _msg = CommonReference()
                    _msg.header.seq = _i+1
                    _msg.header.stamp = _inittim + rospy.Time(_data['time'][_i])
                    _msg.fp1 = _data['data']['Fp1'][_i]
                    _msg.fp2 = _data['data']['Fp2'][_i]
                    _msg.f7 = _data['data']['F7'][_i]
                    _msg.f8 = _data['data']['F8'][_i]
                    _msg.t3 = _data['data']['T3'][_i]
                    _msg.t4 = _data['data']['T4'][_i]
                    _msg.t5 = _data['data']['T5'][_i]
                    _msg.t6 = _data['data']['T6'][_i]
                    _msg.o1 = _data['data']['O1'][_i]
                    _msg.o2 = _data['data']['O2'][_i]
                    _bag.write('/saved_data/data_comref', _msg, _msg.header.stamp)
            elif _data['mode'] == 'Average Reference':
                for _i in range(len(_data['time'])):
                    _msg = AverageReference()
                    _msg.header.seq = _i + 1
                    _msg.header.stamp = _inittim + rospy.Time(_data['time'][_i])
                    _msg.fp1_avg = _data['data']['Fp1-Avg'][_i]
                    _msg.fp2_avg = _data['data']['Fp2-Avg'][_i]
                    _msg.f7_avg = _data['data']['F7-Avg'][_i]
                    _msg.f8_avg = _data['data']['F8-Avg'][_i]
                    _msg.t3_avg = _data['data']['T3-Avg'][_i]
                    _msg.t4_avg = _data['data']['T4-Avg'][_i]
                    _msg.t5_avg = _data['data']['T5-Avg'][_i]
                    _msg.t6_avg = _data['data']['T6-Avg'][_i]
                    _msg.o1_avg = _data['data']['O1-Avg'][_i]
                    _msg.o2_avg = _data['data']['O2-Avg'][_i]
                    _bag.write('/saved_data/data_avgref', _msg, _msg.header.stamp)
            elif _data['mode'] == 'Longitudinal-Bipolar':
                for _i in range(len(_data['time'])):
                    _msg = LongitudinalBipolar()
                    _msg.header.seq = _i + 1
                    _msg.header.stamp = _inittim + rospy.Time(_data['time'][_i])
                    _msg.fp1_fp7 = _data['data']['Fp1-F7'][_i]
                    _msg.f7_t3 = _data['data']['F7-T3'][_i]
                    _msg.t3_t5 = _data['data']['T3-T5'][_i]
                    _msg.t5_o1 = _data['data']['T5-O1'][_i]
                    _msg.fp2_f8 = _data['data']['Fp2-F8'][_i]
                    _msg.f8_t4 = _data['data']['F8-T4'][_i]
                    _msg.t4_t6 = _data['data']['T4-T6'][_i]
                    _msg.t6_o2 = _data['data']['T6-O2'][_i]
                    _bag.write('/saved_data/data_lb', _msg, _msg.header.stamp)
            elif _data['mode'] == 'Transverse-Bipolar':
                for _i in range(len(_data['time'])):
                    _msg = TransverseBipolar()
                    _msg.header.seq = _i + 1
                    _msg.header.stamp = _inittim + rospy.Time(_data['time'][_i])
                    _msg.fp1_fp2 = _data['data']['Fp1-Fp2'][_i]
                    _msg.f7_f8 = _data['data']['F7-F8'][_i]
                    _msg.t3_t4 = _data['data']['T3-T4'][_i]
                    _msg.t5_t6 = _data['data']['T5-T6'][_i]
                    _msg.o1_o2 = _data['data']['O1-O2'][_i]
                    _bag.write('/saved_data/data_tb', _msg, _msg.header.stamp)
            else:
                print 'Data Type Unknown cannot save!'
            # Save Markers #
            _mi = 1
            for _mrks in _data['markers']:
                _msg = EEGEvent()
                _msg.header.seq = _mi + 1
                _msg.header.stamp = _inittim + rospy.Time(_mrks[1])
                _msg.event_id = _mrks[0]
                _msg.event_status = _mrks[2]
                _msg.event_remark = _mrks[3]
                _bag.write('/saved_data/event', _msg, _msg.header.stamp)
                _mi += 1
            try:
                rospy.get_rostime()
                rospy.loginfo('Saved data to %s', _fname)
            except rospy.ROSInitException as e:
                print 'Saved data to %s' % _fname
            if _wdg is not None:
                _wdg.sigSaveDone.emit(os.path.basename(unicode(_fname)))
            return None

    if wdg is None:
        return _parallel_func(None, _DATA, _fn)
    else:
        Thread(target=_parallel_func, args=(wdg, _DATA, _fn)).start()
        return None
