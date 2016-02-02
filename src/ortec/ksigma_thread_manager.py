import time
from kafka import KafkaConsumer, KafkaClient, SimpleProducer
import json
from ksigma import ksigma
import numpy as np
from kafka.common import LeaderNotAvailableError
from messaging.mursavro import mursArrayMessage
from messaging.ksigma_avro import mursKsigmaMessage


def ksigma_manager(background_buffer, middle_buffer, event_buffer, wanted_client, data_schema, data_topic, ksigma_topic, ksigma_schema):
    counter = 0
    outlier = 0
    total = 0
    
    #check that consumer is ready for 'data_messages'
    
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in ksigma thread'
        time.sleep(1)
    consumer = KafkaConsumer(data_topic,bootstrap_servers=wanted_client)

    #Initialize Ksigma messaging
    topic = 'ksigma_messages'
    ksigma_messaging = mursKsigmaMessage(ksigma_schema, ksigma_topic, wanted_client)



    #initialize reading of messages deserialization
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)
    

    #set up ksgigma message for Kafka
    message = {}
    
    det_ksigma = []
    flag = 0

    
    
    for msg in consumer:

         if msg.value != 'STOP':
            
            dict = data_handler.decode(msg.value) 
             
            #instantiate objects
            if flag == 0:
                for key in dict.keys():
                    
                    det_ksigma.append( ksigma(background_buffer, middle_buffer, event_buffer))
                    flag =1 

            for i, key in enumerate(dict.keys()):
                spectrum = np.array(dict[key]['spectrum'])
                timestamp = dict[key]['time']
                kstat_message = det_ksigma[i].ingress(timestamp,spectrum)
                message[key] = kstat_message
                
                

                if kstat_message['k_stat'] >= 1:
                    outlier +=1.
                else:
                    total +=1.

            ksigma_messaging.publishMessage(message)
           
            
            
            #print counter
            counter +=1
         else:
             #print outlier,total
             print "there were 1-std outliers", outlier/(total+outlier) * 100.,'% of the time'
             exit()
