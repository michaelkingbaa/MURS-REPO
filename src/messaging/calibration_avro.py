__author__ = 'kelley'


from kafka import SimpleProducer, KafkaClient
import avro.schema
import io, random
import copy
import time
from avro.io import DatumWriter
from kafka import KafkaConsumer
from kafka.common import LeaderNotAvailableError

import sys

class mursCalibrationMessage:
        
        def __init__(self, schemaFile, topic, client):
            self.topic = topic
            #Setup kafka producer
            self.kafka = KafkaClient(client)
            self.producer = SimpleProducer(self.kafka, async=True)
            
            try:
                self.schema = avro.schema.parse(open(schemaFile).read())
            except:
                print "ERROR: mursCalibrationMessage Init: ", sys.exc_info()[0]
                raise
        


        def serialize(self, calib_object1):
            #to protect shared memory space of arrayDict1 with any "shallow" copies
            calib_object = copy.deepcopy(calib_object1)

            #convert object to dictionary
            arrayDict = {}
            if calib_object.sensorId != None:
                    arrayDict['sensorId'] = calib_object.sensorId
            if calib_object.status != None:        
                    arrayDict["status"] = calib_object.status
            if calib_object.startTime != None:
                    arrayDict['startTime'] = calib_object.startTime
            if calib_object.endTime != None:
                    arrayDict['endTime'] = calib_object.endTime
            if calib_object.referenceEnergy != None:
                    arrayDict['referenceEnergy'] = calib_object.referenceEnergy
            if calib_object.referenceChannel != None:
                    arrayDict['referenceChannel'] = calib_object.referenceChannel
            if calib_object.referenceChannelUncertainty != None:
                    arrayDict['referenceChannelUncertainty'] = calib_object.referenceChannelUncertainty
            if calib_object.binEnergies != None:
                    arrayDict['binEnergies'] = list(calib_object.binEnergies)
            if calib_object.sumSpectrum != None:
                    arrayDict['sumSpectrum'] = list(calib_object.sumSpectrum)
            if calib_object.integrationTime != None:
                    arrayDict['integrationTime'] = calib_object.integrationTime
            #if calib_object.peak != None:
            #        arrayDict['peak'] = calib_object.peak
        
            
            #Setup avro datum Writer
            writer = avro.io.DatumWriter(self.schema)

            

            # Prepare avro encoder and write to raw bytes
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(arrayDict, encoder)
            return bytes_writer.getvalue()

        def decode(self, bytes):
            bytes_reader = io.BytesIO(bytes)
            decoder = avro.io.BinaryDecoder(bytes_reader)
            reader = avro.io.DatumReader(self.schema)
            sensArray = reader.read(decoder)
            return sensArray


        def publishMessage(self, arrayDict):
            
            #publish message to topic
            try:
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
        
            except LeaderNotAvailableError:
                time.sleep(1)
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
                
        def readMessage(self, msg):
            return self.decode(msg.value)



