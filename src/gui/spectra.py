#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
__author__ = "Mitchell Jones"

import sys
import json

import numpy as np
import zmq
from PyQt4.QtGui import *
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
from pyqtgraph.ptime import time
import time

from kafka_global import *


class SpectraWidget(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self)

        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Spectra')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Counts')
        # axis.setLogMode(True)
        self.setLogMode(y=True)

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Channel')

    # self.line = self.plot()


def spectra_update(spectra):
    dict = get_data()
    if dict == 'STOP':
        exit()
    color_mask = ['w', 'b', 'g', 'y', 'r', 'm']

    for i, key in enumerate(dict.keys()):
        if key not in data.keys():
            data[key] = np.zeros(1024)

        data[key] = np.zeros(1024)
        data[key] += dict[key]['spectrum']

        data[key][data[key] == 0] = -1
        data[key] = np.log10(data[key])
        data[key] = data[key][:511]

        if i == 0:
            spectra.clear()

        spectra.addItem(pg.PlotCurveItem(data[key], pen=color_mask[i]))


def get_data():
    data_msg = consumer.next()

    if data_msg.value != 'STOP':
        dict = data_handler.decode(data_msg.value)
    else:
        return 'STOP'

    return dict


data = {}
time = {}
total_counts = {}

# KAFKA consumer
# wanted_client = '192.168.0.101:9092'
# data_schema = '../messaging/mursArray.avsc'
# data_topic = 'data_messages'

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
