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
Widget to build user experiments for video
"""
import sys, os, time, cv2, datetime
import numpy as np
from threading import Thread
from xml.dom import minidom
from PyQt4 import QtCore, QtGui
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'interface'))
from VideoExperimentBuilder import Ui_VideoExperimentBuilder
from VideoExperiment import Ui_VideoExperiment
from GaitechDialogs import GaiTechDataMakerDialog
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


############################################
######### Gstreamre video fetch ############
############################################
class GstVideoFile(QtCore.QObject):
    """
    Class to play video file along with audio
    """
    sigNewFrame = QtCore.pyqtSignal(np.ndarray, float, float) # signal eimitted on new frame and its video time

    def __init__(self, _fname, noaudio=True):
        """
        Initialize video class
        """
        super(GstVideoFile, self).__init__(None)
        ## Initialize gstreamer ##
        Gst.init(None)
        ## Data Members ##
        self.done = False
        self.image = None
        self.playmode = False
        self.player = None
        self.sink = None
        self.fakesink = None
        self.bus = None
        ## Check if video can be played ##
        _sts, _frames, _fps = self._canplay(_fname)
        if not _sts:
            raise(IOError('Video can not be played'))
        ## Create Pipeline ##
        self.player = Gst.ElementFactory.make('playbin', 'player')
        if noaudio:
            self.fakesink = Gst.ElementFactory.make("fakesink", "fakesink")
            self.player.set_property('audio-sink', self.fakesink)
        self.sink = Gst.ElementFactory.make('appsink', 'sink')
        self.player.set_property('uri', 'file://' + _fname)
        self.player.set_property('video-sink', self.sink)
        ## Test Eelements ##
        if noaudio:
            if not self.player or not self.fakesink or not self.sink:
                raise (SystemError('Gstreamer elements could not be created'))
        else:
            if not self.player or not self.sink:
                raise (SystemError('Gstreamer elements could not be created'))
        ##
        self.sink.set_property('emit_signals', True)
        caps = Gst.caps_from_string("video/x-raw, format=(string){BGR, GRAY8};"
                                    " video/x-bayer,format=(string){rggb,bggr,grbg,gbrg}")
        self.sink.set_property("caps", caps)
        self.sink.connect("new-sample", self._new_buffer, self.sink)
        self.bus = self.player.get_bus()
        ## Go to paused state ##
        self.player.set_state(Gst.State.PAUSED)

    def __del__(self):
        if self.player:
            self.player.set_state(Gst.State.NULL)

    def play(self):
        """
        Play Video
        :return:
        """
        self.playmode = True
        self.player.set_state(Gst.State.PLAYING)
        while self.playmode:
            time.sleep(0.01)
            message = self.bus.timed_pop_filtered(10000, Gst.MessageType.ANY)
            if message:
                self.on_message(self.bus, message)
        self.player.set_state(Gst.State.PAUSED)

    def pause(self):
        """
        Pause Video
        :return:
        """
        self.playmode = False
        if not self.done:
            self.player.set_state(Gst.State.PAUSED)
        else:
            self.player.set_state(Gst.State.NULL)

    def stop(self):
        """
        Stop Video
        :return:
        """
        self.pause()
        if not self.done:
            self.player.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE, 0.0 * Gst.SECOND)

    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self.player.set_state(Gst.State.NULL)
            self.playmode = False
            self.done = True
        elif t == Gst.MessageType.ERROR:
            self.player.set_state(Gst.State.NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.playmode = False

    def _gst_to_nparray(self, sample):
        _buffer = sample.get_buffer()
        _caps = sample.get_caps()
        _arr = np.ndarray((_caps.get_structure(0).get_value('height'),
                          _caps.get_structure(0).get_value('width'), 3),
                          buffer=_buffer.extract_dup(0, _buffer.get_size()),
                          dtype=np.uint8)
        return _arr

    def _new_buffer(self, sink, data):
        _sample = sink.emit('pull-sample')
        _arr = self._gst_to_nparray(_sample)
        _, current = self.sink.query_position(Gst.Format.TIME)
        _, total = self.sink.query_duration(Gst.Format.TIME)
        pos_sec = float(current) / Gst.SECOND
        tot_sec = float(total) / Gst.SECOND
        self.image = _arr
        self.sigNewFrame.emit(self.image, pos_sec, tot_sec)
        return Gst.FlowReturn.OK

    def _canplay(self, _vidname):
        """
        Check if video can be played
        :param _vidname:
        :return:
        """
        try:
            _tobj = cv2.VideoCapture(_vidname)
            if _tobj.isOpened():
                _ret, _ = _tobj.read()
                if _ret:
                    try:
                        _length = int(_tobj.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
                    except AttributeError as e:
                        _length = int(_tobj.get(cv2.CAP_PROP_FRAME_COUNT))
                    try:
                        _fps = _tobj.get(cv2.cv.CV_CAP_PROP_FPS)
                    except:
                        _fps = _tobj.get(cv2.CAP_PROP_FPS)
                    if _length > 0 and _fps > 0:
                        return True, _length, _fps
        except:
            return False, 0, 0
        return False, 0, 0


############################################
#### Video Experiment Builder Class ########
############################################
class GaitechVideoExperimentBuilder(QtGui.QWidget):
    """
    QtWidget for video experiment builder
    """
    sigPlayFrame = QtCore.pyqtSignal(np.ndarray)    # Signal emitted when new frame loaded for realtime play

    def __init__(self, parent=None):
        """
        Initialize object of GaitechVideoExperimentBuilder
        :param parent:
        """
        super(GaitechVideoExperimentBuilder, self).__init__(parent)
        self.ui = Ui_VideoExperimentBuilder()
        self.ui.setupUi(self)
        ## Initialize other data ##
        self.markers = []
        self.videoname = None
        self.videoobj = None
        self.totalframes = None
        self.currentframe = -1
        self.totaltime = None
        self.imgdisplayed = None
        self.videoplaying = False
        self.__lastsavedir = ""
        self.scene = QtGui.QGraphicsScene(None)
        ## Initialize UI ##
        self.ui.sliderMovie.setEnabled(False)   # Switch off at start #
        self._loadicons()
        self._changePlayPause(True)
        self._connectcallbacks()
        self._loadeventstable()
        if self.videoname is None:
            self.ui.tbAddMarker.setEnabled(False)
            self.ui.tbPlayPause.setEnabled(False)
            self.ui.tbStop.setEnabled(False)
            self.ui.sliderMovie.setEnabled(False)

    def __del__(self):
        """
        On object destruction
        :return:
        """
        self.videoplaying = False

    def closeEvent(self, evnt):
        """
        When closing widget stop video playing
        :param evnt:
        :return:
        """
        self._onstop()
        evnt.accept()

    def _convert2xml(self):
        """
        Convert experiment to xml format for saving
        :return:
        """
        _doc = minidom.Document()
        _root = _doc.createElement('BCIExperiment')
        _doc.appendChild(_doc.createComment('Auto-generated using Gaitech Video Experiment Builder on %s' %
                                            str(datetime.datetime.now())))
        _exptype = _doc.createElement('type')
        _exptype.appendChild(_doc.createTextNode('video'))
        _root.appendChild(_exptype)
        if self.videoname is not None and self.totalframes is not None and self.totaltime is not None:
            _videonode = _doc.createElement('video')
            _videonode.setAttribute('path', unicode(self.videoname))
            _videonode.setAttribute('time', str(self.totaltime))
            _videonode.setAttribute('frames', str(self.totalframes))
            ## Add all markers ##
            for _mrk in self.markers:
                _marker = _doc.createElement('marker')
                _tm = _doc.createElement('time')
                _tm.appendChild(_doc.createTextNode(str(_mrk[1])))
                _ev = _doc.createElement('event')
                _ev.appendChild(_doc.createTextNode(str(_mrk[2])))
                _rm = _doc.createElement('remark')
                _rm.appendChild(_doc.createTextNode(str(_mrk[3])))
                _marker.appendChild(_tm)
                _marker.appendChild(_ev)
                _marker.appendChild(_rm)
                _videonode.appendChild(_marker)
            #####################
            _root.appendChild(_videonode)
        _doc.appendChild(_root)
        return _doc

    @staticmethod
    def xml2data(_fname):
        """
        Parse experiment file
        :param _fname: path to video experiment file
        :return: videofilename, markers
        """
        try:
            mydoc = minidom.parse(_fname)
        except IOError as e:
            print 'File : %s reading error (%s)' % (_fname, str(e))
            return None, None
        except:
            e = sys.exc_info()[0]
            print 'Error Parsing : %s' % e
            return None, None
        ## Check if experiment ##
        if mydoc.documentElement.tagName.lower() != 'BCIExperiment'.lower():
            print 'Not an experiment'
            return None, None
        _typ = mydoc.getElementsByTagName('type')
        if len(_typ) == 0 or len(_typ) > 1:
            print 'Document have no type'
            return None, None
        _etype = _typ[0].firstChild.nodeValue
        if _etype.lower() != 'video'.lower():
            print 'Experiment not of video type'
            return None, None
        ## Check if the experiment has a video ##
        _vid = mydoc.getElementsByTagName('video')
        if len(_vid) == 0:
            print 'Experiment has no video data'
            return None, None
        _vid = _vid[0]
        if _vid.hasAttribute('path'):
            _path = unicode(_vid.getAttribute('path'))
        else:
            _path = None
        _allevents = _vid.getElementsByTagName('marker')
        _markers = []
        for _evnt in _allevents:
            _tm = _evnt.getElementsByTagName('time')
            _txtE = ''
            _txtR = ''
            if len(_tm) > 0:
                _txtT = _tm[0].firstChild.nodeValue
                try:
                    _tnum = float(_txtT)
                except ValueError:
                    continue
            else:
                continue
            _ev = _evnt.getElementsByTagName('event')
            if len(_ev) > 0:
                _txtE = str(_ev[0].firstChild.nodeValue)
            _rm = _evnt.getElementsByTagName('remark')
            if len(_rm) > 0:
                _txtR = str(_rm[0].firstChild.nodeValue)
            _mrk = ('marker_xxx', _tnum, _txtE, _txtR)
            _markers.append(_mrk)
        return _path, _markers

    ## UI Related Stuff ##
    def _loadeventstable(self):
        """
        Load events in the table so that user can view and edit
        :return:
        """
        self.ui.tblEvents.clearContents()
        if len(self.markers) > 0:
            self.ui.tblEvents.setRowCount(len(self.markers))
            for _i in range(len(self.markers)):
                _row = self.markers[_i]
                self.ui.tblEvents.setItem(_i, 0, QtGui.QTableWidgetItem("%.3f" % _row[1]))
                self.ui.tblEvents.setItem(_i, 1, QtGui.QTableWidgetItem('%s' % _row[2]))
                self.ui.tblEvents.item(_i, 1).setToolTip('%s' % _row[2])
                # Add Buttons #
                _btnedit = QtGui.QToolButton()
                if self.__iconedit is not None:
                    _btnedit.setIcon(self.__iconedit)
                else:
                    _btnedit.setText('E')
                _btnrem = QtGui.QToolButton()
                if self.__iconremove is not None:
                    _btnrem.setIcon(self.__iconremove)
                else:
                    _btnrem.setText('R')
                _btntime = QtGui.QToolButton()
                if self.__iconplace is not None:
                    _btntime.setIcon(self.__iconplace)
                else:
                    _btntime.setText('P')
                _btnedit.setFixedSize(32, 32)
                _btnrem.setFixedSize(32, 32)
                _btntime.setFixedSize(32, 32)
                _btnedit.setToolTip('Edit this event')
                _btnrem.setToolTip('Remove this event')
                _btntime.setToolTip('Set time to current frame displayed')
                _btnedit.event_row = _i
                _btnrem.event_row = _i
                _btntime.event_row = _i
                _btnedit.clicked.connect(self._edit_event)
                _btnrem.clicked.connect(self._remove_event)
                _btntime.clicked.connect(self._change_event)
                _lyt = QtGui.QHBoxLayout()
                _lyt.setContentsMargins(0, 0, 0, 0)
                _lyt.addWidget(_btnedit)
                _lyt.addWidget(_btntime)
                _lyt.addWidget(_btnrem)
                _lyt.setSizeConstraint(QtGui.QBoxLayout.SetFixedSize)
                _cwdg = QtGui.QWidget()
                _cwdg.setLayout(_lyt)
                self.ui.tblEvents.setCellWidget(_i, 2, _cwdg)
        else:
            self.ui.tblEvents.setRowCount(0)
        # Adjust Contents #
        self.ui.tblEvents.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.ui.tblEvents.resizeColumnToContents(0)
        self.ui.tblEvents.resizeColumnToContents(2)

    def _edit_event(self):
        """
        Edit Event
        :return:
        """
        _rowtoedit = self.sender().event_row
        if _rowtoedit < 0 or _rowtoedit >= len(self.markers):
            return
        _marker_data = {'marker': self.markers[_rowtoedit][0], 'time': self.markers[_rowtoedit][1],
                        'event': self.markers[_rowtoedit][2], 'remark': self.markers[_rowtoedit][3]}
        _dlgmarker = GaiTechDataMakerDialog(markerlist=[], data=_marker_data)
        _oldval = self.videoplaying
        self.videoplaying = False
        self._changePlayPause(True)
        if _dlgmarker.exec_() == QtGui.QDialog.Accepted and _dlgmarker.isModified():
            _dmrkmod = _dlgmarker.getData()
            self.markers[_rowtoedit] = (_dmrkmod['marker'], _dmrkmod['time'],
                                                 _dmrkmod['event'], _dmrkmod['remark'])
            # Update On Table
            self.ui.tblEvents.item(_rowtoedit, 1).setText('%s' % _dmrkmod['event'])
            self.ui.tblEvents.item(_rowtoedit, 1).setToolTip('%s' % _dmrkmod['event'])
        if _oldval:
            self._onplaypause()

    def _remove_event(self):
        """
        Remove Event from table
        :return:
        """
        _rowtorem = self.sender().event_row
        try:
            self.markers.pop(_rowtorem)
        except:
            print 'Debugging : Error on Event Removal, Fix it if it shows'
        self._loadeventstable()

    def _change_event(self):
        """
        Change the event time to the current time of video frame being displayed
        :return:
        """
        _rowtoedit = self.sender().event_row
        if _rowtoedit < 0 or _rowtoedit >= len(self.markers):
            return
        if self.currentframe != -1 and self.totalframes is not None and self.totaltime is not None:
            _timeinsec = (float(self.currentframe + 1) / float(self.totalframes)) * self.totaltime
            _mrk = (self.markers[_rowtoedit][0], _timeinsec, self.markers[_rowtoedit][2], self.markers[_rowtoedit][3])
            self.markers[_rowtoedit] = _mrk
            self.ui.tblEvents.setItem(_rowtoedit, 0, QtGui.QTableWidgetItem("%.3f" % _mrk[1]))

    ## Callbacks ##
    def _onsaveexperiment(self):
        """
        Save Experiment to disk after getting name of file to save to
        :return:
        """
        if self.videoname is None or self.totaltime is None or self.totalframes is None:
            return
        if self.videoplaying:
            self.videoplaying = False
            self._changePlayPause(True)
        _fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save Experiment', self.__lastsavedir,
                                                      selectedFilter='*.experiment')
        if _fileName:
            _bname = os.path.basename(unicode(_fileName))
            _dir = os.path.dirname(unicode(_fileName))
            _fnamesext = _bname.split('.')
            self.__lastsavedir = _dir
            if (len(_fnamesext) > 1 and _fnamesext[-1] != 'experiment') or (len(_fnamesext) == 1):
                _bname = '%s.experiment' % _bname
                _fname = os.path.join(_dir, _bname)
            else:
                _fname = unicode(_fileName)
            ###### Save Data to _fname ######
            _doc = self._convert2xml()
            with open(_fname, 'w') as _f:
                _doc.writexml(_f, indent="  ", addindent="  ", newl='\n')

    def _onloadexperminet(self):
        """
        Load *.experiment file
        :return:
        """
        # Clear things #
        if self.videoplaying:
            self.videoplaying = False
            self._changePlayPause(True)
        # Open Dialog #
        dlg = QtGui.QFileDialog()
        dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
        dlg.setFilter("BCI Experiment (*.experiment)")
        if dlg.exec_():
            _fname = unicode(dlg.selectedFiles()[0])
            _dir = os.path.dirname(unicode(_fname))
            self.__lastsavedir = _dir
            # Clear display, events, etc.
            self._cleardisplay()
            self.ui.tblEvents.clearContents()
            self.markers = []
            self.videoname = None
            self.totalframes = None
            self.totaltime = None
            self.videoobj = None
            self.currentframe = -1
            self.ui.sliderMovie.setMinimum(0)
            self.ui.sliderMovie.setMaximum(1)
            self._displayTime()
            # Open Experiment File #
            _vname, _markers = GaitechVideoExperimentBuilder.xml2data(_fname)
            if _vname is None and _markers is None:
                # Some Error Occurred #
                QtGui.QMessageBox.critical(self, 'Parsing Error', "Error parsing %s" %_fname)
                return
            if _markers is not None:
                self.markers = _markers
                self._loadeventstable()
            if _vname is not None:
                self._openvideofile(_vname)

    def _onopenvideo(self):
        """
        Open Video for the experiment by choosing from open file dialog
        :return:
        """
        if self.videoplaying:
            self.videoplaying = False
            self._changePlayPause(True)
        dlg = QtGui.QFileDialog()
        dlg.setFileMode(QtGui.QFileDialog.ExistingFile)
        dlg.setFilter("Video Files (*.avi || *.mp4 || *.wmv) ;; AVI (*.avi) ;; MP4 (*.mp4) ;;"
                      " Windows Media Files (*.wmv) ;; All Files (*.*)")
        if dlg.exec_():
            _vidname = unicode(dlg.selectedFiles()[0])
            self._openvideofile(_vidname)

    def _onplaypause(self):
        """
        Play pause video
        :return:
        """
        if self.videoname is None or self.totalframes is None or self.totaltime is None:
            return
        if self.videoplaying:
            self.videoplaying = False
            self._changePlayPause(True)
        else:
            # Play video #
            self.videoplaying = True
            self._changePlayPause(False)
            Thread(target=self._playvideo).start()

    def _onstop(self):
        """
        Stops the video currently playing
        :return:
        """
        self.videoplaying = False
        self._changePlayPause(True)
        if self.videoname is not None and self.totalframes is not None and self.totaltime is not None:
            self.ui.sliderMovie.setValue(0)
            _frame = self._loadframeno(0)
            if _frame is not None:
                self._displayimage(_frame)

    def _onaddevent(self):
        """
        Add new marker and updated table
        :return:
        """
        if self.currentframe != -1 and self.totalframes is not None and self.totaltime is not None:
            _timeinsec = (float(self.currentframe + 1) / float(self.totalframes)) * self.totaltime
            _mrk = ('marker_xxx', _timeinsec, 'Video Activity', 'Detail')
            self.ui.tblEvents.clearContents()
            self.markers.append(_mrk)
            self.markers.sort(key=lambda x: x[1])
            self._loadeventstable()

    ## Video Related Stuff ##
    def _openvideofile(self, _filename):
        """
        Open Video File
        :param _filename: Absolute path of video file to open
        :return:
        """
        _sts, _frames, _fps = self._canplayvideo(_filename)
        if _sts:
            if self.videoplaying:
                self._onstop()  # Force video to pause first
            self.totalframes = _frames
            self.videoname = _filename
            self.totaltime = float(self.totalframes) / float(_fps)
            self.currentframe = -1
            self.videoobj = None
            # Setup Other Things
            self._changePlayPause(True)
            self.ui.tbAddMarker.setEnabled(True)
            self.ui.tbPlayPause.setEnabled(True)
            self.ui.tbStop.setEnabled(True)
            self.ui.sliderMovie.setEnabled(True)
            self.ui.sliderMovie.setMinimum(0)
            self.ui.sliderMovie.setMaximum(self.totalframes - 1)
            self.ui.sliderMovie.setValue(0)
            _frame = self._loadframeno(0)
            if _frame is not None:
                self._displayimage(_frame)
            else:
                self._displayTime()
        else:
            if self.videoplaying:
                self._onstop()  # Force video to pause first
            self.videoname = None
            self.totalframes = None
            self.totaltime = None
            self.videoobj = None
            self.currentframe = -1
            # Reset Other Stuff #
            self._cleardisplay()
            self._displayTime()
            self._changePlayPause(True)
            self.ui.tbAddMarker.setEnabled(False)
            self.ui.tbPlayPause.setEnabled(False)
            self.ui.tbStop.setEnabled(False)
            self.ui.sliderMovie.setEnabled(False)
            self.ui.sliderMovie.setMinimum(0)
            self.ui.sliderMovie.setMaximum(1)
            # Display Error #
            QtGui.QMessageBox.critical(self, 'Cannot load video file', "Can't play %s" % _filename)

    def _canplayvideo(self, _vidname):
        """
        :param _vidname: absolute path to video file
        :return: True or False depending upon if file can be opened and played
        """
        try:
            _tobj = cv2.VideoCapture(_vidname)
            if _tobj.isOpened():
                _ret, _ = _tobj.read()
                if _ret:
                    try:
                        _length = int(_tobj.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT))
                    except AttributeError as e:
                        _length = int(_tobj.get(cv2.CAP_PROP_FRAME_COUNT))
                    try:
                        _fps = _tobj.get(cv2.cv.CV_CAP_PROP_FPS)
                    except:
                        _fps = _tobj.get(cv2.CAP_PROP_FPS)
                    if _length > 0 and _fps > 0:
                        return True, _length, _fps
        except:
            return False, 0, 0
        return False, 0, 0

    def _loadframeno(self, _fnum):
        """
        Loads frame number from video and return it
        :param _fnum:
        :return:
        """
        if self.videoname is None or self.totalframes is None:
            return None
        if _fnum >= self.totalframes:
            return None
        if _fnum < 0:
            return None
        try:
            if self.videoobj is None:
                self.videoobj = cv2.VideoCapture(self.videoname)
            try:
                self.videoobj.set(cv2.cv.CV_CAP_PROP_POS_FRAMES, _fnum)  # OPNCV 2.4
            except AttributeError as e:
                self.videoobj.set(cv2.CAP_PROP_POS_FRAMES, _fnum) # OPENCV 3.X
            ### Read frame ##
            _ret, _frame = self.videoobj.read()
            if _ret:
                self.currentframe = _fnum
                return _frame
            else:
                return None
        except:
            return None

    def _playvideo(self):
        """
        Play video depending as close as possible to real time
        :return:
        """
        if self.videoname is None or self.totalframes is None or self.totaltime is None:
            return
        if self.videoobj is None:
            self.videoobj = cv2.VideoCapture(self.videoname)
        _ret = True
        _fps = float(self.totalframes) / self.totaltime
        _delay = 1.0 / _fps
        while _ret and self.videoplaying:
            _ret, _image = self.videoobj.read()
            if _ret:
                self.currentframe += 1
                self.sigPlayFrame.emit(_image)
                time.sleep(_delay)
        self.videoplaying = False
        self._changePlayPause(True)

    def _onsliderdragged(self, _newpos):
        """
        Callback to slider drag events
        :param _newpos: new frame to display
        :return:
        """
        self.videoplaying = False
        self._changePlayPause(True)
        if self.videoname is not None and self.totalframes is not None and self.totaltime is not None:
            self.ui.sliderMovie.setValue(_newpos)
            _frame = self._loadframeno(_newpos)
            if _frame is not None:
                self._displayimage(_frame)

    def _oneventtableclicked(self, _row, _col):
        """
        Change display to show the event frame on video
        :param _row: event at this row
        :param _col:
        :return:
        """
        if _row < 0 or _row >= len(self.markers):
            return
        if self.videoname is None or self.totalframes is None or self.totaltime is None:
            return
        _framenum = int((self.markers[_row][1] / self.totaltime) * float(self.totalframes))
        if _framenum < 0 or _framenum >= self.totalframes:
            return
        self.videoplaying = False
        self._changePlayPause(True)
        _frame = self._loadframeno(_framenum)
        if _frame is not None:
            self._displayimage(_frame)

    @QtCore.pyqtSlot(np.ndarray)
    def _displayimage(self, _img):
        """
        Display image that we get from opencv read operation and display it in UI
        :param _img:
        :return:
        """
        _image = cv2.cvtColor(_img, cv2.COLOR_BGR2RGB)
        _height, _width = _image.shape[:2]
        if _height > 0 and _width > 0:
            self.imgdisplayed = None
            self.scene.clear()
            _frame = QtGui.QImage(_image.data, _width, _height, QtGui.QImage.Format_RGB888)
            self.scene.addPixmap(QtGui.QPixmap.fromImage(_frame).scaled(self.ui.gVideo.size()))
            self.scene.update()
            self.ui.gVideo.setScene(self.scene)
            self.imgdisplayed = _img
            if self.currentframe != -1 and (self.currentframe >= self.ui.sliderMovie.minimum()) and\
                    (self.currentframe <= self.ui.sliderMovie.maximum()):
                self._displayTime()
                if self.ui.sliderMovie.value() != self.currentframe:
                    self.ui.sliderMovie.setValue(self.currentframe)

    def _gVideoResizeEvent(self, event):
        """
        Hooked function to update displayed image on resize
        :param event:
        :return:
        """
        if self.imgdisplayed is not None:
            self._displayimage(self.imgdisplayed)
        QtGui.QGraphicsView.resizeEvent(self.ui.gVideo, event)

    def _cleardisplay(self):
        """
        Clears display
        :return:
        """
        self.imgdisplayed = None
        self.scene.clear()

    def _changePlayPause(self, _play):
        """
        Change play pause icon
        :param _play:
        :return:
        """
        if _play:
            if self.__iconplay is not None:
                self.ui.tbPlayPause.setIcon(self.__iconplay)
            self.ui.tbPlayPause.setToolTip('Play')
        else:
            if self.__iconpause is not None:
                self.ui.tbPlayPause.setIcon(self.__iconpause)
            self.ui.tbPlayPause.setToolTip('Pause')

    def _displayTime(self):
        """
        Update UI to show current time
        :return:
        """
        if self.videoname is None or self.totalframes is None or self.totaltime is None or self.currentframe == -1:
            self.ui.lblTime.setText("")
            self.ui.lblETA.setText("")
        else:
            _timeinsec = (float(self.currentframe+1) / float(self.totalframes)) * self.totaltime
            _timeeta = self.totaltime - _timeinsec
            _min, _sec = divmod(int(_timeinsec), 60)
            _hour, _min = divmod(_min, 60)
            _txttime = '%02d:%02d:%02d' % (_hour, _min, _sec)
            self.ui.lblTime.setText(_txttime)
            _min, _sec = divmod(int(_timeeta), 60)
            _hour, _min = divmod(_min, 60)
            _txttime = '-%02d:%02d:%02d' % (_hour, _min, _sec)
            self.ui.lblETA.setText(_txttime)

    ### UI Init Related Stuff ##
    def _connectcallbacks(self):
        """
        Connect callbacks to different UI events
        :return:
        """
        self.ui.pbtnSave.clicked.connect(self._onsaveexperiment)
        self.ui.pbtnEdit.clicked.connect(self._onloadexperminet)
        self.ui.pbtnOpen.clicked.connect(self._onopenvideo)
        self.ui.tbPlayPause.clicked.connect(self._onplaypause)
        self.ui.tbStop.clicked.connect(self._onstop)
        self.ui.tbAddMarker.clicked.connect(self._onaddevent)
        self.ui.sliderMovie.sliderMoved.connect(self._onsliderdragged)
        self.ui.tblEvents.cellClicked.connect(self._oneventtableclicked)
        self.sigPlayFrame.connect(self._displayimage)
        self.ui.gVideo.resizeEvent = self._gVideoResizeEvent  # Hook resize event

    def _loadicons(self):
        """
        Load icons from file and display them in UI
        :return:
        """
        try:
            self.__iconplay = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface', 'resources',
                                                       'if_player_play_377.png'))
        except:
            print 'Debugging : Unable to load play icon'
            self.__iconplay = None
        try:
            self.__iconpause = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface', 'resources',
                                                        'if_player_pause_376.png'))
        except:
            print 'Debugging : Unable to load pause icon'
            self.__iconpause = None
        try:
            self.__iconremove = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                         'resources', 'if_fileclose_320.png'))
        except:
            print 'Unable to load remove icon'
            self.__iconremove = None
        try:
            self.__iconedit = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                       'resources', 'if_comment_edit_40745.png'))
        except:
            print 'Unable to load edit event icon'
            self.__iconedit = None
        try:
            self.__iconplace = QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..',
                                                        'interface', 'resources',
                                                        'if_Gps_location_pin_map_navigation_place_1886996.png'))
        except:
            print 'Unable to load edit event icon'
            self.__iconplace = None
        try:
            self.ui.tbStop.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface', 'resources',
                                                            'if_player_stop_380.png')))
        except:
            print 'Debugging : Unable to load stop icon'
        try:
            self.ui.tbAddMarker.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                                 'resources', 'if_add_290.png')))
        except:
            print 'Debugging : Unable to load add icon'
        try:
            self.ui.pbtnOpen.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                              'resources', 'if_icon-58-document-upload_314515.png')))
        except:
            print 'Debugging : Unable to load add icon'
        try:
            self.ui.pbtnEdit.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                              'resources', 'if_icon-136-document-edit_314503.png')))
        except:
            print 'Debugging : Unable to load add icon'
        try:
            self.ui.pbtnSave.setIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                              'resources', 'if_filesave_326.png')))
        except:
            print 'Debugging : Unable to load add icon'
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'


############################################
##### Video Experiment Player ##############
############################################
class GaitechVideoExperimentPlayer(QtGui.QWidget):
    """
    QtWidget for video experiment builder
    """
    _sigGenImage = QtCore.pyqtSignal(np.ndarray, float, float) # For displaying countdown
    sigExperimentStarted = QtCore.pyqtSignal()          # Signals Emitted on Start
    sigExperimentCancelled = QtCore.pyqtSignal()        # Signals Emitted on Cancel
    sigExperimentDone = QtCore.pyqtSignal()             # Signal Emitted on Done
    sigExperimentMarker = QtCore.pyqtSignal(tuple)      # Signal Emitted on marker

    def __init__(self, experiment):
        """
        Initialize Experiment Player
        :param _expfile:
        """
        super(GaitechVideoExperimentPlayer, self).__init__(None)
        self.ui = Ui_VideoExperiment()
        self.ui.setupUi(self)
        try:
            self.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', 'interface',
                                                        'resources', 'gaitech_logo.png')))
        except:
            print 'Debugging: Unable to load gaitech icon'
        ##
        self.midtoemit = 1
        self.exitthread = False
        self.initokay = False
        self.imgdisplayed = None
        self.scene = QtGui.QGraphicsScene(None)
        # Open Experiment File #
        self.expname = os.path.basename(experiment)
        self.vidname, self.markers = GaitechVideoExperimentBuilder.xml2data(experiment)
        if self.vidname is None and self.markers is None:
            # Some Error Occurred #
            QtGui.QMessageBox.critical(self, 'Parsing Error', "Error parsing %s" % experiment)
            return
        if self.vidname is None:
            QtGui.QMessageBox.critical(self, 'Video Error', 'No Video file present')
            return
        if self.markers is None:
            self.markers = []  # Will not publish any user message
        self.videvents = []
        for i in range(len(self.markers)):
            self.videvents.append(False)
        #########################
        self.keyPressEvent = self._on_space_esc
        self.ui.gVideo.resizeEvent = self._gVideoResizeEvent  # Hook resize event
        ## Ready up player ##
        try:
            self.gstobj = GstVideoFile(self.vidname, False)
        except (SystemError, IOError) as e:
            QtGui.QMessageBox.critical(self, 'Initializing error', str(e))
            return
        self.gstobj.sigNewFrame.connect(self._displayimage)
        self._sigGenImage.connect(self._displayimage)
        self.sigExperimentDone.connect(self._closewidget)
        ## All okay get ready to play ##
        self.paused = False
        self.initokay = True

    def __del__(self):
        """
        On application quit
        :return:
        """
        self.exitthread = True

    def _closewidget(self):
        """
        Close widget
        :return:
        """
        self.close()

    def closeEvent(self, evnt):
        """
        When closing widget stop video playing
        :param evnt:
        :return:
        """
        self.gstobj.stop()
        self.exitthread = True
        evnt.accept()

    def startExperiment(self):
        """
        Start Experiment
        :return:
        """
        def _shownum(num):
            _img = np.zeros((640, 480, 3), dtype=np.uint8)
            _textsize = cv2.getTextSize(str(num), cv2.FONT_HERSHEY_TRIPLEX, 10.0, 5)[0]
            _textX = (_img.shape[1] - _textsize[0]) / 2
            _textY = (_img.shape[0] + _textsize[1]) / 2
            cv2.putText(_img, str(num), (_textX, _textY), cv2.FONT_HERSHEY_TRIPLEX, 10.0, (160, 160, 160), 5)
            return _img

        def _pauseblock():
            while self.paused and not self.exitthread:
                time.sleep(1.0)

        def _bgfunc():
            self._sigGenImage.emit(_shownum(5), -1.0, -1.0)
            time.sleep(1.0)
            _pauseblock()
            if self.exitthread:
                return
            self._sigGenImage.emit(_shownum(4), -1.0, -1.0)
            time.sleep(1.0)
            _pauseblock()
            if self.exitthread:
                return
            self._sigGenImage.emit(_shownum(3), -1.0, -1.0)
            time.sleep(1.0)
            _pauseblock()
            if self.exitthread:
                return
            self._sigGenImage.emit(_shownum(2), -1.0, -1.0)
            time.sleep(1.0)
            _pauseblock()
            if self.exitthread:
                return
            self._sigGenImage.emit(_shownum(1), -1.0, -1.0)
            time.sleep(1.0)
            _pauseblock()
            if self.exitthread:
                return
            self._sigGenImage.emit(_shownum(0), -1.0, -1.0)
            ######## Now Play ##########
            startedonce = False
            started = False
            while not self.exitthread:
                if self.gstobj.done:
                    # Video Completed execution #
                    self.sigExperimentMarker.emit(('videxp_%06d' % self.midtoemit, 'Video Finished', ''))
                    self.midtoemit += 1
                    self.sigExperimentDone.emit()
                    break
                if self.paused and started:
                    self.gstobj.pause()
                    started = False
                elif not self.paused and not started:
                    Thread(target=self.gstobj.play).start()
                    if not startedonce:
                        self.sigExperimentMarker.emit(('videxp_%06d' % self.midtoemit, 'Video Started',
                                                       '<Experiment>%s</Experiment>'%self.expname))
                        self.midtoemit += 1
                        self.sigExperimentStarted.emit()
                    started = True
                    startedonce = True
                time.sleep(0.2)

        self.show()     # Workaround to grab keyboard events
        self.hide()     # Workaround to grab keyborad events
        self.show()     # Workaround to grab keyborad events
        #self.showFullScreen()
        self.grabKeyboard()
        Thread(target=_bgfunc).start()

    def _checkandemit(self, curtime):
        """
        Check and emit signals for passed markers
        :param curtime:
        :return:
        """
        _idx = None
        for _i in range(len(self.videvents)):
            if not self.videvents[_i]:
                _idx = _i
                break
        if _idx is not None and curtime >= self.markers[_idx][1]:
            self.sigExperimentMarker.emit(('videxp_%06d'%self.midtoemit, self.markers[_idx][2], self.markers[_idx][3]))
            self.midtoemit += 1
            self.videvents[_idx] = True

    @QtCore.pyqtSlot(QtGui.QKeyEvent)
    def _on_space_esc(self, event):
        """
        Handle ESC Key to exit from full screen and pause to pause
        :param event:
        :return:
        """
        if event.key() == QtCore.Qt.Key_Space:
            if self.paused:
                self.paused = False
                self.sigExperimentMarker.emit(('videxp_%06d'%self.midtoemit, 'User UnPaused', ''))
                self.midtoemit += 1
            else:
                self.paused = True
                self.sigExperimentMarker.emit(('videxp_%06d' % self.midtoemit, 'User Paused', ''))
                if self.imgdisplayed is not None:
                    self._displayimage(self.imgdisplayed, -1.0, -1.0)
                self.midtoemit += 1
            event.accept()
        elif event.key() == QtCore.Qt.Key_Escape:
            self.sigExperimentCancelled.emit()
            self.close()
            event.accept()
        else:
            event.ignore()

    def _cleardisplay(self):
        """
        Clears display
        :return:
        """
        self.imgdisplayed = None
        self.scene.clear()

    @QtCore.pyqtSlot(np.ndarray, float, float)
    def _displayimage(self, _img, _curtime, _tottime):
        """
        Display image that we get from opencv read operation and display it in UI
        :param _img:
        :return:
        """
        _image = cv2.cvtColor(_img, cv2.COLOR_BGR2RGB)
        _height, _width = _image.shape[:2]
        if _height > 0 and _width > 0:
            if self.paused:
                # Draw paused text over top #
                _textsize = cv2.getTextSize('PAUSED', cv2.FONT_HERSHEY_TRIPLEX, 2.0, 5)[0]
                _textX = (_image.shape[1] - _textsize[0]) / 2
                _textY = (_image.shape[0] + _textsize[1]) / 2
                cv2.putText(_image, 'PAUSED', (_textX, _textY), cv2.FONT_HERSHEY_TRIPLEX, 2.0, (250, 90, 90), 5)
            self.imgdisplayed = None
            self.scene.clear()
            _frame = QtGui.QImage(_image.data, _width, _height, QtGui.QImage.Format_RGB888)
            self.scene.addPixmap(QtGui.QPixmap.fromImage(_frame).scaled(self.ui.gVideo.size()))
            self.scene.update()
            self.ui.gVideo.setScene(self.scene)
            self.imgdisplayed = _img
            if _curtime >= 0 and _tottime > 0:
                # Emit Marker Signal if ready to #
                self._checkandemit(_curtime)
                self.ui.progressBar.setValue((_curtime / _tottime) * 100.0)

    def _gVideoResizeEvent(self, event):
        """
        Hooked function to update displayed image on resize
        :param event:
        :return:
        """
        if self.imgdisplayed is not None:
            self._displayimage(self.imgdisplayed, -1.0, -1.0)
        QtGui.QGraphicsView.resizeEvent(self.ui.gVideo, event)


