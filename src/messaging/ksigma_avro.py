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

class mursKsigmaMessage:
        
        def __init__(self, schemaFile, topic, client):
            self.topic = topic
            #Setup kafka producer
            self.kafka = KafkaClient(client)
            self.producer = SimpleProducer(self.kafka)
            
            try:
                self.schema = avro.schema.parse(open(schemaFile).read())
            except:
                print "ERROR: mursArrayMessage Init: ", sys.exc_info()[0]
                raise
        


        def serialize(self, arrayDict1):
            #to protect shared memory space of arrayDict1 with any "shallow" copies
            arrayDict = copy.deepcopy(arrayDict1)
                
            #Setup avro datum Writer
            writer = avro.io.DatumWriter(self.schema)

            # Convert dictionary of dictionaries to List for Avro serialization
            # Need to save serialnumber in List Field
            
            sensArray = []
            for key in arrayDict:
                sens = arrayDict[key]
                sens["serialnumber"] = key
                sensArray.append(sens)
            #Prepare avro encoder and write to raw bytes
            bytes_writer = io.BytesIO()
            encoder = avro.io.BinaryEncoder(bytes_writer)
            writer.write(sensArray, encoder)
            return bytes_writer.getvalue()

        def decode(self, bytes):
            bytes_reader = io.BytesIO(bytes)
            decoder = avro.io.BinaryDecoder(bytes_reader)
            reader = avro.io.DatumReader(self.schema)
            sensArray = reader.read(decoder)

            arrayDict = {}
            #print sensArray
            for i in range(len(sensArray)):
                
                item = sensArray[i]
                sn = item['serialnumber']
                arrayDict[sn] = item

            return arrayDict


        def publishMessage(self, arrayDict):
            
            #publish message to topic
            try:
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
            except LeaderNotAvailableError:
                time.sleep(1)
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
                
        def readMessage(self, msg):
            return self.decode(msg.value)



