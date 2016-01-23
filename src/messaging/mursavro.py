__author__ = 'chivers'


from kafka import SimpleProducer, KafkaClient
import avro.schema
import io, random
from avro.io import DatumWriter
from kafka import KafkaConsumer

import sys

class mursArrayMessage:

        def __init__(self, schemaFile):
            try:
                self.schema = avro.schema.parse(open(schemaFile).read())
            except:
                print "ERROR: mursArrayMessage Init: ", sys.exc_info()[0]
                raise


        def serialize(self, arrayDict):
            #Setup avro datum Writer
            writer = avro.io.DatumWriter(self.schema)

            # Convert dictionary of dictionaries to List for Avro serialization
            # Need to save serialnumber in List Field
            # Need to convert spectrum from tuple to list
            sensArray = []
            for key in arrayDict:
                sens = arrayDict[key]
                sens["spectrum"] = list(sens["spectrum"])
                sens["serialnumber"] = key
                sensArray.append(sens)

            # Prepare avro encoder and write to raw bytes
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
            for i in range(len(sensArray)):
                item = sensArray[i]
                sn = item['serialnumber']
                item['spectrum'] = tuple(item['spectrum'])
                arrayDict[sn] = item

            return arrayDict


        def publishMessage(self, arrayDict, client, topic):

            #Setup kafka producer
            kafka = KafkaClient(client)
            producer = SimpleProducer(kafka)

            #publish message to topic
            producer.send_messages(topic, self.serialize(arrayDict))

        def readMessage(self, msg):
            return self.decode(msg.value)



