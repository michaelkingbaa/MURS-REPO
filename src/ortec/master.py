import sys
#from threading import Thread, Condition
import multiprocessing as mp
from daq import daq
from Queue import Queue
import time
import zmq
import json
import datetime
from kafka import SimpleConsumer, KafkaClient, KafkaConsumer
from ksigma_thread_manager import ksigma_manager
from direction_thread_manager import direction_manager
#from calibration_thread import calibration_manager
sys.path.append('/Users/nicolekelley/git_repos/murs/src/messaging')
from mursavro import mursArrayMessage 
from ksigma_avro import mursKsigmaMessage
from direction_avro import mursDirMessage
#from calibration_avro import mursCalibrationMessage

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

    #read this is later
    data_schema = '../messaging/mursArray.avsc'
    data_topic = 'data_messages'
    ksigma_topic = 'ksigma_messages'
    direction_topic = 'direction_messages'
    ksigma_schema = '../messaging/ksigma.avsc'

    
    thread = mp.Process(target = daq, args=(daq_message,data_schema,), kwargs = dict(acq_time=3600))
    thread.start()


    #Start GOLF algorithm

    #these should all be read in from somewhere
    background_buffer = 8 #number of data acquisitions to determine background
    event_buffer = 2 #number of data acquisitions to determine time frame of k-sigma
    middle_buffer = 2
    
    thread_ksigma = mp.Process(target = ksigma_manager, args = (background_buffer, middle_buffer, event_buffer, wanted_client, data_schema, data_topic, ksigma_topic, ksigma_schema))
    thread_ksigma.start()

    #read these in at some point
    background_buffer = 8
    event_buffer = 1
    middle_buffer = 2
    direction_schema = '../messaging/direction.avsc'
    setup_file = 'detector_location.config'

    thread_dir = mp.Process(target = direction_manager, args = (setup_file, background_buffer, middle_buffer, event_buffer, wanted_client, data_topic, data_schema, direction_topic, direction_schema))
    thread_dir.start()

#    calibration_schema = '../messaging/calibration.avsc'
#    calibration_topic = 'calibration_messages'
    
#    thread_cal = mp.Process(target = calibration_manager, args = (data_schema, data_topic, wanted_client, calibration_schema, calibration_topic))
#    thread_cal.start()
                                                            

    #get clients to listen to Kafka messages
    
        
    
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

    while not direction_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for direction Client'
        time.sleep(1)
        
    consumer_direction = KafkaConsumer(direction_topic, bootstrap_servers = wanted_client)

  #  while not calibration_topic in KafkaClient(wanted_client).topic_partitions.keys():
  #      print 'waiting for calibration Client', counter
  #      counter +=1
  #      time.sleep(1)
        
 #   consumer_calibration = KafkaConsumer(calibration_topic, bootstrap_servers = wanted_client)
    
    #initialize reading of messages -- for testing
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)
    ksigma_messaging = mursKsigmaMessage(ksigma_schema, ksigma_topic, wanted_client)
    direction_messaging = mursDirMessage(direction_schema, direction_topic, wanted_client)
 #   calibration_messaging = mursCalibrationMessage(calibration_schema, calibration_topic, wanted_client)
    
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
            time.sleep(2)
            break
        
        data = data_handler.decode(msg.value)
        #print data
        #print counter
        msg = consumer_ksigma.next()
        ksigma = ksigma_messaging.decode(msg.value)
        for key in ksigma.keys():
            print ksigma[key]

        #print consumer_direction.pending() ,'pending'
        dir_msg = consumer_direction.next()
        direction = direction_messaging.decode(dir_msg.value)
        print direction
        print counter

        
 #       cal_msg = consumer_calibration.get_message(timeout=0.1)
 #       calibration = calibration_messaging.decode(cal_msg.value)
 #       print calibration
        
        #print ksigma['15226068']
        
    
        
                    
    
    thread.join()
    thread_ksigma.join()
    thread_dir.join()
   # thread_cal.join()


