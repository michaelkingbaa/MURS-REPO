import time
import json
import os
from kafka import  KafkaConsumer, KafkaClient, SimpleProducer
from kafka.common import LeaderNotAvailableError
from messaging.mursavro import mursArrayMessage
from messaging.calibration_avro import mursCalibrationMessage
from baa_algos.mursPeakTracker import PeakTracker

def calibration_manager(data_schema, data_topic, wanted_client, calibration_schema, calibration_topic, sensor_char_dir):

    flag = 0
    #check that consumer is ready for 'data_messages'  
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in ksigma thread'
        time.sleep(1)
    consumer = KafkaConsumer(data_topic,bootstrap_servers=wanted_client)

    #initialize reading of messages deserialization
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)
    calibration_handler = mursCalibrationMessage(calibration_schema, calibration_topic, wanted_client)
    
    
    calibrations={}
    time_previous={}
    
    for msg in consumer:
        
        if msg.value != 'STOP':

            data = data_handler.decode(msg.value)


            #instatiate calibration objects (one for each detector SN)
            #REMOVE FLAG...CHECK IF KEYS EXIST
            if flag == 0:
                for key in data:
                    det_file = os.path.join(sensor_char_dir,key+'.json')
                    with open(det_file) as f:
                        sens_chars = json.load(f)  
                    calibrations[key] = PeakTracker(calibration_handler, key, makeBinEnergies=True, sensorCharacterization = sens_chars) #ask about other Flags
                    time_previous[key] = data[key]['realtime'] - 50.  #for first iteration...make time previous 1 second shorter than the data['key']['realtime'] so realtime will be 1 second
                    flag = 1
            #print data['15226048']['time'] 
            for key in data:
                #REALTIME needs to be actual

                realtime = (data[key]['realtime'] - time_previous[key])*0.02
                time_previous[key] = data[key]['realtime']
                calibrations[key].processSpectrum(data[key]['time'], realtime, data[key]['spectrum'])  #this does calibration and sends message from calibration_handler

                
        else:
            print 'here'
            calibration_handler.producer.send_messages(calibration_topic, 'STOP')
            exit()


    
    
