__author__ = 'chivers'
import time
from h5FileReader import mursH5FileReader as reader
from messaging.mursavro import mursArrayMessage

class mursArrayReplay:

    def __init__(self,h5File, client, topic):
        self.h5File = reader(h5File)
        self.topic = topic
        self.sn = self.h5File.getSerialNumbers()
        self.mursMessage = mursArrayMessage('../messaging/mursArray.avsc', topic, client)

    def replay(self,speed):

        for i in range(self.h5File.getRecordLength()):
            data =  self.h5File.getDataRecord(i)
            self.mursMessage.publishMessage(data)
            time.sleep(speed)
