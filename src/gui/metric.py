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


class MetricWidget(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self)

        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Metric')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Time')

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Metric')

    # self.invertY()
    # self.line = self.plot()


def metric_update(metric):
    epoch_time = {}
    gm_time = {}
    dict = get_data()
    time_range = 200;
    if dict == 'STOP':
        exit()
    color_mask = ['w', 'b', 'g', 'y', 'r', 'm']
    for i, key in enumerate(dict.keys()):
        if key not in data.keys():
            data[key] = np.zeros(time_range)
            time[key] = np.zeros(time_range)

        # data[key].append(sum(dict[key]['k_stat']))
        # time[key].append(dict[key]['time'])

        epoch_time[key] = dict[key]['time']
        gm_time[key] = epoch_time[key] - start_time

        # NP Rolling
        data[key] = np.roll(data[key], -1)
        data[key][-1] = dict[key]['k_stat']
        time[key] = np.roll(time[key], -1)
        time[key][-1] = int(gm_time[key])

        if i == 0:
            metric.clear()

        metric.addItem(pg.PlotCurveItem(data[key], time[key], pen=color_mask[i]))


def get_data():
    metric_msg = consumer_ksigma.next()

    if metric_msg.value != 'STOP':
        dict = metric_handler.decode(metric_msg.value)
    else:
        return 'STOP'

    return dict


start_time = time.time()  # current epoch time
data = {}
time = {}

# KAFKA consumer
# wanted_client = '192.168.0.101:9092'
# ksigma_schema = '../messaging/ksigma.avsc'
# ksigma_topic = 'ksigma_messages'

while not 'ksigma_messages' in KafkaClient(wanted_client).topic_partitions.keys():
    print 'waiting for ksigma Client'
    time.sleep(1)

consumer_ksigma = KafkaConsumer(ksigma_topic, bootstrap_servers=wanted_client)

metric_handler = mursKsigmaMessage(ksigma_schema, ksigma_topic, wanted_client)

'''
#For sending button messages
port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = '1001'
'''
