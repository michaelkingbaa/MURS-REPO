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

from kafka_global import *


class WaterfallWidget(pg.PlotItem):

    def __init__(self):
        pg.PlotItem.__init__(self)
        
        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Waterfall')
        
        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Time')

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('E')

def enum():
    global spectrum, time_range, channels, num_detectors, img_len
    
    dict = get_data()
    if dict == 'STOP':
        exit()
    spectrum = []
    for i, key in enumerate(dict.keys()):
        if key not in ind_spectrum.keys():
            ind_spectrum[key] = np.zeros(channels)

        ind_spectrum[key] = dict[key]['spectrum']
        ind_spectrum[key] = ind_spectrum[key][:channels]
        
        spectrum = np.append(spectrum, ind_spectrum[key])
        
        if len(spectrum) == img_len:
            return spectrum
    
def waterfall_update(waterfall):
    global data, rgb_data, time_range, channels, num_detectors, img_len

    rgb_data = np.zeros((img_len,1,3))
    
    spectrum = enum()
    spec_max = np.amax(spectrum)				# Finds max value in spectrum
    spec_max = float(spec_max)					# Converts value to float

    spectrum = np.divide(spectrum, spec_max)	# Normalizes data to 0-1 float values
    spectrum = spectrum.reshape(img_len,1)		# Reshape data to vertical array for plotting

    # Color Map: Dark blue -> Green -> Yellow -> Orange -> Red
    pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    color = np.array([[0,0,128], [0,255,0], [255,255,0], [255,128,0], [255,0,0]], dtype=np.ubyte)
    cm = pg.ColorMap(pos, color)
    # print cm.getLookupTable(0.0, 1.0, spec_max)

    rgb_data = cm.map(spectrum, mode='byte')	# Maps color to RGB array
    rgb_data = rgb_data[:,0,:]					# Takes away third dimension
    
    data = np.roll(data, 1, axis=1)				# Rolls data down
    data[:,0] = rgb_data						# Sets top row to new RGB data
  
    waterfall.setImage(data, autoRange=True)
    waterfall.view.setAspectLocked(False)
    waterfall.show()


def get_data():
    data_msg = consumer.next()
    if data_msg.value != 'STOP':
        dict = data_handler.decode(data_msg.value)
    else:
        return 'STOP'

    return dict

time_range = 200;                               # Set y-axis range
channels = 256;                                 # Obersable channels for each detector
num_detectors = 6;                              # Number of detectors
img_len = channels * num_detectors;

ind_spectrum = {}
data = np.zeros((img_len,time_range,3))
rgb_data = []
spectrum = []
	

#KAFKA consumer
#wanted_client = 'localhost:9092'
#data_schema = '../messaging/mursArray.avsc'
#data_topic = 'data_messages'

while not 'data_messages' in KafkaClient(wanted_client).topic_partitions.keys():
    print 'waiting for data Client'
    time.sleep(1)
    
consumer = KafkaConsumer(data_topic, bootstrap_servers=wanted_client)

data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)

'''
#For sending button messages
port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = '1001'
'''
