# -*- coding: utf-8 -*-

# For debugging

try:
	import pydevd
except:
	pass

import arduino

pydevd.connected = True

import time
from enum import Enum, unique

from PyQt4 import QtCore

from arduino.package import Sample, Parameter
from arduino.constants import Commands, Modes, Command

from connection.interface import TimeoutRead, ErrorRead, TimeoutWrite, \
	TimeoutConnection, ErrorConnection, ErrorWrite
from connection.con_bluetooth import ConBluetooth
from connection.con_serial import ConSerial
from connection.con_simulated import ConSimulated

"""
Known bluetooth mac addresses 
	00:06:66:43:11:8D	- first version of controller 
	00:06:66:43:07:AF	- second version of controller
"""

@unique
class ConStates(Enum):
	"""
	Winch connection states.  
	"""
	STATE_UNKNOWN = 0
	STATE_DISCONNECTED = 1
	STATE_SAMPELS = 2
	STATE_SYNCS = 3
	STATE_STOPPED = 4

# class ConWinch(QtCore.QThread):
class ConWinch(QtCore.QObject):
	SIMULATE = False  # Set to true to simulate a bluetooth connection

	# Signals
	# conn_status = QtCore.pyqtSignal(int, 'QString')
	# 	 sigDisconnected			 = QtCore.pyqtSignal()

	sigConnected	 = QtCore.pyqtSignal()
	sigDisconnected	 = QtCore.pyqtSignal([str], [])
	sigSamples		 = QtCore.pyqtSignal()
	sigSyncs		 = QtCore.pyqtSignal()
	sigStopped		 = QtCore.pyqtSignal()

	sigConnectionTimeout = QtCore.pyqtSignal()
	sigPackageReceived = QtCore.pyqtSignal(bytes)
	sigPackageTimeout = QtCore.pyqtSignal()

	sigStateChange = QtCore.pyqtSignal(ConStates)

	_sigSend = QtCore.pyqtSignal(Command)

	# Connection status
	DISCONNECTED	= 0
	CONNECTED		= 1
	ERR_CONNECTION	= 2
	ERR_SYNC		= 3
	ERR_TIMEOUT		= 4

	# Some settings
	conn_retry_delay	= 3.0
	COM_PORT			= 16

	_con_state		= ConStates.STATE_UNKNOWN
	_param_indices	= []

	bt_mac			= ""  # BLuetooth mac address
	port			= 2
	timeout			= 1.0  # Timeout when waiting for data
	conn_timeout	= 10.0  # Timeout upon initial connection
	sock			= None  # Will normally hold a socket object

	def __init__(self, bt_mac):  # 			 self.result_rx.emit()
		super().__init__()

		print("ConWinch::__init__ - {}".format(QtCore.QThread.currentThreadId()))

		self.bt_mac			= bt_mac
		self._start_time	= 0
		self._sample_count	= 0

		# slot_connect connection to the winch or simulator
# 		 self._initCommunication()

	def _initCommunication(self):
		""" Setup connection to the winch using bluetooth, serial or a 
		simulated connection. """

		print("_initCommunication - {}".format(QtCore.QThread.currentThreadId()))

		# Simulate a connection
		if ConWinch.SIMULATE:
			print("*** Simulating bluetooth ***")
			ConWinch.sock = ConSimulated()
			return

		# Connect internal signal here since it will run in worker thread
		try:
			self._sigSend.connect(self._send, QtCore.Qt.QueuedConnection)
			print("Connected _sigGetNext to _get_next()")
		except Exception as e:
			print("No connection of _sigGetNext to _get_next()")
			print(e)

		# Try a bluetooth connection.
		try:
			ConWinch.sock = ConBluetooth(port=2, addr=self.bt_mac)
		except AttributeError:
			# Try a serial connection.
			print("Bluetooth socket not supported. Falling back to serial connection.")
			ConWinch.sock = ConSerial(ConWinch.COM_PORT)

	def __del__(self):
		""" Closes socket before destroying object. """
		if ConWinch.sock == None : return
		ConWinch.sock.close()
		ConWinch.sock = None

	def _ReadItem(self):
		"""
		Read connection to get a parameter or sample.
		Returns number of bytes read or None in case of a connection timeout.
		:rtype: int
			Number of bytes read.
		"""

		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		mv_chunk1	= memoryview(bytearray(35))  # Received byte storage
		received 	= 0  # Number of bytes received
		expect 		= 12  # Number of bytes to fetch

# 		 mv_chunk1 = memoryview(chunk1)

		# Start getting at least first byte to determine winch mode.
		try:
			received += ConWinch.sock.recv_into(mv_chunk1, expect)
		except (TimeoutRead, ErrorRead):
			self.sigPackageTimeout.emit()
			return received		
		except (ErrorConnection) as e:
			self.sigDisconnected.emit(str(e))
			self._set_state(ConStates.STATE_DISCONNECTED)
			return received
		
		m = Modes.getMode(mv_chunk1[0])

		# If in configuration mode, expect a parameter of 35 bytes.
		if m == Modes.CONFIG_IS or m == Modes.CONFIG_OS: expect = 35

		# Fetch remaining bytes
		while expect > received:
			try:
				received += ConWinch.sock.recv_into(mv_chunk1[received:])
			except (TimeoutRead, ErrorRead):
				self.sigPackageTimeout.emit()
				return received
			except (ErrorConnection) as e:
				self.sigDisconnected.emit(str(e))
				self._set_state(ConStates.STATE_DISCONNECTED)
				return received

		if received == Parameter.SIZE:
			# Parameter received!
			data = bytes(mv_chunk1[:Parameter.SIZE])
			self.sigPackageReceived.emit(data)

			if self._con_state == ConStates.STATE_SYNCS:
				# Syncronizing parameters.
				p_ind = Parameter(data)["index"]
				if p_ind in ConWinch._param_indices:
					self._set_state(ConStates.STATE_STOPPED)
				else:
					ConWinch._param_indices.append(p_ind)
					self._sigSend.emit(Commands.SP)

		elif received == Sample.SIZE:
			# Sample received!
			data = bytes(mv_chunk1[:Sample.SIZE])
			self.sigPackageReceived.emit(data)
			self._sample_count += 1

			if self._con_state == ConStates.STATE_SAMPELS:
				# Getting samples.
				# print("Read - received {:3d} samples.".format(self._sample_count))
				self._sigSend.emit(Commands.GT)

		return received

	def _PollWinsch(self, c, param_index=None, param_val=None):
		""" Send a command to the winch and return the result. The result may be
		a Sample, Parameter or None. None is returned if result cannot be 
		properly parsed or there is a timeout. 

		The SP (set parameter) command have 3 possibilities;
		If no optional arguments are given, get next parameter (also installation parameters).  
		With param_index only, it gets the indexed parameter.   
		With param_index and param_val, it sets the indexed parameter to the given value.

		c: arduino.constants.Command
			Command to send
		param_index: uint8
			Parameter index. Ignored unless c is arduino.constants.Commands.SP.			
		param_val: int16
			Parameter index. Ignored unless c is arduino.constants.Commands.SP.
		"""

		assert isinstance(c, arduino.constants.Command)

		tx_bytes = bytearray([c.code])

		# Check optional arguments if command is SP (set parameter)
		if c == Commands.SP:
			if param_index != None:
				tx_bytes.append(param_index)
				if param_val != None:
					tx_bytes += param_val.to_bytes(length=2, byteorder='big', signed=True)

		try:
			ConWinch.sock.send(tx_bytes)
		except TimeoutWrite:
			self.sigPackageTimeout()
		except ErrorWrite:
			self.sigDisconnected.emit("Failed to write data")
		else:
			# print("Poll {}".format(c))
			QtCore.QThread.sleep(0.05)
			self._ReadItem()

	def _set_state(self, state):
		assert state in ConStates
		if (self._con_state == state): return
		self._con_state = state
		self.sigStateChange.emit(state)

	@QtCore.pyqtSlot()
	def slot_connect(self):
		""" slot_connect to winch. Returns true on success and false otherwise. """

		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		ConWinch.sock.settimeout(ConWinch.conn_timeout)
		try:
			ConWinch.sock.connect()
		except (TimeoutConnection):
			self.sigConnectionTimeout.emit();
			self.sigDisconnected.emit("Connection timeout")
			self._set_state(ConStates.STATE_DISCONNECTED)
			return (time.time(), False)
		except (ErrorConnection) as e:
			self.sigDisconnected.emit(str(e))
			self._set_state(ConStates.STATE_DISCONNECTED)
			return (time.time(), False)

		print("Connection opened.")
		ConWinch.sock.settimeout(ConWinch.timeout)
		self.sigConnected.emit()
		self._set_state(ConStates.STATE_STOPPED)
		return (time.time(), True)

	@QtCore.pyqtSlot()
	def slot_disconnect(self):
		""" Stops connection to the winch but keeps the socket open. """

		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		# Disconnect internal signal since it will re-connected in slot_connect()
# 		 self._sigGetNext.disconnect()
		print("...slot_disconnect - {}".format(QtCore.QThread.currentThreadId()))

		ConWinch.sock.close()
		print("Connection closed.")
		self._set_state(ConStates.STATE_DISCONNECTED)
		self.sigDisconnected.emit("Connection intentionally closed");

	def slot_stop(self):
		try:
			pydevd.settrace(suspend=False)
		except:
			pass
		self._set_state(ConStates.STATE_STOPPED)
		self.sigStopped.emit()

	def slot_sample(self):
		if self._con_state != ConStates.STATE_STOPPED : return

		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		self._set_state(ConStates.STATE_SAMPELS)
		self.sigSamples.emit()
		self._PollWinsch(Commands.GT)

	def slot_up(self):
		if self._con_state != ConStates.STATE_STOPPED : return
		self._PollWinsch(Commands.UP)

	def slot_down(self):
		if self._con_state != ConStates.STATE_STOPPED : return
		self._PollWinsch(Commands.DN)

	def slot_select(self):
		if self._con_state != ConStates.STATE_STOPPED : return
		self._PollWinsch(Commands.SE)

	def slot_setp(self, param_index=None, param_val=None):
		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		if self._con_state != ConStates.STATE_STOPPED : return
		self._PollWinsch(Commands.SP, param_index, param_val)

	def slot_sync(self):
		""" Fetch parameters from winch. """

		try:
			pydevd.settrace(suspend=False)
		except:
			pass

		if self._con_state != ConStates.STATE_STOPPED: return

		# Start sync.
		self._set_state(ConStates.STATE_SYNCS)
		self.sigSyncs.emit()
		# Clear list of parameter indices...
		ConWinch._param_indices.clear()
		# ...and start getting parameters
		self._PollWinsch(Commands.SP, 0)

	@QtCore.pyqtSlot('QString')
	def slot_changeMac(self, mac):
		print("Change MAC to: " + mac)
		self.bt_mac = mac

#
# 		 o = self._PollWinsch(Commands.SE)
# 		 if not isinstance(o, Parameter):
# 			 self._set_state(ConStates.STATE_STOPPED)
# 			 # self.conn_status.emit(ConWinch.ERR_SYNC, "Parameter sync error. Unknown data received.")
# 			 return
#
# 		 p_set = {}
# 		 while (o.data["index"] not in p_set):
# 			 p_set[o.data["index"]] = o
# 			 o = self._PollWinsch(Commands.SE)
#
# 		 Sample.p_drum = p_set[0]
# 		 Sample.p_pump = p_set[1]
# 		 Sample.p_temp = p_set[2]
# 		 # Sample.p_pres = p_set[]
#
# 		 print("slot_sync done!")

	def _send(self, cmd):
		self._PollWinsch(cmd)
