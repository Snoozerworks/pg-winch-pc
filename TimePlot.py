'''
Created on 21 aug 2014

@author: markus
'''
from pyqtgraph import PlotWidget
from dataLog import DataLog

class TimePlot(PlotWidget):
    """
    A PlotWidget which uses dataLog as a data source.  
    """    

    def __init__(self, params):
        super(TimePlot, self).__init__(params);
        self._log = DataLog(1);

        
    def setDataLog(self, log):
        self._log = log;
        self._log.sigSampleAdded.connect(self.updateGraph);
        self.updateGraph();
        
        
    def updateGraph(self):
        self.getPlotItem().clear()
        self.getPlotItem().plot(self._log.data["tach_pump"]);
        self.getPlotItem().plot(self._log.data["tach_drum"]);
        self.getPlotItem().plot(self._log.data["pres"]);
        
