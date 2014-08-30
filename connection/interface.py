# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:34:12 2013

@author: Markus
"""

import abc


class ConInterface(object):
	__metaclass__ = abc.ABCMeta
	

	@abc.abstractmethod
	def close(self):
		""" Close connection. """
		raise NotImplemented		

	
	@abc.abstractmethod
	def connect(self):
		""" Establish a connection. """
		raise NotImplemented		

	
	@abc.abstractmethod
	def send(self, b):
		""" 
		Send bytes in b.
		
		b : bytes
			Bytes to send. 		
		"""
		raise NotImplemented		

	
	@abc.abstractmethod
	def recv(self, n):
		""" Receive n bytes of data. 
		
		n : integer
			Number of bytes to receive.
		"""
		raise NotImplemented		


	def recv_into(self, buffer, nbytes):
		raise NotImplemented

	
	@abc.abstractmethod
	def settimeout(self, t):
		""" Set timeouts. 
		
		t : number
			Timeout in seconds.
		"""
		raise NotImplemented		




class ConError(Exception):
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
	
