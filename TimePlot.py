'''
Created on 21 aug 2014

@author: markus
'''

from enum import Enum, unique
from pyqtgraph import PlotWidget
from dataLog import DataLog

@unique
class PlotSignals(Enum):
    TACH_PUMP = 1
    TACH_DRUM = 2
    PRES = 3
    TEMP = 4
    

class TimePlot(PlotWidget):
    """
    A PlotWidget which uses dataLog as a data source.  
    """    

    def __init__(self, params):
        super(TimePlot, self).__init__(params);
        self.signals = [PlotSignals.TACH_DRUM,
                        PlotSignals.TACH_PUMP,
                        PlotSignals.PRES,
                        PlotSignals.TEMP]
        self._log = DataLog(1);

        
    def setDataLog(self, log):
        self._log = log;
        self._log.sigSampleAdded.connect(self.updateGraph);
        self.updateGraph();
        

    def show_signal(self, signal, disp=True):
        """
        Show signals named in signals.
        :type signals: list
        """
        if disp and signal not in self.signals:
            self.signals.append(signal)
        elif not disp and signal in self.signals:
            self.signals.remove(signal)
        
        
    def updateGraph(self):
        self.getPlotItem().clear()
        if PlotSignals.TACH_DRUM in self.signals:
            self.getPlotItem().plot(self._log.samples["drum_spd"], pen={'color': (1,4), "width": 3});
        if PlotSignals.TACH_PUMP in self.signals:
            self.getPlotItem().plot(self._log.samples["pump_spd"], pen={'color': (2,4), "width": 3});
        if PlotSignals.PRES in self.signals:            
            self.getPlotItem().plot(self._log.samples["pres"], pen={'color': (3,4), "width": 3});
        if PlotSignals.TEMP in self.signals:            
            self.getPlotItem().plot(self._log.samples["temp"], pen={'color': (4,4), "width": 3});
        
