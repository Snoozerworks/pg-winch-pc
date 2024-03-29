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
	TACH_ENGINE = 3
	PRES = 4
	TEMP = 5


class TimePlot(PlotWidget):
	"""
	A PlotWidget which uses dataLog as a data source.  
	"""

	def __init__(self, params):
		super(TimePlot, self).__init__(params);
		self.signals = [PlotSignals.TACH_DRUM,
						PlotSignals.TACH_PUMP,
						PlotSignals.TACH_ENGINE,
						PlotSignals.PRES,
						PlotSignals.TEMP]
		self._log = DataLog(1)
		self._disp_offset = 0
		self._disp_length = 1
		self.showGrid(True, True)


	def setDataLog(self, log):
		self._log = log;
		self._log.sigSampleAdded.connect(self.updateGraph);
		self.setDisplayRange(0, log.length)
		self.updateGraph();


	def setDisplayRange(self, offset, length):
		"""
		Sets range of samples to display.
		Displays length number of samples with first sample according to offset.
		The offset will be adjusted within [0, length-1].
		The length will be adjusted within [1, length of log - display offset].    
		"""
		self._disp_offset = offset
		self._disp_length = length
		self.setYRange(0, 100)


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
		o = max(0, min(self._disp_offset, self._log.size - 2))
		l = max(1, min(self._disp_length, self._log.size - o))
		
		self.setXRange(o, l)

		self.getPlotItem().clear()
		if PlotSignals.TACH_DRUM in self.signals:
			self.getPlotItem().plot(self._log.samples["drum_spd"], pen={'color': (1, 5), "width": 3});
		if PlotSignals.TACH_PUMP in self.signals:
			self.getPlotItem().plot(self._log.samples["pump_spd"], pen={'color': (2, 5), "width": 3});
		if PlotSignals.TACH_ENGINE in self.signals:
			self.getPlotItem().plot(self._log.samples["engine_spd"], pen={'color': (3, 5), "width": 3});
		if PlotSignals.PRES in self.signals:
			self.getPlotItem().plot(self._log.samples["pres"], pen={'color': (4, 5), "width": 3});
		if PlotSignals.TEMP in self.signals:
			self.getPlotItem().plot(self._log.samples["temp"], pen={'color': (5, 5), "width": 3});
