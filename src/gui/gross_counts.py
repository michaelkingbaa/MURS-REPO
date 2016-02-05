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


class GrossCountsWidget(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self)

        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Gross Counts')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Time')

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Counts')

    # self.invertY()
    # self.line = self.plot()


def gross_counts_update(gross_counts):
    epoch_time = {}
    gm_time = {}
    dict = get_data()
    time_range = 200;
    if dict == 'STOP':
        exit()
        ###FIGURE OUT HOW TO END NICELY
    color_mask = ['w', 'b', 'g', 'y', 'r', 'm']
    for i, key in enumerate(dict.keys()):
        if key not in total_counts.keys():
            total_counts[key] = np.zeros(time_range)
            time[key] = np.zeros(time_range)

        # Append
        # total_counts[key].append(sum(dict[key]['spectrum']))
        # time[key].append(dict[key]['time'])

        # NP append & delete first element
        # total_counts[key][1:]
        # total_counts[key] = np.append(total_counts[key], sum(dict[key]['spectrum']))
        # time[key][1:]
        # time[key] = np.append(time[key], dict[key]['time'])

        epoch_time[key] = dict[key]['time']
        gm_time[key] = epoch_time[key] - start_time

        # NP Rolling
        total_counts[key] = np.roll(total_counts[key], -1)
        total_counts[key][-1] = sum(dict[key]['spectrum'])

        time[key] = np.roll(time[key], -1)
        time[key][-1] = int(gm_time[key])

        if i == 0:
            gross_counts.clear()

        gross_counts.addItem(pg.PlotCurveItem(total_counts[key], time[key], pen=color_mask[i]))


def get_data():
    data_msg = consumer.next()

    if data_msg.value != 'STOP':
        dict = data_handler.decode(data_msg.value)
    else:
        return 'STOP'

    return dict


start_time = time.time()  # current epoch time
data = {}
time = {}
total_counts = {}

# KAFKA consumer
# wanted_client = 'localhost:9092'
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
