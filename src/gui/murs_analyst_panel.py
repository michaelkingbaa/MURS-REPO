#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
__author__ = "Mitchell Jones"

import sys
import json
import math

import numpy as np
import zmq
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.ptime import time
import time	

from spectra import SpectraWidget, spectra_update
from waterfall import WaterfallWidget, waterfall_update
from gross_counts import GrossCountsWidget, gross_counts_update
from direction import DirectionWidget, direction_update
from metric import MetricWidget, metric_update

# Forces print function to print entire np array
np.set_printoptions(threshold=np.nan)	

class StartButtonWidget(QtGui.QWidget):

	def __init__(self):
		QtGui.QWidget.__init__(self)
		self.startBtn = QtGui.QPushButton('Start Data Acquisition', self)
		self.startBtn.clicked.connect(self.start)
		layout = QtGui.QVBoxLayout(self)
		layout.addWidget(self.startBtn)

	def start(self):
		pressed = True;
		print 'Pressed'

def update():
	spectra_update(spectra)
	gross_counts_update(gross_counts)
	direction_update(direction)
	metric_update(metric)
	waterfall_update(waterfall)
	app.processEvents()  

app = QtGui.QApplication(sys.argv)

w = QWidget()
w.resize(1400, 700)
w.setWindowTitle("MURS Analyst Panel")

# Set pyqtgraph to use white background/black foreground
# It defaults to black background/white foreground otherwise
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# Set widget variable names for grid layout
waterfall_list = QComboBox(w)
metric_list = QComboBox(w)
spectra = SpectraWidget()
gross_counts = GrossCountsWidget()
direction = DirectionWidget()
metric = MetricWidget()
waterfall = pg.ImageView(view=WaterfallWidget())
start_button = StartButtonWidget()

# Sets minimum size of each element
spectra.setMinimumSize(550,300)
gross_counts.setMinimumSize(300,300)
direction.setMinimumSize(300,300)
metric.setMinimumSize(300,300)
waterfall.setMinimumSize(550,300)

# Waterfall thread dropdown list
waterfall_list.addItem("Thread 1")
waterfall_list.addItem("Thread 2")
waterfall_list.addItem("Thread 3")
waterfall_list.addItem("Thread 4")
waterfall_list.addItem("Thread 5")
waterfall_list.addItem("Thread 6")

# Metrics dropdown list
metric_list.addItem("Metric 1")
metric_list.addItem("Metric 2")
metric_list.addItem("Metric 3")
metric_list.addItem("Metric 4")
metric_list.addItem("Metric 5")
metric_list.addItem("Metric 6")

# Create a grid layout to manage the widgets size and position
layout = QtGui.QGridLayout()
w.setLayout(layout)

# Add widgets to the layout in their proper positions
layout.addWidget(waterfall_list, 0, 0, 1, 1)
layout.addWidget(metric_list, 0, 3, 1, 1)
layout.addWidget(waterfall, 1, 0, 1, 1)
layout.addWidget(spectra, 2, 0, 1, 1)
layout.addWidget(gross_counts, 1, 1, 1, 1)
layout.addWidget(direction, 1, 2, 1, 1)
layout.addWidget(metric, 1, 3, 1, 1)
layout.addWidget(start_button, 2, 1, 1, 3)
# (widget_name, row, column, rows spanned, columns spanned)

#spectra.line
#gross_counts.line
#direction.line
#metric.line

'''
#For sending button messages
port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = '1001'
'''

# Timer to update plots
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0.5)

if __name__ == '__main__':
	w.show()
	if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
		QtGui.QApplication.instance().exec_()
		
	app.exec_()
