__author__ = 'chivers'

import sys
from h5FileReader import mursH5FileReader as reader
sys.path.append('/Users/baamitch/GitHub/murs/src/messaging')
#from messaging.mursavro import mursArrayMessage
from mursavro import mursArrayMessage

class mursArrayReplay:

    def __init__(self,h5File, client, topic):
        self.h5File = reader(h5File)
        self.sn = self.h5File.getSerialNumbers()
        self.mursMessage = mursArrayMessage('messaging/mursArray.avsc', client, topic)

    def replay(self):

        for i in range(self.h5File.getRecordLength()):
            data =  self.h5File.getDataRecord(i)
            print data
            self.mursMessage.publishMessage(data)




