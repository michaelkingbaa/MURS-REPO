#Created by S. Henshaw 28 September 2015

import sys
import os
import numpy as np
import h5py
import datetime as dt
import time

class DataLogger(object):
    def __init__(self,fName=None,bufferLength=10):
        #print 'Constructing DataLogger'
        ############  Setting File Name Appropriately     ############
        if fName is None:
            t=dt.datetime.utcfromtimestamp(time.time())
            t=t.strftime("%Y-%m-%dT%H-%M-%SZ")
            if os.path.exists(os.path.abspath('./data/')):
                self._fName=os.path.abspath('./data/DataLog-%s.h5'%t)
            elif os.path.exists(os.path.abspath('/home/data/ortec')):
                self._fName=os.path.abspath('/home/data/ortec/DataLog-%s.h5'%t)
            else:
                self._fName=os.path.abspath('./DataLog-%s.h5'%t)
        else:
            dir=os.path.dirname(fName)
            if os.path.exists(dir):
                self._fName=fName
            else:
                raise RuntimeError('Cannot create log file at %s...Location does not exist'%dir)
        print 'Saving Data to: ',self._fName
        #################### Setting up Class Variables ####################
        self._bufferLength=bufferLength
        self._bufferIndex=0
        self._buffer={}
        self._bufferInitialized=False

    def initializeBuffer(self,sample):
        if not self._bufferInitialized:
            #print 'initializing buffer'
            self._bufferInitialized=True
            for sn in sample.keys():
                #print 'Creating Group for sn: {0}'.format(sn)
                self._buffer[sn]={}
                for key in sample[sn].keys():
                    #print 'Creating Dataset for key: {0}'.format(key)
                    if key == 'spectrum':
                        nChannels=len(sample[sn][key])
                        self._buffer[sn][key]=np.zeros((self._bufferLength,nChannels),dtype=np.int)
                    else:
                        #print 'dataType: {0}'.format(type(sample[sn][key]))
                        self._buffer[sn][key]=np.zeros(self._bufferLength,dtype=type(sample[sn][key]))
        else:
            raise RuntimeError('Cannot reinitialze buffer in DataLogger...')
        
    def logSample(self,sample):
        if not self._bufferInitialized:
            self.initializeBuffer(sample)
        if self._bufferIndex<self._bufferLength:
            print 'Adding sample to buffer at position {0}'.format(self._bufferIndex)
            for sn in sample.keys():
                for key in sample[sn].keys():
                    self._buffer[sn][key][self._bufferIndex]=sample[sn][key]
            self._bufferIndex+=1
        else:
            self.writeBufferToFile()
            self.logSample(sample)

    def writeBufferToFile(self):
        print 'Writing Buffer [:{0}] to File'.format(self._bufferIndex)
	with h5py.File(self._fName,'a') as f:
	    for sn in self._buffer.keys():
                if sn not in f:
                    #Adding group to the File
                    grp=f.create_group(sn)
                    for key,value in self._buffer[sn].items():
                        if key =='spectrum':
                            grp.create_dataset(key,(self._bufferIndex,value.shape[1]),
                                               data=value[:self._bufferIndex,:],maxshape=(None,value.shape[1]))
                        else:
                            grp.create_dataset(key,(self._bufferIndex,),data=value[:self._bufferIndex],maxshape=(None,))
                else:
                    #Appending to Groups in file
                    for key,value in self._buffer[sn].items():
                        ds=f[sn][key]
                        if key =='spectrum':
                            oldshape=ds.shape
                            ds.resize((oldshape[0]+self._bufferIndex,oldshape[1]))
                            ds[oldshape[0]:,:]=value[:self._bufferIndex,:]
                        else:
                            oldshape=ds.shape
                            ds.resize((oldshape[0]+self._bufferIndex,))
                            ds[oldshape[0]:]=value[:self._bufferIndex]
        self._bufferIndex=0

    def cleanup(self):
        self.writeBufferToFile()

if __name__=="__main__":
    raise RuntimeError("Cannot run logger.py as Main...consider importing...")
