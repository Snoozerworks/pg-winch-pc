# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:55:46 2013

@author: Markus
"""


import serial
from commInterface import commInterface, commError


class commSerial(commInterface):
  
  def __init__(self, port):
    """ Constructor for serial communication. """    
    print("Setting up serial port %d" % port)
    self.serial = serial.Serial()
    self.serial.port      = port
    self.serial.baudrate  = 115200
    self.serial.bytesize  = serial.EIGHTBITS
    self.serial.parity    = serial.PARITY_NONE
    self.serial.stopbits  = serial.STOPBITS_ONE
    self.serial.timeout      = 4.0
    self.serial.writeTimeout = 4.0
    
    
  def close(self):
    """ Close connection. """
    return self.serial.close()


  def connect(self):
    """ Establish a connection. """   
    #print("Try serial.open() with timeouts (%f, %f)." % (self.serial.timeout, self.serial.writeTimeout))
    try:
      self.serial.open()
    except serial.SerialException as e:
      raise commError( str(e) )
       

  def send(self, b):
    """ Send bytes in string b. """
    try:
      return self.serial.write(b)
    except serial.SerialTimeoutException as e:
      raise commError( str(e) )    

  
  def recv(self, n):
    """ Recieve n bytes of data. """
    r = self.serial.read(n)
    if len(r)<n:
      raise commError( "Timeout" )

    return r


  def settimeout(self, t):
    """ Set timeouts. """
    self.serial.timeout      = t
    self.serial.writeTimeout = t
   