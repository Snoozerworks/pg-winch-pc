# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:51:18 2013

@author: Markus
"""

import socket
from connection.interface import ConInterface, TimeoutConnection, \
	ErrorConnection, TimeoutWrite, ErrorWrite, TimeoutRead, ErrorRead


class ConBluetooth(ConInterface):

	def __init__(self, port, addr):
		""" Constructor for a bluetooth connection. May throw exception 
		AttributeError if bluetooth socket is not supported. 
		:type port: String
			Bluetooth port.
		:type addr: String
			Bluetooth mac-address.
		"""
		self.port = port
		self.addr = addr
		self.socket = None
		self._timeout = 10


	def close(self):
		""" Close connection. """
		if self.socket == None : return
		self.socket.shutdown(socket.SHUT_RDWR)
		self.socket.close()
		self.socket = None


	def connect(self):
		""" Establish a connection. May raise TimeoutConnection or ErrorConnection. """
		if self.socket != None: self.close()

		self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
		self.socket.settimeout(self._timeout)

		try:
			self.socket.connect((self.addr, self.port))
		except (socket.timeout) as e:
			raise TimeoutConnection(e)
		except (socket.herror, socket.gaierror, OSError) as e:
			raise ErrorConnection(e)


	def send(self, b):
		""" Send all bytes in b. May raise TimeoutWrite or ErrorWrite. """
		if self.socket == None: return

		# print("sends {} len({})".format(b, len(b)))
		try:
			self.socket.send(b)
		except (socket.timeout) as e:
			raise TimeoutWrite(e)
		except (socket.herror, socket.gaierror, OSError) as e:
			raise ErrorWrite(e)


	def recv(self, n):
		""" Receive up to n bytes of data. 
		May raise TimeoutRead, ErrorRead or ErrorConnection. 
		Returns the bytes received. """
		if self.socket == None: 
			raise ErrorConnection("Socket closed")
			return 0

		try:
			bytesread = self.socket.recv(n)
		except (socket.timeout) as e:
			raise TimeoutRead(e)
		except (socket.herror, socket.gaierror, OSError) as e:
			raise ErrorRead(e)
		return bytesread


	def recv_into(self, buffer, nbytes=0):
		""" Receive up to nbytes of data in buffer.
		May raise TimeoutRead,	ErrorRead or ErrorConnection. 
		Returns number of bytes received or None if socket is closed. """
		if self.socket == None: 
			raise ErrorConnection("Socket closed")
			return 0

		try:
			bytesread = self.socket.recv_into(buffer, nbytes)
		except (socket.timeout) as e:
			raise TimeoutRead(e)
		except (socket.herror, socket.gaierror, OSError) as e:
			raise ErrorRead(e)
		return bytesread


	def settimeout(self, t):
		""" Set timeouts. """
		# print ("Set bt timeout to {}".format(t))
		self._timeout = t
		if self.socket == None: return
		self.socket.settimeout(t)
