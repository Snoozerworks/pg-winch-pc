'''
Created on 22 aug 2014

@author: markus
'''


import time
import numpy as np
from arduino.constants import MODE_TXT

from builtins import int


class _avgBuffer():
	def __init__(self, v, length):
		self.buf = [v / length] * length
		self.ind = 0
		self.len = int(length)
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

	SIZE = data_type.itemsize

	def __init__(self, data=None):
		""" Initialize parameter values. """
		self.raw = [(0, 0, 0, 0, 1, 0, 1, 1, "")]  # Init parameter values
		self.data = np.array(self.raw, Parameter.data_type)
		self._descr = ""
		if data != None:
			self.Parse(data);


	def __getitem__(self, i):
		if i == "descr" :
			return self._descr
		else:
			return self.data[i]


	def Parse(self, data):
		""" Interpret the raw bytes received from the Arduino, and copy values to 
		the Parameter properties accordingly. """

		# Get the data record
		self.raw = bytes(data)
		self.data = np.frombuffer(self.raw, Parameter.data_type, 1, 0)[0]

		s = self.data["descr"]
		s = s.replace(b'\x00', ''.encode())
		s = s.replace(b'\x80', 'å'.encode())
		s = s.replace(b'\xE1', 'ä'.encode())
		s = s.replace(b'\xEF', 'ö'.encode())
		s = s.replace(b'\x81', 'Å'.encode())
		s = s.replace(b'\x82', 'Ä'.encode())
		s = s.replace(b'\x83', 'Ö'.encode())
		self._descr = s.decode()


	def mapval(self, v):
		""" Returns a value v mapped from (low,hi) to (low_map,high_map) 
		using linear interpolation. If high=low method returns 0."""
		if self.data["low"] == self.data["high"]:
			return 0

		lo = self.data["low"] * 1.0
		hi = self.data["high"] * 1.0
		to_lo = self.data["low_map"] * 1.0
		to_hi = self.data["high_map"] * 1.0

		return to_lo + (v - lo) * (to_hi - to_lo) / (hi - lo)


	def mapval_inv(self, v):
		""" Returns a value mapped from (low_map,high_map) to (low,high)
		using linear interpolation. If high_map=low_map method returns 0.
		If v is outside range (low_map,high_map) then either low or high
		will be returned. 
		
		:type v: float
			Value to map
		:rtype: int
			Mapped value.
		"""
		if self.data["low_map"] == self.data["high_map"]:
			return 0

		if v < self.data["low_map"]: return self.data["low"]
		if v > self.data["high_map"]: return self.data["high"]

		lo = self.data["low_map"] * 1.0
		hi = self.data["high_map"] * 1.0
		to_lo = self.data["low"] * 1.0
		to_hi = self.data["high"] * 1.0

		return int(to_lo + (v - lo) * (to_hi - to_lo) / (hi - lo))


	def to_csv(self):
		""" Return fields as a comma separated string. """
		frmt = "{mode},{index},{val},{low},{high},{step},{low_map},{high_map},{descr}"
		return frmt.format_map(self)


	@staticmethod
	def csvHeader():
		""" Return comma separated headers for csv format """
		return "mode,index,value,low,high,step,low_map,high_map,descr\n"


	def __str__(self):
		""" Returns a string representation of the parameter. """

		frmt = ("Parameter {p[index]:2d} - {p[descr]}\n"
				"	mode\t: {mt} ({p[mode]})\n"
				"	val\t: {vm:6.1f} ({p[val]:4d})\n"
				"	low\t: {lm:6.1f} ({p[low]:4d})\n"
				"	high\t: {hm:6.1f} ({p[high]:4d})\n"
				"	low_map\t: {p[low_map]:4d}\n"
				"	high_map\t: {p[high_map]:4d}\n"
				"	step\t: {sm:6.1f} ({p[step]:4d})\n")
		s = frmt.format(p=self,
						mt=MODE_TXT[self["mode"]],
						vm=self.mapval(self["val"]),
						lm=self.mapval(self["low"]),
						hm=self.mapval(self["high"]),
						sm=self.mapval(self["step"]))
		return s




class Sample():
	""" 
	Represents a sample as received when sending a get request to the 
	Arduino.
	"""

	data_type = np.dtype([  # Data type definition of raw data
		("mode", "u1"),
		("time", ">u4"),
		("errors", "u1"),
		("pump_spd", "u1"),
		("drum_spd", "u1"),
		("engine_spd", "u1"),
		("temp", ">i2"),
		("pres", ">i2")])

	SIZE = data_type.itemsize

	pump_buffer = _avgBuffer(0, 10)  # Average for tacho pump
	drum_buffer = _avgBuffer(0, 10)  # Average for tacho drum
	engine_buffer = _avgBuffer(0, 10)  # Average for tacho engine 
	time_buffer = _avgBuffer(200, 20)  # Average for sample period
	_tx_time = [0, 0]  # Transmitting times
	_rx_time = [time.time(), time.time()]  # Receiving times
	_dt = 0
	p_pump = Parameter()
	p_drum = Parameter()
	p_temp = Parameter()
	p_pres = Parameter()


	def __init__(self, data=None):
		""" 
		Initialize Sample values.
		"""
		initval = [(0, 0, 0, 0, 0, 0, 0)]  # Init sample values
		self.data = np.array(initval, Sample.data_type)
		if data != None:
			self.Parse(data)


	def __getitem__(self, i):
		return self.data[i]


	def Parse(self, data):
		""" Interpret raw bytes as sent from the Arduino representing a sample. """

		self.data = np.frombuffer(buffer=bytes(data), dtype=Sample.data_type, count=1, offset=0)[0]

		Sample._tx_time[1] = Sample._tx_time[0]
		Sample._tx_time[0] = self.data["time"]
		Sample._rx_time[1] = Sample._rx_time[0]
		Sample._rx_time[0] = time.time()

		Sample.pump_buffer.add(self.data["pump_spd"])
		Sample.drum_buffer.add(self.data["drum_spd"])
		Sample.engine_buffer.add(self.data["engine_spd"])
		Sample._dt = (Sample._rx_time[0] - Sample._rx_time[1]) * 1000.0
		Sample.time_buffer.add(Sample._dt)


	def to_csv(self):
		""" Return fields as a comma separated string. """
		frmt = "{time},{mode},{errors},{pump_spd},{drum_spd},{engine_spd},{temp},{pres}"
		return frmt.format_map(self)


	@staticmethod
	def csvHeader():
		""" Return comma separated headers for csv format """
		return "time,mode,errors,pump_speed,drum_speed,engine_speed,temp,pres\n";


	def __str__(self):
		s = "Sample - receive period {:0.0f}({:3.1f})\n".format(Sample._dt, Sample.time_buffer.sum)
		s += "	mode\t\t: {:2d} ({})\n".format(self.data["mode"], MODE_TXT[self.data["mode"]])
		s += "	errors\t\t: {:b}\n".format(self.data["errors"])
		s += "	on time\t\t: {:6d} ms\n".format(self.data["time"])
		s += "	pump speed\t: {:4d}({:4.0f}) rpm\n".format(self.data["pump_spd"], Sample.pump_buffer.sum)
		s += "	drum speed\t: {:4d}({:4.0f}) rpm\n".format(self.data["drum_spd"], Sample.drum_buffer.sum)
		s += "	engine speed\t: {:4d}({:4.0f}) rpm\n".format(self.data["engine_spd"], Sample.engine_buffer.sum)
		s += "	period\t\t: {:4.0f} ms\n".format(Sample._tx_time[0] - Sample._tx_time[1])
		s += "	temperature\t: {:4.0f} deg C\n".format(self.data["temp"])
		s += "	pressure\t\t: {:4.0f} bar\n".format(self.data["pres"])
		return s
