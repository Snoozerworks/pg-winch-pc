# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 22:46:21 2013

@author: Markus
"""
import time
import struct
import numpy as np

from commInterface import commInterface
from winchConstants import CMD, MODE


class commSimulated(commInterface):
  """ A dummy class to simulate a bluetooth connection """
  
  def __init__(self):
    print ("Socket start")
    
    self.mode = MODE.IDLE
    self.zero_time = time.time()  

    self.cmd_time = [self.zero_time, self.zero_time]
    self.cmd      = [CMD.NOCMD, CMD.NOCMD] 
    self.count    = 0;
    self.paramno  = 0;
  
    self.dummy_param = bytearray(35)
    self.dummy_param[0]     = struct.pack("B", MODE.CONFIG_OS)  # mode
    self.dummy_param[1]     = struct.pack("B", self.paramno) # index
    self.dummy_param[2:4]   = [0,1]         # val
    self.dummy_param[4:6]   = [0,2]         # low
    self.dummy_param[6:8]   = [0,4]         # high
    self.dummy_param[8:10]  = [0,4]         # low_map
    self.dummy_param[10:12] = [0,8]         # high_amp
    self.dummy_param[12:14] = [0,1]         # step
    self.dummy_param[14:35] = "abcabcabcabcabcabcabc"
  
  
  def close(self, *args):
    """ Close connection. """
    pass


  def shutdown(self, *args):
    """ Shutdown connection. """
    pass

  
  def connect(self, *args):
    """ Establish a connection. """
    time.sleep(0.1)


  def send(self, cmd):
    """ Send bytes in string b. """
    self.cmd_time[1] = self.cmd_time[0]
    self.cmd_time[0] = time.time()
    self.cmd[1] = self.cmd[0]
    self.cmd[0] = ord(cmd)

    #print ("Send command %d") % ord(cmd)

    if self.mode!=MODE.IDLE and self.cmd_time[0]-self.cmd_time[1]>6.0:
      print ("Switch to mode IDLE")
      self.mode=MODE.IDLE

    if self.cmd[0]==CMD.SET and self.mode==MODE.IDLE:
      self.mode=MODE.CONFIG_OS
      print ("Switch to mode CONFIG_OS")
      
    #time.sleep(0.18)


  def recv(self, c):
    """ Recieve n bytes of data. """

    self.count += 1
    #print("recv(%d)" % c)
    
    if self.mode==MODE.IDLE:
      if self.cmd[0]==CMD.GET:      
        print ("Sending sample")
        data = self._getDummySample()
        return str(data)
        
      if self.cmd[0]==CMD.SET:      
        print ("Sending parameter")
        self.paramno = 0    # Send first parameter
        data = self._getDummyParameter(0)
        return str(data)
        
      if self.cmd[0]==CMD.UP: 
        print ("Increase throttle.")
        return str(self._getDummySample())
        
      if self.cmd[0]==CMD.DOWN:      
        print ("Decrease throttle.")
        return str(self._getDummySample())
        

    if self.mode==MODE.CONFIG_OS:
      if self.cmd[0]==CMD.GET:      
        print ("Sending nothing")
        return ""        
      
      if self.cmd[0]==CMD.SET:      
        print ("Sending next parameter")
        data = self._getDummyParameter(self.paramno+1)
        return str(data)
        
      if self.cmd[0]==CMD.UP: 
        print ("Increase parameter.")
        data = self._changeParamVal(1)
        return str(data)
        
      if self.cmd[0]==CMD.DOWN:      
        print ("Decrease parameter.")
        data = self._changeParamVal(-1)
        return str(data)        
      
      
    print("Unhandled mode")
    return ""

  
  def settimeout(self, *args):   
    """ Set timeouts. """
    pass


  def _getDummySample(self):
    data = bytearray(11)
    data[0]     = struct.pack("B", MODE.IDLE)  # Mode
    data[1:5]   = struct.pack(">I", time.time()-self.zero_time) # Time
    data[5]     = int(127 + 128*np.sin(self.count/10.0)) # Pump counts
    data[6]     = int(127 + 128*np.sin(self.count/10.0+1)) # Drum counts
    data[7:9]   = struct.pack(">h", 40 + 60*np.sin(self.count/20.0+2) ) # Temperature
    data[9:11]  = struct.pack(">h", 250 + 100*np.sin(self.count/7.0+3) )  # Pressure
    return data


  def _getDummyParameter(self, no):
    self.paramno = no % 6
    self.dummy_param[1] = struct.pack("B", self.paramno) # index
    return self.dummy_param
    
    
  def _changeParamVal(self, delta):
    v = struct.unpack(">h", self.dummy_param[2:4])[0]
    self.dummy_param[2:4] = struct.pack(">h", v + delta) 
    return self._getDummyParameter(self.paramno)
    
