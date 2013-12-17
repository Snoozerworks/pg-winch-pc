#!/usr/bin/python3.2
# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 20:42:16 2013

@author: Markus
"""

import sys
from PyQt4 import QtCore, QtGui
from AppUI import Ui_MainWindow
import winchComm as vs
from winchCommObjects import Sample, Parameter
import dataLog as log
import os
import fnmatch
import queue

GRAPH_LEN = 50  


class StartQT4(QtGui.QMainWindow):
  
  def __init__(self, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)

    # Setup the datalog
    self.log = log.DataLog(10000)    # 10000 records to save
    
    # Connect gui buttons
    self.ui.btn_get.clicked.connect(lambda : self.on_btn_click(0))
    self.ui.btn_set.clicked.connect(lambda : self.on_btn_click(1))
    self.ui.btn_up.clicked.connect(lambda : self.on_btn_click(2))
    self.ui.btn_down.clicked.connect(lambda : self.on_btn_click(3))
    self.ui.btn_sync.clicked.connect(lambda : self.on_btn_click(4))
    self.ui.btn_save.clicked.connect(lambda : self.on_btn_click(5))
    self.ui.btn_load.clicked.connect(lambda : self.on_btn_click(6))

    # Connect graph line checkboxes
    self.ui.chk_pump.clicked.connect(lambda checked: self.on_show_line(0, checked))
    self.ui.chk_drum.clicked.connect(lambda checked: self.on_show_line(1, checked))
    self.ui.chk_temp.clicked.connect(lambda checked: self.on_show_line(2, checked))
    self.ui.chk_pres.clicked.connect(lambda checked: self.on_show_line(3, checked))
    
    # Connect slider
    self.ui.hslider.valueChanged.connect(self.on_slider_changed)

    # Parameter list    
    self.ui.lst_params.itemSelectionChanged.connect(self.on_lst_selected) 
    
    # Create communication thread    
    self.bt = vs.Comm(self)
    self.bt.result_rx.connect(self.on_result_received)
    self.bt.conn_status.connect(self.on_connection)
    #self.bt.conn_status[int, 'QString'].connect(self.on_connection)
    self.bt.start()
    
    # Create graph
    self.ui.graph.setDataSource(self.log)
    self.ui.graph.setRange(0,0)
    self.ui.graph.updateY()
        
    # Check for saved .npz files.
    self.getFileCount()    
    

  def getFileCount(self):
    """ Count the number of .npz files in the log directory. """
    basedir   = os.path.dirname(os.path.abspath(__file__))
    filecount = 0
    for file in os.listdir("{}/log".format(basedir)):
      if fnmatch.fnmatch(file, '*.npz'):
        filecount += 1
    self.ui.spinBox.setMaximum(filecount)
    self.ui.btn_load.setEnabled( (filecount>0) )
    return filecount

  
  def on_slider_changed(self, v):
    self.ui.graph.setRange(v, GRAPH_LEN)
    self.ui.graph.updateY()


  def on_lst_selected(self):
    if len(self.ui.lst_params.selectedItems())>0:
      item = self.ui.lst_params.selectedItems()[0]
      item = item.data(QtCore.Qt.UserRole)      
      index,ok = item.toInt() 
      # Show parameter in gui 
      self.showParam(self.log.params[index])
      

  def on_btn_click(self, btn_no):
    if btn_no==0: # get
      if self.ui.btn_get.isChecked():
        self.queue_command(vs.CMD.GET)
      return

    if btn_no==1: # set
      self.queue_command(vs.CMD.SET)
      return
    
    if btn_no==2: # up
      self.queue_command(vs.CMD.UP)
      return
    
    if btn_no==3: # down
      self.queue_command(vs.CMD.DOWN)
      return
    
    if btn_no==4: # sync
      self.queue_command(vs.CMD._SYNC)
      return
      
    if btn_no==5: # save
      fname = self.log.Save()
      self.getFileCount()
      self.ui.statusbar.showMessage(fname)
      self.ui.btn_load.setEnabled(True) 
      return
    
    if btn_no==6: # load
      fname = self.log.Load(self.ui.spinBox.value())
      if fname=="":
        self.ui.statusbar.showMessage("Error loading file") 
        return
      self.ui.statusbar.showMessage(fname)
      
      for i in self.log.params:
        print(self.log.params[i])
        self._addParamToList(self.log.params[i])
      
      self.ui.hslider.setMaximum(max(0,self.log.length-GRAPH_LEN))
      self.ui.graph.setRange(0, GRAPH_LEN)
      self.ui.graph.updateY()
      return
      
  
  
  def on_show_line(self, lineno, visible):
    self.ui.graph.showLine(lineno, visible)
   

  def queue_command(self, cmd):
    try:  
      self.bt.q_command.put(cmd, False)
    except queue.Full:
      self.ui.txt_status.appendPlainText("Command que full")
          

  def set_status(self, msg):
    self.ui.txt_status.setPlainText(msg)


  def on_result_received(self):
    r = self.bt.q_result.get(True, 2.0)
    if isinstance(r, Sample):
      self.log.addSample(r)
      #self.ui.txt_status.setPlainText( unicode(str(r),'utf-8') )
      self.ui.txt_status.setPlainText( str(r) )
      
      self.ui.hslider.setMaximum(max(0,self.log.length-GRAPH_LEN))
      v = self.ui.hslider.value()
      self.ui.graph.setRange(v, GRAPH_LEN)
      self.ui.graph.updateY()
      self.on_btn_click(0)  # Get button click

    elif isinstance(r, Parameter):
      self.showParam(r)
      if self.log.addParameter(r):
        self._addParamToList(r)
    
    else:
      print("Recieved unknown data")


  def _addParamToList(self, p):
    txt = "%d - %s" % (p["index"], p["descr"])
    item = QtGui.QListWidgetItem(self.ui.lst_params)
    item.setData(QtCore.Qt.DisplayRole, txt)
    item.setData(QtCore.Qt.UserRole, int(p["index"]))
    

  def showParam(self, p):
    self.ui.spnbox_param.setRange(p["low"], p["high"])
    self.ui.spnbox_param.setSingleStep(p["step"])
    self.ui.spnbox_param.setValue(p["val"])
    #self.ui.lbl_descr.setText("%d - %s" % (p["index"], unicode(p["descr"], 'utf-8')))
    self.ui.lbl_descr.setText("%d - %s" % (p["index"], p["descr"]))
    self.ui.label_3.setText( str(p["val"]) )
    self.ui.lbl_lim.setText("[%d, %d]" % (p["low"], p["high"]))
    self.ui.lbl_step.setText( str(p["step"]) )


  def on_connection(self, status, errtxt=""):
    if status==vs.Comm.DISCONNECTED:
      self.ui.txt_status.appendPlainText("Disconnected")
    elif status==vs.Comm.CONNECTED:
      self.ui.txt_status.appendPlainText("Connected")
    elif status in (vs.Comm.ERR_CONNECTION, vs.Comm.ERR_TIMEOUT, vs.Comm.ERR_SYNC):
      #errtxt = unicode(errtxt, 'utf-8')  # linux?
      #errtxt = unicode(errtxt, 'latin1')
      self.ui.txt_status.appendPlainText("Connection failed. %s" % errtxt)


  def closeEvent(self, event):
    self.queue_command(vs.CMD._CLOSE)
    


if __name__ == "__main__":
  if len(sys.argv)>1:
    vs.Comm.SIMULATE = True # Simulate bluetooth device
    
  app = QtGui.QApplication(sys.argv)
  myapp = StartQT4()
  myapp.show()
  sys.exit(app.exec_())