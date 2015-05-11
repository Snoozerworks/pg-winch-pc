# -*- coding: utf-8 -*-
"""
Created on Mon May 11 22:10:20 2015

Script for py2exe to create windows standalone binary.

@author: Markus
"""

from distutils.core import setup
import py2exe

setup(console=['main.py'])