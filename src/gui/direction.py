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


class DirectionWidget(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self)

        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Direction')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Time')

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Direction')

    # self.line = self.plot()


def direction_update(direction):
    global data, time
    time_range = 20;
    epoch_time = {}
    gm_time = {}
    dict = get_data()
    if dict == 'STOP':
        exit()
    color_mask = ['w', 'b', 'g', 'y', 'r', 'm']
    # if len(time) == 0:
    #	data = np.zeros(time_range)
    #	time = np.zeros(time_range)

    direction_data = dict['direction']
    # time_data = dict['time']
    if np.isnan(direction_data) == True:
        direction_data = 0

    epoch_time = dict['time']
    gm_time = epoch_time - start_time

    # NP Rolling Data
    # data = np.roll(data, -1)
    # data[-1] = direction_data
    # print data
    # time = np.roll(time, -1)
    # time[-1] = int(gm_time)
    # print time

    data.append(direction_data)
    time.append(gm_time)

    if len(time) > time_range:
        data = data[1:]
        time = time[1:]
    direction.addItem(pg.PlotCurveItem(data, time, pen=color_mask[1]))
    print time


def get_data():
    direction_msg = consumer_direction.next()

    if direction_msg.value != 'STOP':
        dict = direction_handler.decode(direction_msg.value)
    else:
        return 'STOP'
    return dict


start_time = time.time()  # current epoch time
data = []
time = []

# KAFKA consumer
# wanted_client = '192.168.0.101:9092'
# direction_schema = '../messaging/direction.avsc'
# direction_topic = 'direction_messages'

while not 'direction_messages' in KafkaClient(wanted_client).topic_partitions.keys():
    print 'waiting for direction Client'
    time.sleep(1)

consumer_direction = KafkaConsumer(direction_topic, bootstrap_servers=wanted_client)

direction_handler = mursDirMessage(direction_schema, direction_topic, wanted_client)

'''
#For sending button messages
port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = '1001'
'''
