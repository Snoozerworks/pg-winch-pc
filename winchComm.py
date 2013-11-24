# -*- coding: utf-8 -*-

import time

import queue
from PyQt4 import QtCore


from winchCommObjects import Parameter, Sample
from winchConstants import CMD, MODE

from commInterface import commError 
from commBluetooth import commBluetooth 
from commSerial    import commSerial 
from commSimulated import commSimulated 



class Comm(QtCore.QThread):
  SIMULATE = False # Set to true to simulate a bluetooth connection

  # Connection status 
  DISCONNECTED    = 0  
  CONNECTED       = 1
  ERR_CONNECTION  = 2
  ERR_SYNC        = 3
  ERR_TIMEOUT     = 4
  
  # Some settings
  conn_retry_delay = 3.0
  COM_PORT = 16

  # Signals
  result_rx = QtCore.pyqtSignal()
  conn_status = QtCore.pyqtSignal(int, 'QString')
  #conn_status = QtCore.pyqtSignal([int, 'QString'])
  
  
  BT_ADDR       = "00:06:66:43:11:8D" # first version of controller 
  BT_ADDR       = "00:06:66:43:07:AF" # second version of controller
  port          = 2
  timeout       = 1.0   # Timeout when waiting for data
  conn_timeout  = 5.0    # Timout upon initial connnection
  sock          = None  # Will normally hold a socket object

  def __init__(self, notify_window):
    super(Comm, self).__init__()

    # Que for recieved data, i.e. samples and parameters
    self.q_result = queue.Queue(1)

    # Que for commands to send to winch.
    self.q_command = queue.Queue(1)

    self._is_connected = False
    self._start_time = 0
    
    # Start communication to the winch or simulator
    self._initCommunication()
    
    
  def _initCommunication(self):
    """ Setup communication to the winch using bluetooth, serial or a 
    simulated connection. """
    
    # Simulate a connection
    if Comm.SIMULATE:
      print("*** Simulating bluetooth ***")
      Comm.sock = commSimulated()
      return
    
    # Try a bluetooth connection. 
    try:
      Comm.sock = commBluetooth(port=2, addr=Comm.BT_ADDR)
      return
    except AttributeError:
      pass
    
    # Try a serial connection.    
    print("Bluetooth socket not supported. Falling back to serial communication.")
    Comm.sock = commSerial(Comm.COM_PORT)  
    
        
  def run(self):
    cmd = CMD.NOCMD
    # Try to connect
    self._start_time, self._is_connected = self.Start()
    
    while True:
      # Block until command is given
      try:
        cmd = self.q_command.get()
      except Exception as e:
        print(e)
      
      if cmd==CMD._CLOSE: 
        self.Stop()
        return None # Quit thread

      if not self._is_connected:
        if time.time()-self._start_time>Comm.conn_retry_delay:
          # Try to reconnect every 3 seconds
          print("Try reconnect...")
          self._start_time, self._is_connected = self.Start()
          
      elif cmd==CMD._SYNC:      
          self.Sync()
          cmd = CMD.NOCMD

      elif cmd!=CMD.NOCMD:
        self._PollWinsch(cmd)


  def __del__(self):
    """ Closes socket before destroying object. """
    Comm.sock.close()
    Comm.sock = None


  def Stop(self):
    """ Stops communication to the winsch but keeps the socket. """
    print("Close communication and return from thread")
    Comm.sock.close() 
    self.emit(Comm.DISCONNECTED, "")

  
  def Start(self):
    """ Connect to winch. Returns true on success and false othervice. """
    Comm.sock.settimeout(Comm.conn_timeout)
    try:
      Comm.sock.connect()
    except commError as e: 
      self.conn_status.emit(Comm.DISCONNECTED, "")
      self.conn_status.emit(Comm.ERR_CONNECTION, str(e))
      return (time.time(), False)

    print("Is connected.")
    Comm.sock.settimeout(Comm.timeout)
    self.conn_status.emit(Comm.CONNECTED, "")   
    return (time.time(), True)


  def _ReadItem(self):
    """ Waits for n number of bytes and return them. Or return None upon timeout. """  
    data      = bytearray() # Recieved byte storage
    requested = 11  # Fetch at least 11 bytes. Get more later if needed.
    recieved  = 0   # Number of bytes recieved
    fragment  = ''  # Byte fragment recieved 

    try:
      fragment = Comm.sock.recv(requested)
    except commError as err:
      errstr = "%s\nRecieved %d of %d bytes." % (str(err), recieved, requested)
      self.conn_status.emit(Comm.ERR_TIMEOUT, errstr)   
      return None

    recieved += len(fragment)
    data.extend(fragment)

    m = ord(fragment[0])
    if m==MODE.CONFIG_IS or m==MODE.CONFIG_OS:
      # Winch should return a 35 byte parameter instead of a 11 byte sample. 
      requested += 24 # Expect a parameter with length 35 bytes
      
    while recieved<requested:
      # Fetch all remaining bytes
      try:
        fragment = Comm.sock.recv(requested-recieved)
      except commError as err:
        errstr = "Error: %s.\nRecieved %d of %d bytes." % (str(err), recieved, requested)
        #print errstr
        self.conn_status.emit(Comm.ERR_TIMEOUT, errstr)   
        return None
        
      recieved += len(fragment)
      data.extend(fragment)


    if len(data)==11:
      o = Sample()
    elif len(data)==35:
      o = Parameter()
    else:
      raise Exception("Cannot intrepret data. Unknown length %d." % len(data))
      
    o.Parse(data)
    return o


  def _PollWinsch(self, c):
    """ Send a command to the winsch and return the result. The result may be
    a Sample, Parameter or None. None is returned if result cannot be 
    properly parsed or there is a timeout. """

    try:
      Comm.sock.send(chr(c))
    except commError as e:
      errstr = "Send error. %s" % (str(e))
      self.conn_status.emit(Comm.ERR_TIMEOUT, errstr)   
      return None
      
    o = self._ReadItem()

    if isinstance(o, Sample) or isinstance(o, Parameter):
      try:
        self.q_result.put(o, True, 1.0)
      except queue.Full:
        print("Result queue full")
        return None
      self.result_rx.emit()
      return o
    else:
      return None
          
    
  def Sync(self):
    """ Fetch parameters from winsch. """
    
    o = self._PollWinsch(CMD.SET)
    if not isinstance(o, Parameter):
      self.conn_status.emit(Comm.ERR_SYNC, "Parameter sync error. Unknown data recieved.")
      return
      
    p_set = {}
    while (o.data["index"] not in p_set):
      p_set[o.data["index"]] = o
      o = self._PollWinsch(CMD.SET)
    
    Sample.p_drum = p_set[0]    
    Sample.p_pump = p_set[1]    
    Sample.p_temp = p_set[2]    
    #Sample.p_pres = p_set[]    
      
    print("Sync done!")
      
