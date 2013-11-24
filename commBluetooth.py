# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:51:18 2013

@author: Markus
"""

import socket
from commInterface import commInterface
from commInterface import commError
#from PyQt4.QtCore import QString

class commBluetooth(commInterface):
  
  def __init__(self, port, addr):
    """ Construcor for a Bluetooth connection. May throw exception 
    AttributeError if bluetooth socket is not supported. """
    self.socket = None
    self.port = port
    self.addr = addr
    self.socket = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)

 
  def close(self):
    """ Close connection. """
    self.socket.shutdown(socket.SHUT_RDWR)
    return self.socket.close()

  
  def connect(self):
    """ Establish a connection. """
    try:
      self.socket.connect((self.addr, self.port))
    except (socket.error, socket.herror, socket.gaierror) as e:
      raise commError( str(e[1]) )
    except (socket.timeout) as e:
      raise commError( str(e) )

  
  def send(self, b):
    """ Send bytes in string b. """
#    print ("send command %d of length %d" % (ord(b), len(b))) 
    try:
      n = self.socket.send(b)
      print ("...send returned %s") % str(n)
      return n
    except (socket.error, socket.herror, socket.gaierror) as e:
      raise commError( str(e) )
    except (socket.timeout) as e:
      raise commError( str(e) )
  
  
  
  def recv(self, n):
    """ Recieve n bytes of data. """
#    print ("Wait for %d bytes..." % n)
    try:
      r = self.socket.recv(n)
#      print ("...got %s." % repr(r))
      return r
    except socket.error as e:
#      print ("...but failed with error: %s" % str(e))
      raise commError( str(e) )
  
  
  def settimeout(self, t):
    """ Set timeouts. """
    print ("Set bt timeout to %f") % t    
    return self.socket.settimeout(t)
    