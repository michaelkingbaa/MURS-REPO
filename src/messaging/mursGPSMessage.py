__author__ = 'chivers'


from kafka import SimpleProducer, KafkaClient
import avro.schema
import io, random
import copy
import time
from avro.io import DatumWriter
from kafka import KafkaConsumer
from kafka.common import LeaderNotAvailableError

import sys

class mursGPSMessage:
        
        def __init__(self, schemaFile, topic, client):
            self.topic = topic
            #Setup kafka producer
            self.kafka = KafkaClient(client)
            self.producer = SimpleProducer(self.kafka)
            
            try:
                self.schema = avro.schema.parse(open(schemaFile).read())
            except:
                print "ERROR: mursGPSMessage Init: ", sys.exc_info()[0]
                raise

            cons = KafkaConsumer(topic,client)
            c2 = super(cons)



        def serialize(self, arrayDict1):
            #to protect shared memory space of arrayDict1 with any "shallow" copies
            arrayDict = copy.deepcopy(arrayDict1)
                
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
            print arrayDict

            try:
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
            except LeaderNotAvailableError:
                time.sleep(1)
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
                
        def readMessage(self, msg):
            return self.decode(msg.value)



