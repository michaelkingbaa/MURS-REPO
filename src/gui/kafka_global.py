#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
__author__ = "Mitchell Jones"

import sys

from kafka import KafkaConsumer, KafkaClient, SimpleConsumer

from messaging.mursavro import mursArrayMessage
from messaging.direction_avro import mursDirMessage
from messaging.ksigma_avro import mursKsigmaMessage 
from replay.h5FileReader import mursH5FileReader as reader
from replay.mursReplay import mursArrayReplay
	

# Kafka Producer IP Address & Port #
wanted_client = 'localhost:9092'

# Spectra and Gross Counts Plot
data_schema = '../messaging/mursArray.avsc'
data_topic = 'data_messages'

# Direction Plot
direction_schema = '../messaging/direction.avsc'
direction_topic = 'direction_messages'

# Metric Plot
ksigma_schema = '../messaging/ksigma.avsc'
ksigma_topic = 'ksigma_messages'
