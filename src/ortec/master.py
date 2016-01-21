from threading import Thread, Condition
from daq import daq
from Queue import Queue
import time
import zmq
import json
import datetime
from kafka import SimpleConsumer, KafkaClient, KafkaConsumer
from ksigma_thread_manager import ksigma_manager

#Setting up messaging queue for listening to GUI/ can control threads
port = "5556"
context = zmq.Context()
socket = context.socket(zmq.SUB)
socket.connect("tcp://localhost:%s" % port)
topic = '1001'
socket.setsockopt(zmq.SUBSCRIBE, topic)


#q = Queue()
#_sentinel = object() #object that signals shutdown
thread_message = Queue()
daq_message = Queue()
daq_flag = True


counter=0



if __name__ == "__main__":
    
    wanted_client = 'localhost:9092'

    #DO THIS LATER
    #perform a check to see if Digibases are plugged in 
    #code is written  so that if check is kwargs=(check=True) is run and there are no digibases, queue returns _sentinel    
    
#    thread = Thread(target = daq, args = (daq_message,),kwargs = dict(spoof_digibase = True, time=10))
    
    thread = Thread(target = daq, args=(daq_message,), kwargs = dict(acq_time=20))
    thread.start()


    #Start GOLF algorithm

    #these should all be read in from somewhere
    background_buffer = 8 #number of data acquisitions to determine background
    event_buffer = 2 #number of data acquisitions to determine time frame of k-sigma
    middle_buffer = 2
    
    thread_ksigma = Thread(target = ksigma_manager, args = (background_buffer, middle_buffer, event_buffer, wanted_client))
    thread_ksigma.start()


    #get clients to listen to Kafka messages
    
    data_topic = 'data_messages'
    ksigma_topic = 'ksigma_messages'
    
    
    kafka_client = KafkaClient(wanted_client)
    print 'master thinks',kafka_client.topic_partitions.keys()
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for Data Client'
        time.sleep(1)

    consumer = KafkaConsumer(data_topic, bootstrap_servers=wanted_client)

    while not ksigma_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for ksigma Client'
        time.sleep(1)
        
    consumer_ksigma = KafkaConsumer(ksigma_topic, bootstrap_servers = wanted_client)
    
    
    while True:

        #check for messages on ZMQ and add to DAQ queue
        try:
            user_message = socket.recv(flags = zmq.NOBLOCK)
            print user_message
            #print 'here'
        except zmq.Again as e:
            pass
        
        
        
        counter+=1
        
        msg = consumer.next()

        
        if msg.value == 'STOP':
            print 'kafka is really empty'
            break
        data = json.loads(msg.value)
        print data

        msg = consumer_ksigma.next()
        ksigma = json.loads(msg.value)
#        print ksigma['15226068']
        
    
        
                    
    
    thread.join()
    #thread_ksigma.join()


