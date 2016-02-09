#__author__ = 'kelley'


from kafka import SimpleProducer, KafkaClient
import avro.schema
import io, random
import copy
import time
from avro.io import DatumWriter
from kafka import KafkaConsumer
from kafka.common import LeaderNotAvailableError

import sys

class mursSynchronizationMessage:
        
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
        


    def serialize(self, data1, calibration1, gps1):
        #to protect shared memory space of arrayDict1 with any "shallow" copies
        data = copy.deepcopy(data1)
        calibration = copy.deepcopy(calibration1)
        gps = copy.deepcopy(gps1)

        #convert three dicts to one dictionary and keep what is wanted
        newList = []

        for key in data:
            #if key not in newDict:
            #    newDict[key] = {}
            newDict = {}
            newDict['Serialnumber'] = key
            newDict['Spectrum'] = data[key]['spectrum'][:1023]
            newDict['OverflowCounts'] = data[key]['spectrum'][1023]
            newDict['Timestamp'] = data[key]['time']
            newDict['HighVoltage'] = data[key]['hv_actual']
            newDict['Livetime'] = data[key]['livetime']

            #if data[key]['deadtime'] != None:
            #    newDict['Deadtime'] = data[key]['deadtime']

            newDict['GainStabilizationEnabled'] = data[key]['gain_stab_enable']
            
            if calibration[key]['startTime'] !=  None:
                newDict['CalibrationStartTime'] = calibration[key]['startTime']
                
            if calibration[key]['endTime'] != None:
                newDict['CalibrationEndTime'] = calibration[key]['endTime']
                
            if calibration[key]['referenceEnergy'] != None:
                newDict['ReferenceEnergy'] = calibration[key]['referenceEnergy']

            if calibration[key]['referenceChannel'] != None:
                newDict['ReferenceChannel'] = calibration[key]['referenceChannel']

            if calibration[key]['referenceChannelUncertainty'] != None:
                newDict['ReferenceChannelUncertainty'] = calibration[key]['referenceChannelUncertainty']

            if calibration[key]['binEnergies'] != None:
                newDict['BinEnergies'] = calibration[key]['binEnergies']
                
            if calibration[key]['sumSpectrum'] != None:
                newDict['SummedSpectra'] = calibration[key]['sumSpectrum']
                    
            if calibration[key]['integrationTime'] != None:
                newDict['IntegrationTime'] = calibration[key]['integrationTime']

            #if calibration[key]['peak'] != None:
            #       newDict['peak'] = calibration[key]['peak']

            #if gps['time'] != None:
            #    newDict['GPSTime'] = gps['time']

            #if gps['Latitude'] != None:
            #    newDict['Latitude'] = gps['latitude']

            #if gps['Longitude'] != None:
            #    newDict['Longitude'] = gps['longitude']

            #if gps['Elevation'] !=  None:
            #    newDict['Elevation'] = gps['elevation']

            newList.append(newDict)
            
        #print newList    
        #Setup avro datum Writer
        writer = avro.io.DatumWriter(self.schema)

            

        # Prepare avro encoder and write to raw bytes
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(newList, encoder)
        return bytes_writer.getvalue()

    def decode(self, bytes):
        bytes_reader = io.BytesIO(bytes)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)
        sensArray = reader.read(decoder)
        return sensArray


    def publishMessage(self, fixed_data, calibration_data, gps_data):
            
        #publish message to topic
        try:
            self.producer.send_messages(self.topic, self.serialize(fixed_data, calibration_data, gps_data))
        
        except LeaderNotAvailableError:
            time.sleep(1)
            self.producer.send_messages(self.topic, self.serialize(fixed_data, calibration_data, gps_data))
                
    def readMessage(self, msg):
        return self.decode(msg.value)



