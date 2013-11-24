# -*- coding: utf-8 -*-

import time
import numpy as np


# Texts for modes 
MODE_TXT = (
 "Okänt läge!", 
 "Uppstart", 
 "Inställlningar - installation", 
 "Inställningar - drift",
 "Vänteläge",
 "Dragläge")


class avgBuffer():
  def __init__(self, v, len):
    self.buf = [v/len]*len
    self.ind = 0
    self.len = len * 1.0
    self.sum = v

  def add(self, v):
    if self.ind >= self.len:
      self.ind = 0
    x = v / self.len
    self.sum += x - self.buf[self.ind]
    self.buf[self.ind] = x
    self.ind += 1


class Parameter():
  """ Represents a parameter definition. This corresponds to the
  parameters used by the Arduino . """
  
  
  # Record data type definition of raw data
  data_type = np.dtype([
    ("mode", "u1"),
    ("index", "u1"),
    ("val", ">h"),
    ("low", ">h"),
    ("high", ">h"),
    ("low_map", ">h"),
    ("high_map", ">h"),
    ("step", ">h"),
    ("descr", "S21")])


  def __init__(self):
    initval = [(0,0,0,0,1,0,1,1,"")]  # Init parameter values
    self.data =  np.array(initval, Parameter.data_type)
    self.descr2 = ""

    
  def __getitem__(self, i):
    return self.data[i]
    
    
  def Parse(self, data):
    """ Interpret the raw bytes received from the Arduino, and copy values to 
    the Parameter properties accordingly. """
    
    # Get the data record
    self.data       = np.frombuffer(buffer=data, dtype=Parameter.data_type, count=1, offset=0)[0]

    s = self.data["descr"]
    s = s.replace('\x00', '')
    s = s.replace('\x80', 'å')
    s = s.replace('\xE1', 'ä')
    s = s.replace('\xEF', 'ö')
    s = s.replace('\x81', 'Å')
    s = s.replace('\x82', 'Ä')
    s = s.replace('\x83', 'Ö')
    self.descr2 = s
    
    
  def mapval(self, v):
    """ Returns a value v mapped from (low,hi) to (low_map,high_map) 
    using linear interpolation. If high=low method returns 0."""        
    if self.data["low"]==self.data["high"]:
      return 0
    return self.data["low_map"] + (v-self.data["low"])*(self.data["high_map"]-self.data["low_map"])*1.0/ ((self.data["high"]-self.data["low"])*1.0)


  def __str__(self): 
    """ Returns a string representation of the parameter. """
    
    s = "Parameter - no %d\n" % (self.data["index"]+1)
    s += "  descr   : %s\n" % self.descr2
    s += "  mode    : %s (%d)\n" % (MODE_TXT[self.data["mode"]], self.data["mode"])
    s += "  val     : %4d (%4d)\n" % (self.mapval(self.data["val"]), self.data["val"])
    s += "  low     : %4d (%4d)\n" % (self.mapval(self.data["low"]), self.data["low"])
    s += "  high    : %4d (%4d)\n" % (self.mapval(self.data["high"]), self.data["high"])
    s += "  low_map : %4d\n" % self.data["low_map"]
    s += "  high_map: %4d\n" % self.data["high_map"]
    s += "  step    : %4d (%4d)\n" % (self.mapval(self.data["step"]), self.data["step"])
    return s
    
    
class Sample():
  """ Represents a sample as received when sending a get request to the 
  Arduino. """

  data_type = np.dtype([    # Data type definition of raw data
    ("mode", "u1"),
    ("time", ">u4"),
    ("tach_pump", "u1"),
    ("tach_drum", "u1"),
    ("temp", ">i2"),
    ("pres", ">i2")])
  pump_buffer = avgBuffer(0,10) # Average for tacho pump 
  drum_buffer = avgBuffer(0,10) # Average for tacho drum 
  time_buffer = avgBuffer(200,20) # Average for sample period 
  _tx_time  = [0,0]   # Transmitting times
  _rx_time  = [time.time(),time.time()]   # Recieving times
  _dt = 0
  p_pump = Parameter()
  p_drum = Parameter()
  p_temp = Parameter()
  p_pres = Parameter()
  
  
  def __init__(self, data=None):
    initval = [(0,0,0,0,0,0)]  # Init sample values
    self.data =  np.array(initval, Sample.data_type)

    
  def __getitem__(self, i):
    return self.data[i]


  def Parse(self, data):
    """ Interpret raw bytes as sent from the Arduino representing a sample. """
    self.data       = np.frombuffer(buffer=data, dtype=Sample.data_type, count=1, offset=0)[0]
    
    Sample._tx_time[1]  = Sample._tx_time[0]
    Sample._tx_time[0]  = self.data["time"]
    Sample._rx_time[1]  = Sample._rx_time[0]
    Sample._rx_time[0]  = time.time()
    
    Sample.pump_buffer.add(self.data["tach_pump"])
    Sample.drum_buffer.add(self.data["tach_drum"])
    Sample._dt = (Sample._rx_time[0] - Sample._rx_time[1])*1000.0
    Sample.time_buffer.add(Sample._dt)


  def __str__(self): 
    s = "Sample - receive period %d(%3.1f)\n" % (Sample._dt, Sample.time_buffer.sum)
    s += "  mode       : %2d (%s)\n" % (self.data["mode"], MODE_TXT[self.data["mode"]])
    s += "  on time    : %6d ms\n" % self.data["time"]
    s += "  pump speed : %4d(%4d) rpm\n" % (self.data["tach_pump"], Sample.pump_buffer.sum)
    s += "  drum speed : %4d(%4d) rpm\n" % (self.data["tach_drum"], Sample.drum_buffer.sum)
    s += "  period     : %4d ms\n" % (Sample._tx_time[0] - Sample._tx_time[1])
    s += "  temperature: %4d deg C\n" % self.data["temp"]
    s += "  pressure   : %4d bar\n" % self.data["pres"]
    return s

