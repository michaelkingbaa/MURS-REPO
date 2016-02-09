
from kafka import  KafkaConsumer, KafkaClient, SimpleProducer, SimpleConsumer
from kafka.common import LeaderNotAvailableError
from messaging.mursavro import mursArrayMessage
from messaging.calibration_avro import mursCalibrationMessage
from messaging.synchronized_avro import mursSynchronizationMessage

def messaging_manager(data_schema, data_topic, wanted_client, calibration_schema, calibration_topic, synchronization_topic, synchronization_schema):
    
    #client 
    kafka_client = KafkaClient(wanted_client)
    
    #check that consumer is ready for 'data_messages'  
    while not data_topic in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client in ksigma thread'
        time.sleep(1)
    consumer = KafkaConsumer(data_topic,bootstrap_servers=wanted_client)

    #initialize reading of messages deserialization
    data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)
    calibration_handler = mursCalibrationMessage(calibration_schema, calibration_topic, wanted_client)
    synchronized_handler = mursSynchronizationMessage(synchronization_schema, synchronization_topic, wanted_client)
    calibration_consumer = False

    gps_data = {}
    cal_data = {} # each key is the sensor sn
    #need to load these data with defaults
    

    #check for calibration message every loop

    for msg in consumer:

        data = data_handler.decode(msg.value)
        #fixed_data = 
        
        #set up calibration consumer....only once
        if not calibration_consumer:
            if calibration_topic in KafkaClient(wanted_client).topic_partitions.keys():
                calibration_consumer = SimpleConsumer(kafka_client, "group", calibration_topic)
        
        #check for calibration message
        
        print calibration_consumer.pending(), 'out of while loop'
        #DEALS with calibration messages falling ahead of data messages...clears out queue 
        while calibration_consumer.pending() >0:
            if calibration_consumer.pending() <= len(data.keys()):
                print calibration_consumer.pending(), 'in if '
                cal_msg = calibration_consumer.get_message()
                hold_cal = calibration_handler.decode(cal_msg.message.value)
                #check that calibration worked first...
                cal_data[hold_cal['sensorId']] = hold_cal
                #print calibration_handler.decode(cal_msg.message.value)['referenceEnergy']
            else:
                #throw away messages to get synced up
                print calibration_consumer.pending(), 'in else'
                calibration_consumer.get_message()

        if len(cal_data.keys()) != 0:
            print cal_data['15226068']['status']
            #add the last version of calib
            #print data
            #gets here when pending messages = 0
            #process msg and cal_data
            #make new message
            fixed_data = data
            synchronized_handler.publishMessage(fixed_data, cal_data, gps_data)
        else:
            continue
                


        
        
    
