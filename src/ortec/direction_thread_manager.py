import time
from kafka import KafkaConsumer, KafkaClient, SimpleProducer
import json
from direction import direction
import numpy as np
from kafka.common import LeaderNotAvailableError
import sys
sys.path.append('/Users/nicolekelley/git_repos/murs/src/avro')
from mursavro import mursArrayMessage
from direction_avro import mursDirMessage

def direction_manager(setup_file, background_buffer, middle_buffer, event_buffer, wanted_client, data_topic, data_schema, direction_topic, direction_schema):
    counter = 0
    
    
    #check that consumer is ready for 'data_messages'
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in direction thread'
        time.sleep(1)
    data_consumer = KafkaConsumer(data_topic, bootstrap_servers=wanted_client)
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)

    #set up producer
    #kafka = KafkaClient(wanted_client)
    #producer = SimpleProducer(kafka)
    #topic = 'direction_messages'

    dir_messaging = mursDirMessage(direction_schema, direction_topic, wanted_client)
    
    dir_object = direction(setup_file, background_buffer, middle_buffer, event_buffer)
    
    for msg in data_consumer:

         if msg.value != 'STOP':
            dict = data_handler.decode(msg.value)
            #print dict
            
            
            
            dir_message = dir_object.ingress(dict)
            dir_messaging.publishMessage(dir_message)
            
            counter +=1
         else:
             exit()
