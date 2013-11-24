# -*- coding: utf-8 -*-

import sys
import numpy as np
from winchCommObjects import Sample

class DataLog:
  """ Keeps data to plot """
  
  def __init__(self, size):
    self.size     = size  # max number of samples in record 
    self.length   = 0     # current number of samples in record
    self.data     = np.zeros(self.size, dtype=Sample.data_type) 
    self.recordno = 0
    self.params = {}
    self.reset()
    
    
  def addSample(self, sample):
    """ Add a winch sample to the log """
    self.length = min(self.length+1, self.size)
    
    # Forward data by one...
    self.data = np.roll(self.data, 1, 0)
    
    # ...then prepend the new sample
    self.data[0] = sample.data


  def addParameter(self, p):
    """ Add a winch parameter to the log. Returns False if the parameter was 
    updated and not added. """
    is_added = (p['index'] not in self.params)
    self.params[p['index']] = p.data
    return is_added  
    

  def reset(self):
    """ Empty the samples log. """
    #self.params = {}
    self.length   = 0     # current number of samples in record


  def getRange(self, offset=0, length=50):
    """ Return a valid range (inside the bounds) to use on data. """
    i0 = max(0, min(offset, self.length-length))
    i1 = min(i0+length, self.length)
    return range(i0,i1)

              
  def Save(self):
    """ Save log to disk. """
    self.recordno += 1 
    fname = "{}/log/record_{:03d}.npz".format(sys.path[0], self.recordno)
    print("Save %d samples in file %s" % (self.length, fname))
    np.savez(fname, samples=self.data[0:self.length], parameters=self.params)  
    return fname        
  
  
  def Load(self, fileno):
    """ Load a log from disk given the number of the log. """    
    fname = "{}/log/record_{:03d}.npz".format(sys.path[0], fileno)
    try:
      d = np.load(fname)
    except IOError:
      print("Error loading file %s" % fname)
      return ""
        
    self.reset()
    self.params = d["parameters"].item()   
    
#    print repr(self.params)
#    print repr(self.params[0])
      
    for s in d["samples"]:
      self.addSample(s)
    print("Loaded %d samples and %d parameters" % (d["samples"].size, d["parameters"].size))
    return fname
    