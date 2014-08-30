# -*- coding: utf-8 -*-
"""
Created on Tue Aug 13 22:46:21 2013

@author: Markus
"""

#
# C code constants
#
#
# namespace C {
# // Running modes
# const byte MD_NOMODE = 0; // Undefined mode.
# const byte MD_STARTUP = 1; // Startup checks
# const byte MD_CONFIG_IS = 2; // Set parameters (config)
# const byte MD_CONFIG_OS = 3; // Set parameters (operation)
# const byte MD_IDLE = 4; // Winch in stand by (lever in neutral)
# const byte MD_TOWING = 5; // In towing operation (lever not in neutral)
# 
# // Commands
# const byte CM_NOCMD = 0; // No command
# const byte CM_SE = 1; // Select switch active
# const byte CM_UP = 2; // Up switch active
# const byte CM_DN = 3; // Down switch active
# const byte CM_SP = 4; // Set parameter (virtual) switch active
# const byte CM_GT = 5; // Get sample (virtual) switch active
# const byte _CM_LAST = CM_GT; // Last element. Used internally only.
# 
# // State of switches are saved in a structure.
# const byte SW_NE = 1; // Neutral switch
# const byte SW_SE = 2; // Select switch
# const byte SW_UP = 4; // Up switch
# const byte SW_DN = 8; // Down switch
# const byte SW_SP = 16; // Set parameter (virtual) switch
# const byte SW_GT = 32; // Get sample (virtual) switch
# const byte SW_IS = 64; // Installation settings (virtual) switch
# 
# // State of errors are saved in a structure.
# const byte ERR_TEMP_HIGH = 1; // Above high temperature limit
# const byte ERR_TEMP_LOW = 2; // Below low temperature limit
# const byte ERR_DRUM_MAX = 4; // Drum speed exceeded
# const byte ERR_TWI = 8; // TWI bus error
# const byte ERR_PUMP_SENSOR = 16; // Pump sensor fault
# const byte ERR_DRUM_SENSOR = 32; // Drum sensor fault
# }
#



class _SimplePair():
	
	def __init__(self, code, name):
		if code < 0 or code > 255:
			raise ValueError 
		self.code = code
		self.name = name
	
	def __eq__(self, other):
		return isinstance(other, _SimplePair) and other.code == self.code 
	
# 	def __bytes__(self):
# 		return bytes([self.code]);
	
	def __str__(self):
		return "{.name} ({.code:3d})".format(self)
	
	
class Command(_SimplePair):
	def __eq__(self, other):
		return isinstance(other, Command) and other.code == self.code 
	

class Mode(_SimplePair):
	def __eq__(self, other):
		return isinstance(other, Mode) and other.code == self.code 
	
	

# const byte CM_NOCMD = 0; // No command
# const byte CM_SE = 1; // Select switch active
# const byte CM_UP = 2; // Up switch active
# const byte CM_DN = 3; // Down switch active
# const byte CM_SP = 4; // Set parameter (virtual) switch active
# const byte CM_GT = 5; // Get sample (virtual) switch active


class Commands():
	""" Collection of constants for commands """
	_CLOSE	 = Command(100, "_CLOSE");
	_SYNC	 = Command(101, "_SYNC");
		
	NOCMD	 = Command(0, "NOCMD");
	SE		 = Command(1, "SELECT");
	UP		 = Command(2, "UP")
	DN		 = Command(3, "DOWN")
	SP		 = Command(4, "SET PARAMETER")
	GT		 = Command(5, "GET")


class Modes():
	""" Collection of constants for mode """
	NOMODE		 = Mode(0, "NOMODE")
	STARTUP		 = Mode(1, "STARTUP")
	CONFIG_IS	 = Mode(2, "CONFIG_IS")
	CONFIG_OS	 = Mode(3, "CONFIG_OS")
	IDLE		 = Mode(4, "IDLE")
	TOWING		 = Mode(5, "TOWING")
	
	_mode_dict = {NOMODE.code : NOMODE,
				STARTUP.code : STARTUP,
				CONFIG_IS.code : CONFIG_IS,
				CONFIG_OS.code : CONFIG_OS,
				IDLE.code : IDLE,
				TOWING.code : TOWING}
	

	@staticmethod
	def getMode(m):
		"""
		Return mode as specified by m. Returns NOMODE if m is invalid.
		m integer:
			Value of mode 
		"""
		mode = Modes._mode_dict.get(m);
		if mode==None:
			return Modes.NOMODE
		
		return mode
		

# Texts for modes 
MODE_TXT = (
 "Okänt läge!",
 "Uppstart",
 "Inställlningar - installation",
 "Inställningar - drift",
 "Vänteläge",
 "Dragläge")
