# -*- coding: utf-8 -*-

import sys
import numpy as np
from arduino.package import Sample, Parameter
from PyQt4 import QtCore
from PyQt4.QtCore import QObject, QModelIndex
from PyQt4.Qt import Qt

# import from PyQt4.Qt as Qt
# from guidata.qt import QtCore


class DataLog(QObject):
	""" Keeps data to plot """
	
	sigSampleAdded = QtCore.pyqtSignal();
	sigParamAdded = QtCore.pyqtSignal();
	
	def __init__(self, size):
		super().__init__()

		self.size		 = size  # max number of samples in record 
		self.length	 = 0  # current number of samples in record
		self.data		 = np.zeros(self.size, dtype=Sample.data_type) 
		self.recordno = 0
		self.params = {}
		self.reset()
		self.param_mdl = dataParamModel(self)
		
		
	def addSample(self, sample):
		""" Add a winch sample to the log """
		self.length = min(self.length + 1, self.size)
		
		# Forward data by one...
		self.data = np.roll(self.data, 1, 0)
		
		# ...then prepend the new sample
		self.data[0] = sample.data

		# Emit the sigSampleAdded signal 		
		self.sigSampleAdded.emit();


	def addParameter(self, p):
		""" Add/update a winch parameter to the log. """
		self.params[p['index']] = p
		self.sigParamAdded.emit();


	def getParameter(self, index):
		""" Get parameter with specified index. """		
		return self.params[index]
		

	def reset(self):
		""" Empty the samples log. """
		# self.params = {}
		self.length	 = 0  # current number of samples in record


	def getRange(self, offset=0, length=50):
		""" Return a valid range (inside the bounds) to use on data. """
		i0 = max(0, min(offset, self.length - length))
		i1 = min(i0 + length, self.length)
		return range(i0, i1)

							
	def Save(self):
		""" Save log to disk. """
		self.recordno += 1 
		fname = "{}/log/record_{:03d}.npz".format(sys.path[0], self.recordno)
		print("Save %d samples in file %s" % (self.length, fname))
		np.savez(fname, samples=self.data[0:self.length], parameters=self.params)	
		return fname				
	
	
	def Load(self, fileno):
		""" Load a log from disk given the number of the log. """		
		fname = "{}/log/record_{:03d}.npz".format(sys.path[0], fileno)
		try:
			d = np.load(fname)
		except IOError:
			print("Error loading file %s" % fname)
			return ""
				
		self.reset()
		self.params = d["parameters"].item()	 
		
# 		print repr(self.params)
# 		print repr(self.params[0])
			
		for s in d["samples"]:
			self.addSample(s)
		print("Loaded %d samples and %d parameters" % (d["samples"].size, d["parameters"].size))
		return fname
	
		
		
		
class dataParamModel(QtCore.QAbstractTableModel):
	
	# Column number of value field
	EDITABLE_COL_NO = 2
	_header_names 	 = ("Namn", "Värde", "Min", "Max", "Steg")
	_header_fields 	 = ("descr", "val", "low", "high", "step")

	def __init__(self, log):
		super().__init__()
		self.log = log
		log.sigParamAdded.connect(self._on_added_param)  
		
	def _on_added_param(self):
		si = self.index(0, 0)
		ei = self.index(len(self.log.params), len(dataParamModel._header_fields))
		self.reset()
		#self.dataChanged.emit(si,ei)	
		
	# int QAbstractItemModel::rowCount ( const QModelIndex & parent = QModelIndex() ) const [pure virtual]	
	def rowCount(self, parent=QModelIndex()):
		if parent.isValid(): 
			return 0
		else:
			return len(self.log.params)	
	
	# int QAbstractItemModel::columnCount ( const QModelIndex & parent = QModelIndex() ) const [pure virtual]
	def columnCount(self, parent=QModelIndex()):
		if parent.isValid(): return 0
		return len(dataParamModel._header_fields)
	
	# QVariant QAbstractItemModel::data ( const QModelIndex & index, int role = Qt::DisplayRole ) const [pure virtual]	
	def data(self, index, role=Qt.DisplayRole):
		':type index: QModelIndex'
		if role==Qt.DisplayRole or role==Qt.EditRole: 
			c = index.column()
			r = index.row()
			f = dataParamModel._header_fields[c]
			d = self.log.getParameter(r)[f]
			return str(d)
		else:
			return None
		
				
	# QVariant QAbstractItemModel::headerData ( int section, Qt::Orientation orientation, int role = Qt::DisplayRole ) const [virtual]
	def headerData(self, section, orientation, role=Qt.DisplayRole):
		if role == Qt.DisplayRole and orientation == Qt.Horizontal:
			return dataParamModel._header_names[section]
		return QtCore.QAbstractTableModel.headerData(self, section, orientation, role)
		
	
	# bool QAbstractItemModel::setData ( const QModelIndex & index, const QVariant & value, int role = Qt::EditRole ) [virtual]	
	def setData(self, index, value, role=Qt.EditRole):
		':type index: QModelIndex'
		':type value: int'
		self.log.getParameter(index.row())
		self.dataChanged.emit(index,index)
		return True
	
	
	# Qt::ItemFlags QAbstractItemModel::flags ( const QModelIndex & index ) const [virtual]
	def flags(self, index):
		':type index: QModelIndex'
		':rtype : ItemFlags'
		f = QtCore.QAbstractTableModel.flags(self, index)		
		if index.column() == dataParamModel.EDITABLE_COL_NO:
			return f | Qt.ItemIsEditable | Qt.ItemIsSelectable
		else:
			return f
		
	
	# bool QAbstractItemModel::insertRows ( int row, int count, const QModelIndex & parent = QModelIndex() ) [virtual]
	def insertRows(self, row, count, parent=QModelIndex()):
		if parent.isValid():
			return False
	
		self.beginInsertRows()
		pass
		self.endInsertRows()

	
