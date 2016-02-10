__author__ = 'chivers'

#!/usr/bin/env python


import re
import time
import SocketServer
import datetime
import socket
from kafka import SimpleProducer, KafkaClient
import avro.schema
import io, random
import copy
import time
from avro.io import DatumWriter
from kafka import KafkaConsumer
from kafka.common import LeaderNotAvailableError

import sys


class TaipData:
  def __init__(self,taipString):
    self.reg = '^>(\w)(\w{2})(\d{5})(\+|-)(\d{2})(\d{5})(\+|-)(\d{3})(\d{5})(\d{3})(\d{3})(\d)(\d)(?:;ID=(\w+))?;\*(\w+)<$'
    self.TaipData = re.search(self.reg,taipString)


    self.data = self.TaipData.group(0)
    self.type = self.TaipData.group(1) + self.TaipData.group(2)
    self.time_of_day = self.TaipData.group(3)
    self.latitude = self.TaipData.group(4) + self.TaipData.group(5) + "." + self.TaipData.group(6)
    self.longitude =  self.TaipData.group(7) + self.TaipData.group(8) + "." + self.TaipData.group(9)
    self.speed = self.TaipData.group(10)
    self.heading = self.TaipData.group(11)
    self.source = self.TaipData.group(12)
    self.age = self.TaipData.group(13)
    self.id = self.TaipData.group(14)
    self.checksum = self.TaipData.group(15)


class sierraUDPServer(SocketServer.UDPServer):
    def __init__(self,server_address, handlerClass,schemaFile,topic,client):
        SocketServer.UDPServer.__init__(self,server_address,handlerClass)
        print server_address
        print handlerClass
        print schemaFile
        print topic
        print client

        self.message = sierraWirelessGPSMessage(schemaFile,topic,client)

class MyUDPHandler(SocketServer.BaseRequestHandler):

  def handle(self):
          time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          data = self.request[0].strip()
          remote_host = self.client_address[0]
          print "remote host: " + remote_host + " data: " + data
          try:
              taip_data = TaipData(data)
              dict = {}
              dict['time'] = float(taip_data.time_of_day)
              dict['latitude'] = float(taip_data.latitude)
              dict['longitude'] = float(taip_data.longitude)
              dict['elevation'] = 0.0
              dict['speed'] = float(taip_data.speed)
              dict['heading'] = float(taip_data.heading)
              self.server.message.publishMessage(dict)

          except ValueError:
            latitude = 0
            longitude = 0


class sierraWirelessGPSMessage:

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
            try:
                self.producer.send_messages(self.topic, self.serialize(arrayDict))
            except LeaderNotAvailableError:
                time.sleep(1)
                self.producer.send_messages(self.topic, self.serialize(arrayDict))

        def readMessage(self, msg):
            return self.decode(msg.value)


def runSierraWirelessServer(schemaFile, topic, client):
    HOST, PORT = socket.gethostbyname(socket.gethostname()), 5031
    server = sierraUDPServer((HOST, PORT), MyUDPHandler, schemaFile, topic, client)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print "shutting down server"
        server.shutdown()


