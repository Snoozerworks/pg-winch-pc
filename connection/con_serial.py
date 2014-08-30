# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:55:46 2013

@author: Markus
"""


import serial
from connection.interface import  ConInterface, ConError, ErrorConnection,\
	TimeoutWrite, TimeoutRead


class ConSerial(ConInterface):
	
	def __init__(self, port):
		""" Constructor for serial connection. """		
		print("Setting up serial port {}".format(port));
		self.serial = serial.Serial()
		self.serial.port = port
		self.serial.baudrate = 115200
		self.serial.bytesize = serial.EIGHTBITS
		self.serial.parity = serial.PARITY_NONE
		self.serial.stopbits = serial.STOPBITS_ONE
		self.serial.timeout = 4.0
		self.serial.writeTimeout = 4.0
		
		
	def close(self):
		""" Close connection. """
		return self.serial.close()


	def connect(self):
		""" Establish a connection. """	 
		# print("Try serial.open() with timeouts (%f, %f)." % (self.serial.timeout, self.serial.writeTimeout))
		try:
			self.serial.open()
		except serial.SerialException as e:
			raise ErrorConnection(e)


	def send(self, b):
		""" Send bytes in string b. """
		try:
			return self.serial.write(b)
		except serial.SerialTimeoutException as e:
			raise TimeoutWrite(e) 		

	
	def recv(self, n):
		""" Receive n bytes of data. """
		data = self.serial.read(n)
		if len(data)<n:
			raise TimeoutRead()
		return data 

	
	def recv_into(self, buffer, nbytes=0):
		""" Receive n bytes of data in buffer. May raise ConError exception. """
		assert isinstance(buffer, bytearray)
		
		if nbytes == None or nbytes < 1:
			nbytes = len(buffer)
		
		data = self.recv(nbytes)
		buffer[:len(data)] = data
		return len(data)		


	def settimeout(self, t):
		""" Set timeouts. """
		self.serial.timeout			= t
		self.serial.writeTimeout	= t
