# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:55:46 2013

@author: Markus
"""


import serial
from connection.interface import ConInterface, TimeoutConnection, \
	ErrorConnection, TimeoutWrite, ErrorWrite, TimeoutRead, ErrorRead


class ConSerial(ConInterface):

	def __init__(self, port):
		""" Constructor for serial connection. """
		self.serial = serial.Serial()
		self.serial.baudrate = 115200
		self.serial.bytesize = serial.EIGHTBITS
		self.serial.parity = serial.PARITY_NONE
		self.serial.stopbits = serial.STOPBITS_ONE
		self.serial.timeout = 4.0
		self.serial.writeTimeout = 4.0
		self.setPort(port);

	def setPort(self, port):
		""" Set com port number. """
		print("Selecting com port {}".format(port));
		self.serial.port = port-1

	def close(self):
		""" Close connection. """
		return self.serial.close()


	def connect(self):
		""" Establish a connection. """
		# print("Try serial.open() with timeouts (%f, %f)." % (self.serial.timeout, self.serial.writeTimeout))
		print(self.serial)
		try:
			self.serial.open()
		except serial.SerialTimeoutException as e:
			raise TimeoutConnection(e)
		except serial.SerialException as e:
			raise ErrorConnection(e)
   

	def send(self, b):
		""" Send bytes in string b. """
		try:
			return self.serial.write(b)
		except serial.SerialTimeoutException as e:
			raise TimeoutWrite(e)
		except serial.SerialException as e:
			raise ErrorWrite(e)


	def recv(self, n):
		""" Receive n bytes of data. """
		try:
			data = self.serial.read(n)
		except serial.SerialTimeoutException as e:
			raise TimeoutRead(e)
		except serial.SerialException as e:
			raise ErrorRead(e)

		if len(data) < n:
			raise TimeoutRead()
		return data


	def recv_into(self, buffer, nbytes=0):
		""" Receive n bytes of data in buffer. May raise ConError exception. """
		#assert isinstance(buffer, bytearray)

		if nbytes == None or nbytes < 1:
			nbytes = len(buffer)

		data = self.recv(nbytes)
		buffer[:len(data)] = data
		return len(data)


	def settimeout(self, t):
		""" Set timeouts. """
		self.serial.timeout			 = t
		self.serial.writeTimeout	 = t
