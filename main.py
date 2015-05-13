#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 20:42:16 2013

@author: Markus
"""

import os
import sys
import fnmatch
import configparser
from PyQt4 import uic
from PyQt4 import QtCore, QtGui

# from AppUI import Ui_MainWindow
from connection.con_winch import ConWinch
from arduino.package import Parameter, Sample

import dataLog as log
from TimePlot import TimePlot, PlotSignals
from defaults import APP_CONFIG_FILE, APP_DEFAULTS, APP_ROOT

LOG_LENGTH 		 = 4500		# Max samples in log stack
GRAPH_LEN 		 = 100		# Max samples to show in graph

# Run connection in separate thread
bt = ConWinch("00:06:66:43:11:8D", 16)

class _WorkerThread(QtCore.QThread):
	def setup_signals(self):
		print("Setup signals in thread - {}".format(QtCore.QThread.currentThreadId()))
		self.started.connect(lambda : print("Worker started"))
		self.finished.connect(lambda : print("Worker finished"))


_worker_thread = _WorkerThread()
bt.moveToThread(_worker_thread)  # <-- first this...
_worker_thread.setup_signals()  # <-- ...then that ?
_worker_thread.started.connect(bt._initCommunication)


class StartQT(QtGui.QMainWindow):

	def __init__(self, parent=None):

		print("Running thread main {}".format(QtCore.QThread.currentThreadId()))

		# Load GUI
		QtGui.QWidget.__init__(self, parent)
		self.ui = uic.loadUi(os.path.join(APP_ROOT, "AppUI.ui"), self)

		# Load settings
		self.conf 				 = configparser.ConfigParser()
		self.conf["DEFAULT"]	 = APP_DEFAULTS
		self.conf["winch"]		 = {}
		conf					 = self.conf["winch"]
		if os.path.isfile(APP_CONFIG_FILE):
			self.conf.read_file(open(APP_CONFIG_FILE, mode="rt", encoding="utf8"))
		if conf.get("log-path") == None:
			conf["log-path"] = os.path.join(APP_ROOT, "log")

		# Setup the datalog
		self.log 			 = log.DataLog(LOG_LENGTH)  # records to save
		self.log.log_path	 = conf["log-path"]

		# Create connection thread
		self.bt = bt

		# Set tab stop for text field
		self.ui.txt_status.tabStopWidth = 40

		# Setup log folder lineedit and button
		print("PATH=" + conf["log-path"])
		self.ui.lineEdit_log_folder.setText(conf["log-path"])
		def onPathChange():
			d = QtGui.QFileDialog.getExistingDirectory(directory=conf["log-path"])
			if d == "": return
			self.ui.lineEdit_log_folder.setText(d)
			conf["log-path"] = d
			self.log_path = d
		self.ui.btn_log_folder.clicked.connect(onPathChange)

		# Setup mac-address lineedit
		self.ui.lineEdit_btmac.setInputMask("HH:HH:HH:HH:HH:HH;_")
		self.ui.lineEdit_btmac.setText(APP_DEFAULTS["mac-address"])
		self.ui.lineEdit_btmac.setText(conf["mac-address"])
		def onMacChange():
			value = self.ui.lineEdit_btmac.text().lower()
			print(value)
			bt.slot_changeMac(value)
			conf["mac-address"] = value
		self.ui.lineEdit_btmac.editingFinished.connect(onMacChange)

		# Setup com-port spinbox
		self.ui.spinBox_COMport.setValue(int(conf["com-port"]))
		def onComChange():
			value = self.ui.spinBox_COMport.value()
			bt.slot_changeSerialPort(value)
			conf["com-port"] = str(value)
		self.ui.spinBox_COMport.valueChanged.connect(onComChange)

		# Connect gui buttons signals
		self.ui.btn_connect.clicked.connect(bt.slot_connect)
		self.ui.btn_get.clicked.connect(bt.slot_sample)
		self.ui.btn_select.clicked.connect(bt.slot_select)
		self.ui.btn_up.clicked.connect(bt.slot_up)
		self.ui.btn_down.clicked.connect(bt.slot_down)
		self.ui.btn_sync.clicked.connect(bt.slot_sync)
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
		self.ui.tbl_params.show()

		# Create graph
		self.ui.graph.setDataLog(self.log);
		self.ui.graph.setDisplayRange(0, GRAPH_LEN)

		# Connect signals from bt connection
		self.bt.sigSamples.connect(self.on_samples)
		self.bt.sigStopped.connect(self.on_stopped)

		self.bt.sigPackageReceived.connect(self.on_package_received)
		self.bt.sigConnected.connect(self.on_connected)
		self.bt.sigDisconnected.connect(self.on_disconnected)
		self.bt.sigConnectionTimeout.connect(self.on_connection_timeout)
		self.bt.sigPackageTimeout.connect(self.on_package_timeout)

		# Connect log  signals
		self.log.sigParamChange.connect(bt.slot_setp)

		# Check for saved .npz files.
		self.getFileCount()

		# Kick off worker thread
		_worker_thread.start()


	def getFileCount(self):
		""" Count the number of .csv files in the log directory. """
		filecount = 0
		os.listdir()
		try:
			for file in os.listdir(os.path.join(self.conf["winch"]["log-path"], "log")):
				if fnmatch.fnmatch(file, '*.csv'):
					filecount += 1
		except FileNotFoundError:
			return 0

		self.ui.spinBox.setMaximum(filecount)
		self.ui.btn_load.setEnabled((filecount > 0))
		return filecount


	def on_slider_changed(self, v):
		self.ui.graph.setDisplayRange(0, v)


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
			self.ui.hslider.setMaximum(max(1, self.log.length))

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
		self.ui.btn_connect.clicked.connect(bt.slot_disconnect)
		self.ui.tab_samples.setEnabled(True)
		self.ui.tab_params.setEnabled(True)

		self.ui.txt_status.appendPlainText("Connected")


	def on_disconnected(self, txt=""):
		self.on_stopped() # Reset GUI to a "stopped" state

		self.ui.btn_connect.setText("Connect")
		self.ui.btn_connect.setChecked(False)
		self.ui.btn_connect.clicked.disconnect()
		self.ui.btn_connect.clicked.connect(bt.slot_connect)
		self.ui.tab_samples.setEnabled(False)
		self.ui.tab_params.setEnabled(False)

		self.ui.txt_status.appendPlainText("Disconnected : " + txt)


	def on_samples(self):
		self.ui.btn_get.setText("Stop")
		self.ui.btn_get.clicked.disconnect()
		self.ui.btn_get.clicked.connect(bt.slot_stop)
		self.ui.txt_status.appendPlainText("Samples")


	def on_stopped(self):
		self.ui.btn_get.setText("Sample")
		self.ui.btn_get.setChecked(False)
		self.ui.btn_get.clicked.disconnect()
		self.ui.btn_get.clicked.connect(bt.slot_sample)
		self.ui.txt_status.appendPlainText("Stopped")


	def closeEvent(self, event):
		print("Stopping thread")
		with open(APP_CONFIG_FILE, mode="+w", encoding="utf8") as f:
			self.conf.write(f)
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
