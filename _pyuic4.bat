@echo off
SET WINPYDIR=C:\WinPython-64bit-3.3.2.3\python-3.3.2.amd64
:: %WINPYDIR%\python.exe "%WINPYDIR%\Lib\site-packages\PyQt4\uic\pyuic.py" %1 %2 %3 %4 %5 %6 %7 %8 %9
%WINPYDIR%\python.exe "%WINPYDIR%\Lib\site-packages\PyQt4\uic\pyuic.py" AppUI.ui > AppUI.py