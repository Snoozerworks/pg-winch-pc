# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 21:52:20 2013

@author: Markus
"""
#import time
from guiqwt.plot import CurveWidget
from guiqwt.builder import make 
 
class myCurveWidget(CurveWidget):
 
  def __init__(self, parent=None):
    super(myCurveWidget, self).__init__(parent)
        
    self.x = []    
    self.source = None
    self.lines = [None,None,None,None]

    colors = ("r", "g", "b", "y")
    
    for i in range(4):
      self.lines[i] = make.curve([], [], 
      title="curve %d" % i, 
      color=colors[i],
      linewidth=4.0)
      self.plot.add_item(self.lines[i])     
      
      
  def setRange(self, offset, length):
    self.x = self.source.getRange(offset, length)

    
  def setDataSource(self, d):
    self.source = d
    
    
  def updateY(self):
    #t0 = time.time()
    x = list(self.x)
    self.lines[0].set_data(x, self.source.data[x]["tach_pump"])
    self.lines[1].set_data(x, self.source.data[x]["tach_drum"])
    self.lines[2].set_data(x, self.source.data[x]["pres"])
    self.lines[3].set_data(x, self.source.data[x]["temp"])
#    print ("Draw 0 dt=%f" % (time.time()-t0))
    self.plot.show()
    self.plot.replot()
    self.plot.do_autoscale()
#    print("Draw 1 dt=%f" % (time.time()-t0))


  def showLine(self, line, show):
    self.lines[line].setVisible(show)
    self.plot.replot()    
    #self.lines[line].set_visible(show)      
    #self.canvas.draw()
    
