# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:34:12 2013

@author: Markus
"""

import abc


class ConInterface(object):
	"""
	Abstract class defining the connection interface. 
	"""
	__metaclass__ = abc.ABCMeta


	@abc.abstractmethod
	def close(self):
		""" Override to close connection. """
		raise NotImplemented


	@abc.abstractmethod
	def connect(self):
		""" Override to establish a connection. """
		raise NotImplemented


	@abc.abstractmethod
	def send(self, b):
		""" Override to send bytes in b.
		
		:param b: Bytes to send.
		:type b: bytes
		"""
		raise NotImplemented


	@abc.abstractmethod
	def recv(self, n):
		""" Override to receive n bytes of data. 
		
		n : integer
			Number of bytes to receive.
		"""
		raise NotImplemented


	def recv_into(self, buffer, nbytes):
		raise NotImplemented


	@abc.abstractmethod
	def settimeout(self, t):
		""" Override to set timeouts.
		
		:param t: Timeout in seconds 
		:type t: number
		"""
		raise NotImplemented




class ConError(Exception):
	"""
	Base class for all connection errors. 
	"""
	def __init__(self, exception=None):
		self.exception = exception

	def __str__(self):
		return  "{!s}".format(self.exception)


class TimeoutConnection(ConError): pass
class TimeoutRead(ConError): pass
class TimeoutWrite(ConError): pass
class ErrorConnection(ConError): pass
class ErrorRead(ConError): pass
class ErrorWrite(ConError): pass

