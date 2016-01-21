import time
from kafka import KafkaConsumer, KafkaClient, SimpleProducer
import json
from ksigma import ksigma
import numpy as np
from kafka.common import LeaderNotAvailableError

def ksigma_manager(background_buffer, middle_buffer, event_buffer, wanted_client):
    counter = 0
    outlier = 0
    total = 0
    
    #check that consumer is ready for 'data_messages'
    while not 'data_messages' in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in ksigma thread'
        time.sleep(1)
    consumer = KafkaConsumer('data_messages',bootstrap_servers=wanted_client)

    #set up producer
    kafka = KafkaClient(wanted_client)
    producer = SimpleProducer(kafka)
    topic = 'ksigma_messages'

    #set up ksgigma message for Kafka
    message = {}
    
    det_ksigma = []
    flag = 0

    
    
    for msg in consumer:

         if msg.value != 'STOP':
            dict = json.loads(msg.value)
            
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
                    
            payload = json.dumps(message)
            try:
                producer.send_messages(topic,payload)
            except LeaderNotAvailableError:
                time.sleep(1)
                producer.send_messages(topic, payload)
            
            
            #print counter
            counter +=1
         else:
             #print outlier,total
             print "there were 1-std outliers", outlier/(total+outlier) * 100.,'% of the time'
             exit()
