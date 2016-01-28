import sys
import time
from kafka import  KafkaConsumer, KafkaClient, SimpleProducer
from kafka.common import LeaderNotAvailableError
sys.path.append('/Users/nicolekelley/git_repos/murs/src/messaging')
from mursavro import mursArrayMessage
from calibration_avro import mursCalibrationMessage
sys.path.append('/Users/nicolekelley/git_repos/murs/src/baa_algos')
from mursPeakTracker import PeakTracker

def calibration_manager(data_schema, data_topic, wanted_client, calibration_schema, calibration_topic):

    flag = 0
    #check that consumer is ready for 'data_messages'  
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in ksigma thread'
        time.sleep(1)
    consumer = KafkaConsumer(data_topic,bootstrap_servers=wanted_client)

    #initialize reading of messages deserialization
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)
    calibration_handler = mursCalibrationMessage(calibration_schema, calibration_topic, wanted_client)
    
    calibrations=[]
    
    for msg in consumer:

        if msg.value != 'STOP':

            dict = data_handler.decode(msg.value)
            

            #instatiate calibration objects (one for each detector SN)
            if flag == 0:
                for i, key in enumerate(dict.keys()):
                    calibrations[i] = PeakTracker(calibration_handler, key) #ask about other Flags
                    flag == 1
            for i, key in ennumerate(dict.keys()):
                calibrations[i].processMessage(dict[key]['time'], dict[key]['realtime'], dict[key]['spectrum'])  #this does calibration and sends message from calibration_handler

                
    else:
        exit()


    
    
