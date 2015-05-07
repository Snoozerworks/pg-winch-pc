#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 20:42:16 2013

@author: Markus
"""

import sys
from PyQt4 import uic
from PyQt4 import QtCore, QtGui

#from AppUI import Ui_MainWindow
from connection.con_winch import ConWinch   

from arduino.package import Parameter, Sample


import dataLog as log
import os
import fnmatch
from TimePlot import TimePlot, PlotSignals


LOG_LENGTH 	 = 100  # Max samples in log stack
GRAPH_LEN 	 = 50  # Max samples to show in graph	



# Run connection in separate thread
bt = ConWinch("00:06:66:43:11:8D")


class _WorkerThread(QtCore.QThread):
	sig_connect 	 = QtCore.pyqtSignal()
	sig_disconnect 	 = QtCore.pyqtSignal()
	sig_sample  	 = QtCore.pyqtSignal()
	sig_stop	  	 = QtCore.pyqtSignal()
	sig_up		  	 = QtCore.pyqtSignal()
	sig_down	  	 = QtCore.pyqtSignal()
	sig_select  	 = QtCore.pyqtSignal()
	sig_setp	  	 = QtCore.pyqtSignal([], [int], [int, int])
	sig_sync	  	 = QtCore.pyqtSignal()
	
	def setup_signals(self):
		print("Setup signals in thread - {}".format(QtCore.QThread.currentThreadId()))
		self.started.connect(lambda : print("Worker started"))
		self.finished.connect(lambda : print("Worker finished"))
		#self.terminated.connect(lambda : print("Worker terminated")) # terminated was removed in Qt5

		self.sig_connect.connect(bt.slot_connect)
		self.sig_disconnect.connect(bt.slot_disconnect)
		self.sig_sample.connect(bt.slot_sample)
		self.sig_sync.connect(bt.slot_sync)
		
		self.sig_setp.connect(bt.slot_setp)
		self.sig_setp[int].connect(bt.slot_setp)
		self.sig_setp[int, int].connect(bt.slot_setp)
		
		self.sig_stop.connect(bt.slot_stop)

		self.sig_select.connect(bt.slot_select)
		self.sig_up.connect(bt.slot_up)
		self.sig_down.connect(bt.slot_down)
		


		
_worker_thread = _WorkerThread()
bt.moveToThread(_worker_thread)  # <-- first this...
_worker_thread.setup_signals()  # <-- ...then that ?
_worker_thread.started.connect(bt._initCommunication)


class StartQT(QtGui.QMainWindow):
	
	def __init__(self, parent=None):

		print("Running thread main {}".format(QtCore.QThread.currentThreadId()))

		QtGui.QWidget.__init__(self, parent)
		#self.ui = Ui_MainWindow()
		self.ui = uic.loadUi("AppUI.ui", self)
		#self.ui.setupUi(self)

		# Setup the datalog
		self.log = log.DataLog(LOG_LENGTH)  # 10000 records to save

		# Create connection thread
		self.bt = bt
		
		# Connect gui buttons signals 
		self.ui.btn_connect.clicked.connect(_worker_thread.sig_connect.emit)
		self.ui.btn_get.clicked.connect(_worker_thread.sig_sample.emit)
		self.ui.btn_select.clicked.connect(_worker_thread.sig_select.emit)
		self.ui.btn_up.clicked.connect(lambda : self._step_param("+"))
		self.ui.btn_down.clicked.connect(lambda : self._step_param("-"))
		self.ui.btn_sync.clicked.connect(_worker_thread.sig_sync.emit)
		self.ui.btn_save.clicked.connect(self.log.Save)
		
		# Connect graph line checkboxes
		self.ui.chk_pump.clicked.connect(lambda checked: self.ui.graph.show_signal(PlotSignals.TACH_DRUM, checked))
		self.ui.chk_drum.clicked.connect(lambda checked: self.ui.graph.show_signal(PlotSignals.TACH_PUMP, checked))
		self.ui.chk_pres.clicked.connect(lambda checked: self.ui.graph.show_signal(PlotSignals.PRES, checked))
		self.ui.chk_temp.clicked.connect(lambda checked: self.ui.graph.show_signal(PlotSignals.TEMP, checked))
		
		# Connect slider
		self.ui.hslider.valueChanged.connect(self.on_slider_changed)

		# Parameter list
		self.ui.tbl_params.setModel(self.log.param_mdl)
			
		# Create graph
		self.ui.graph.setXRange(0, GRAPH_LEN)
		self.ui.graph.setYRange(0, 100)
		self.ui.graph.setDataLog(self.log);	

		# Connect signals from bt connection
		self.bt.sigSamples.connect(self.on_samples)
		self.bt.sigStopped.connect(self.on_stopped)

		self.bt.sigPackageReceived.connect(self.on_package_received)
		self.bt.sigConnected.connect(self.on_connected)
		self.bt.sigDisconnected.connect(self.on_disconnected)
		self.bt.sigConnectionTimeout.connect(self.on_connection_timeout)
		self.bt.sigPackageTimeout.connect(self.on_package_timeout)

				
		# Connect log  signals
		self.log.sigParamChange[int, int].connect(_worker_thread.sig_setp[int,int])
				
				
		# Check for saved .npz files.
		self.getFileCount()


		self.ui.tbl_params.show()

		# Kick off worker thread		
		_worker_thread.start()
		

	def getFileCount(self):
		""" Count the number of .csv files in the log directory. """
		basedir	 	 = os.path.dirname(os.path.abspath(__file__))
		filecount 	 = 0
		os.listdir()
		try:
			for file in os.listdir("{}/log".format(basedir)):
				if fnmatch.fnmatch(file, '*.csv'):
					filecount += 1
		except FileNotFoundError:
			return 0
					
		self.ui.spinBox.setMaximum(filecount)
		self.ui.btn_load.setEnabled((filecount > 0))
		return filecount



# 	def _step_param(self, direction):
# 		""" Increase or decrease currently selected parameter. 
# 		direction : string
# 			Increase with "+" or decrease with "-"
# 		"""
# 		return
# 	
# 		inds = self.ui.tbl_params.selectedIndexes()
# 		if len(inds)>1: return
# 		inds[0].row()
# 		
# 		item = self.ui.lst_params.currentItem()
# 		if item == None: return
# 		index = item.data(QtCore.Qt.UserRole)
# 		param = self.log.getParameter(index)
# 		nv = param["val"]
# 		if direction == "+": 
# 			nv += param["step"]
# 		elif direction == "-": 
# 			nv -= param["step"]
# 		_worker_thread.sig_setp[int, int].emit(index, nv)	
		
	
	def on_slider_changed(self, v):
		return;
# 		self.ui.graph.setRange(v, GRAPH_LEN)
# 		self.ui.graph.updateY()

	
	def on_show_line(self, lineno, visible):
		self.ui.graph.showLine(lineno, visible)
	

	def set_status(self, msg):
		self.ui.txt_status.setPlainText(msg)
				

	def on_package_received(self, package):
		if (len(package) == Sample.SIZE):
			s = Sample()
			s.Parse(package)
			self.ui.txt_status.setPlainText(str(s))
			self.log.addSample(s)
			self.ui.hslider.setMaximum(max(0, self.log.length - GRAPH_LEN))
		
		elif (len(package) == Parameter.SIZE):
			p = Parameter()
			p.Parse(package)
			self.ui.txt_status.setPlainText(str(p))
			self.log.addParameter(p)
		else:
			print("Received unknown data")
			
	def on_package_timeout(self):
		self.ui.txt_status.appendPlainText("Package timeout")

	def on_connection_timeout(self):
		self.ui.txt_status.appendPlainText("Connection timeout")

	def on_connected(self):
		self.ui.btn_connect.setText("Disconnect")
		self.ui.btn_connect.clicked.disconnect()
		self.ui.btn_connect.clicked.connect(_worker_thread.sig_disconnect)		
		self.ui.tab_samples.setEnabled(True)
		self.ui.tab_params.setEnabled(True)
		
		self.ui.txt_status.appendPlainText("Connected")
			
	def on_disconnected(self, txt=""):
		self.ui.btn_connect.setText("Connect")
		self.ui.btn_connect.clicked.disconnect()
		self.ui.btn_connect.clicked.connect(_worker_thread.sig_connect)
		self.ui.tab_samples.setEnabled(False)
		self.ui.tab_params.setEnabled(False)

		self.ui.txt_status.appendPlainText("Disconnected")
		self.ui.txt_status.appendPlainText(txt)

	def on_samples(self):
		self.ui.btn_get.setText("Stop")
		self.ui.btn_get.clicked.disconnect()
		self.ui.btn_get.clicked.connect(_worker_thread.sig_stop.emit)
		self.ui.txt_status.appendPlainText("Samples")

	def on_stopped(self):
		self.ui.btn_get.setText("Sample")
		self.ui.btn_get.clicked.disconnect()
		self.ui.btn_get.clicked.connect(_worker_thread.sig_sample.emit)
		self.ui.txt_status.appendPlainText("Stopped")
		

	def closeEvent(self, event):
		_worker_thread.quit()
		

if __name__ == "__main__":
	if len(sys.argv) > 1:
		ConWinch.SIMULATE = True  # Simulate bluetooth device
		
	app = QtGui.QApplication(sys.argv)
	myapp = StartQT()
	myapp.show()
	
	app.exec_()
	app.deleteLater()
	sys.exit()
	_worker_thread.quit()
# 	sys.exit(app.exec_())
