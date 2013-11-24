# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 22:46:21 2013

@author: Markus
"""

class CMD():
  """ Collection of constants for commands """
  _CLOSE= -2  # Used in python script only
  _SYNC = -1  # Used in python script only
  NOCMD = 0
  CONF  = 1
  SET   = 2
  UP    = 3
  DOWN  = 4
  SETP  = 5
  GET   = 6
  
  _TXT = {-2: "Close", -1: "Sync", 0: "NOCMD", 1: "CONF", 2: "SET",
           3: "UP"   ,  4: "DOWN", 5: "SETP",  6: "GET"}


class MODE():
  """ Collection of constants for mode """
  NOMODE    = 0
  STARTUP   = 1
  CONFIG_IS = 2
  CONFIG_OS = 3
  IDLE      = 4
  TOWING    = 5
