# -*- coding: utf-8 -*-

import os
import locale
import sys
import numpy as np
from arduino.package import Sample, Parameter
from PyQt4 import QtCore
from PyQt4.QtCore import QObject, QModelIndex
from PyQt4.Qt import Qt
from numpy import select
from _datetime import datetime

# import from PyQt4.Qt as Qt
# from guidata.qt import QtCore


class DataLog(QObject):
	""" Keeps data to plot """

	sigSampleAdded	= QtCore.pyqtSignal();
	sigParamAdded	= QtCore.pyqtSignal();
	sigParamChange	= QtCore.pyqtSignal(int, int);  # index, value


	def __init__(self, size):
		super().__init__()

		self.size		= size  # max number of samples in record
		self.length		= 0  # current number of samples in record
		self.samples	= np.zeros(self.size, dtype=Sample.data_type)
		self.recordno	= 0
		self.params 	= {}  # Dict of parameters with index as key
		self._param_keys= []  # List of sorted parameter indices in .params
		self.reset()
		self.param_mdl	= dataParamModel(self)


	def addSample(self, sample):
		""" Add a winch sample to the log.
		
		:param sample: The sample to add. 
		:type sample: Sample
		"""
		self.length = min(self.length + 1, self.size)

		# Forward data by one...
		self.samples = np.roll(self.samples, 1, 0)

		# ...then prepend the new sample
		self.samples[0] = sample.data

		# Emit the sigSampleAdded signal
		self.sigSampleAdded.emit();


	def addParameter(self, param):
		""" Add or update a winch parameter to the log.
		
		:param param: Parameter to add. 
		:type param: Parameter
		"""
		self.params[param['index']] = param
		self._param_keys = sorted(self.params.keys())
		self.sigParamAdded.emit();


	def getParameter(self, index):
		""" Get parameter with specified index.
		
		:param index: Parameter index.
		:rtype: Parameter
		"""
		return self.params[index]

	def updateParameter(self, index, value):
		""" Update parameter value.
		
		:type index: uint8
		:type value: int16
		"""
		if index not in self.params: return False
		raw = self.params[index].mapval_inv(value)
		self.sigParamChange[int, int].emit(index, raw)


	def reset(self):
		""" Empty the samples log. """
		# self.params = {}
		self.length	 = 0  # current number of samples in record


# 	def getRange(self, offset=0, length=50):
# 		""" Return a valid range (inside the bounds) to use on data. 
# 		
# 		:param offset: Offset in log.
# 		:param length: Max number of items to include.
# 		:type offset: int
# 		:type length: int 
# 		"""
# 		i0 = max(0, min(offset, self.length - length))
# 		i1 = min(i0 + length, self.length)
# 		return range(i0, i1)


	def Save(self):
		""" Save log to disk. """
		self.recordno += 1
		now = datetime.today()
		path = "{}/log".format(sys.path[0])
		fname = "{}/rec_{}.csv".format(path, now.strftime("%Y%m%dT%H%M%S"))
		print("Save %d samples in file %s" % (self.length, fname))

		try:
			os.makedirs(path)
		except OSError as exception:
			if exception.errno != os.errno.EEXIST:
				raise
			# Directory already exists


		with open(fname, mode='wt', encoding='utf-8') as f:
			f.write(Parameter.csvHeader());
			for i in self.params:
				f.write(self.params[i].to_csv())
				f.write("\n")

			f.write("\n")
			
			f.write(Sample.csvHeader());
			for sample in self.samples:
				S = Sample(sample)
				f.write(S.to_csv())
				f.write("\n")

		# np.savez(fname, samples=self.samples[0:self.length], parameters=self.params)
		return fname


# 	def Load(self, fileno):
# 		""" Load a log from disk given the number of the log.
#
# 		:param fileno: File number to load.
# 		:type fileno: int
# 		"""
# 		fname = "{}/log/record_{:03d}.npz".format(sys.path[0], fileno)
# 		try:
# 			d = np.load(fname)
# 		except IOError:
# 			print("Error loading file %s" % fname)
# 			return ""
#
# 		self.reset()
# 		self.params = d["parameters"].item()
#
# 		for s in d["samples"]:
# 			self.addSample(s)
# 		print("Loaded %d samples and %d parameters" % (d["samples"].size, d["parameters"].size))
# 		return fname




class dataParamModel(QtCore.QAbstractTableModel):
	# Column number of value field
	EDITABLE_COL_NO = 1

	def __init__(self, log):
		super().__init__()
		self.log = log
		log.sigParamAdded.connect(self._on_added_param)

	def _on_added_param(self):
		self.reset()

	# int QAbstractItemModel::rowCount ( const QModelIndex & parent = QModelIndex() ) const [pure virtual]
	def rowCount(self, parent=QModelIndex()):
		if parent.isValid():
			return 0
		else:
			return len(self.log.params)

	# int QAbstractItemModel::columnCount ( const QModelIndex & parent = QModelIndex() ) const [pure virtual]
	def columnCount(self, parent=QModelIndex()):
		if parent.isValid(): return 0
		return 4

	# QVariant QAbstractItemModel::data ( const QModelIndex & index, int role = Qt::DisplayRole ) const [pure virtual]
	def data(self, index, role=Qt.DisplayRole):
		"""
		:type index: QModelIndex
		"""

		r = index.row()
		c = index.column()
		index = self.log._param_keys[r]

		if role == Qt.DisplayRole or role == Qt.EditRole:
			p = self.log.getParameter(index)

			if c == 0:
				return p["descr"]
			elif c == 1:
				return "{:0.1f}".format(p.mapval(p["val"]))
			elif c == 2:
				return "[{:d}, {:d}]".format(p["low_map"], p["high_map"])
			elif c == 3:
				return "{:0.1f}".format(p.mapval(p["step"]))
			else:
				return None
		else:
			return None


	# QVariant QAbstractItemModel::headerData ( int section, Qt::Orientation orientation, int role = Qt::DisplayRole ) const [virtual]
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			if section == 0:
				return "Namn"
			elif section == 1:
				return "Värde"
			elif section == 2:
				return "[Min, Max]"
			elif section == 3:
				return "Steg"
			else:
				return None
		else:
			return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)


	# bool QAbstractItemModel::setData ( const QModelIndex & index, const QVariant & value, int role = Qt::EditRole ) [virtual]
	def setData(self, index, value, role=Qt.EditRole):
		"""
		Called when data edited in table.
		
		:param index: Model index.
		:type index: int
		:param value: Value at index.
		:type value: object
		:param role: Model role.
		:type role: Qt.WditRole
		:return: Always false.  
		:rtype: bool
		"""
		try:
			value = locale.atof(value)
		except ValueError:
			return False
		k = self.log._param_keys[index.row()]
		self.log.updateParameter(k, value)
		return False


	# Qt::ItemFlags QAbstractItemModel::flags ( const QModelIndex & index ) const [virtual]
	def flags(self, index):
		':type index: QModelIndex'
		':rtype : ItemFlags'
		f = QtCore.QAbstractTableModel.flags(self, index)
		if index.column() == dataParamModel.EDITABLE_COL_NO:
			return f | Qt.ItemIsEditable | Qt.ItemIsSelectable
		else:
			return Qt.NoItemFlags


	# bool QAbstractItemModel::insertRows ( int row, int count, const QModelIndex & parent = QModelIndex() ) [virtual]
	def insertRows(self, row, count, parent=QModelIndex()):
		if parent.isValid():
			return False

		self.beginInsertRows()
		pass
		self.endInsertRows()


