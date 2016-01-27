__author__ = 'chivers'

from h5FileReader import mursH5FileReader as reader
from messaging.mursavro import mursArrayMessage

class mursArrayReplay:

    def __init__(self,h5File, client, topic):
        self.h5File = reader(h5File)
        self.sn = self.h5File.getSerialNumbers()
        self.mursMessage = mursArrayMessage('messaging/mursavro.avsc', client, topic)

    def replay(self):

        for i in range(self.h5File.getRecordLength()):
            data =  self.h5File.getDataRecord(i)
            print data
            self.mursMessage.publishMessage(data)




