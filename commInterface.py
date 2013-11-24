# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 15:34:12 2013

@author: Markus
"""

import abc


class commInterface(object):
  __metaclass__ = abc.ABCMeta
  
 
  @abc.abstractmethod
  def close(self):
    """ Close connection. """
    return

  
  @abc.abstractmethod
  def connect(self):
    """ Establish a connection. """
    return

  
  @abc.abstractmethod
  def send(self, b):
    """ Send bytes in string b. """
    return

  
  @abc.abstractmethod
  def recv(self, n):
    """ Recieve n bytes of data. """
    return

  
  @abc.abstractmethod
  def settimeout(self, t):
    """ Set timeouts. """
    return



class commError(Exception):

  def __init__(self, value):
    self.value = value
    
  def __str__(self):
    return self.value
    