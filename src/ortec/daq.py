#!/usr/bin/env python2
'''
Created by S. Henshaw 21 Oct. 2015
This is the main daq code for running ortec digibases.  It uses multiprocessing as well as queue
to ensure minimal loss of data and dead time.
'''
import os
import sys
import time
import numpy as np
import multiprocessing as mp
import Queue 
from logger import DataLogger
from controller import DigiBaseController
from controller import DigiBaseSpoofer
import warnings
import datetime as dt
import argparse
import json
import zmq
from kafka import SimpleProducer, KafkaClient
from kafka.common import LeaderNotAvailableError
from messaging.mursavro import mursArrayMessage


class WriteToFileProcess(mp.Process):
    def __init__(self,q,logger):
        mp.Process.__init__(self)
        self.exit=mp.Event()

        self._q=q
        self._logger=logger
        
    def run(self):
        while not self.exit.is_set():
            try:
                sample=self._q.get(timeout=0.1)
                #print 'Logging Sample'
                self._logger.logSample(sample)
            except Queue.Empty:
                pass
            except:
                print 'Exception occurred'
                raise 
            
        #print 'Exiting Logger.run()'
        self._logger.cleanup()

    def shutdown(self):
        print 'Shutdown initiated'
        self.exit.set()


        
######################### Main Execution Portion #########################
##########################################################################        
def daq(MESSAGE_Q, schema_file, **kwargs):

    #print 'here'
    #MESSAGE_Q is the global queue that sends "messages" from the master thread...
    
#kwargs can be:
    #check: "Check to see if Digibases are connected"
    
    #time: This sets the Total Acquisition Time
    #sample_duration: This is the length of one time binning (either 0.1 or 1 second)
    #log_period : This is the amount of time that data is stored
    #file : This is the file name
    #directory: directory to store file data
    #config_file : configuration file name
    #spoof_digibase: Checks daq software when no Digibase is connected

    
    #Setting Default Values
    minAcqTime=1#seconds
    maxAcqTime=30*3600#seconds 

    defaultSamplePeriod=1#seconds
    minSamplePeriod=0.1#seconds
    
    defaultLogPeriod=300#seconds
    minLogPeriod=1#seconds

    timeStart=dt.datetime.utcfromtimestamp(time.time())
    timeStart=timeStart.strftime("%Y-%m-%dT%H-%M-%SZ")
    defaultFileName='DataLog_{0}.h5'.format(timeStart)

    if os.path.exists(os.path.abspath('./data/')):
        defaultDirectory='./data/'
    else:
        defaultDirectory='./'

    defaultConfigFile='./ortec_config_default.ini'

    #set up kafka producer
    wanted_client = 'localhost:9092'
    #kafka = KafkaClient('localhost:9092')
    #producer = SimpleProducer(kafka)
    topic = 'data_messages'
    
    #Initialize Kafka messaging with avro
    data_messaging = mursArrayMessage(schema_file,  topic, wanted_client)
        
    #get kwargs out and set defaults for anything that hasn't been set
    default = False

    check = kwargs.get('check', default)
    acq_time = kwargs.get('acq_time',defaultSamplePeriod)
    sample_duration = kwargs.get('sample_duration', defaultSamplePeriod)
    log_period = kwargs.get('log_period', defaultLogPeriod)
    data_file = kwargs.get('file',defaultFileName)
    directory = kwargs.get('directory',defaultDirectory)
    config_file = kwargs.get('config_file',defaultConfigFile)
    spoof_digibase = kwargs.get('spoof_digibase',default)
    
    
    if check:
        print 'Performing Check to see if we can connect to Digibases'
        dbc=DigiBaseController(data_messaging.producer,topic)
        exit()
    
    if not minAcqTime <= acq_time <=maxAcqTime:
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('time: {0}  must be between {1} - {2} seconds. (use -h for help)'.format(acq_time,minAcqTime,maxAcqTime))
    if sample_duration>acq_time:
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('Sample Duration must be less than Acquisition Time')

    if sample_duration<minSamplePeriod:
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('Sample Duration must be greater than {0} seconds'.format(minSamplePeriod))
    if log_period<=minLogPeriod:
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('Log Period must be greater than {0} seconds'.format(minLogPeriod))
    if not os.path.exists(os.path.abspath(directory)):
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('Log Directory does not exist!...Cannot set log to: {0}'.format(directory))
    fileName=os.path.join(os.path.abspath(directory),data_file)
    
    if os.path.exists(fileName):
        warnings.warn('Log file already exists!! file: {0} may be overwritten!!'.format(fileName))
        
    if not os.path.exists(os.path.abspath(config_file)):
        data_messaging.producer.send_messages(topic,'STOP')
        raise RuntimeError('Detector Configuration File: {0} Not Found!!'.format(config_file))

        
    print 'Acquisition Time set to: {0} s'.format(acq_time)
    print 'Sample Duration set to {0} s'.format(sample_duration)
    print 'Log file: {0}'.format(fileName)
    print 'Writing Log to Disk every {0} seconds'.format(log_period)
    
    nSamples=int(acq_time*1.0/sample_duration)
    nLogSamples=max(int(log_period/sample_duration),1)
    print 'Logging data every {0} samples = {1} seconds'.format(nLogSamples,log_period)
    print 'Detector Configuration File: {0}'.format(config_file)

    
    if spoof_digibase:
        warnings.warn("Spoofing Digibase Input for debug purposes")
        dbc=DigiBaseSpoofer()
    else:
        dbc=DigiBaseController(data_messaging.producer,topic)
        
    #check for digibases
    
        
    dLog=DataLogger(fileName,nLogSamples)

    
    #Getting Detector Settings from .ini file
    with open(config_file,'r') as f:
        data=json.load(f)
        
        hv_setting=data[u'hv_setting']
        gain_stab_pars=data[u'gain_stab_pars']
        fine_gain=data[u'fine_gain']

    #Making sure there is a setting in .ini for each digibase connected otherwise setting default
    for det in dbc.getDetList():

        #import pdb; pdb.set_trace()
        #Applying HV Settings
        if det in hv_setting:
            print 'Setting HV for {0} to: {1} V'.format(det,hv_setting[det])
            dbc.setHV(det,hv_setting[str(det)])
        else:
            warnings.warn('{0} does not contain HV setting entry for det: {1}...setting to default 1000V'.format(config_file,det))
            dbc.setHV(det,1000)

        #Applying Gain Stabilization and pars
        if det in gain_stab_pars:
            if gain_stab_pars[det]['enable']:
                print 'Enabling Gain Stabilization for Det: {0}'.format(det)
                print 'Window channels: {0} - {1} - {2} '.format(gain_stab_pars[det]['min'],
                                                                 gain_stab_pars[det]['mid'],
                                                                 gain_stab_pars[det]['max'])
                dbc.set_gain_stab_pars(det,
                                       gain_stab_pars[det]['min'],
                                       gain_stab_pars[det]['mid'],
                                       gain_stab_pars[det]['max'])
                
                dbc.enable_gain_stab(det)
            else:
                print 'Disabling Gain Stabilization for Det: {0}'.format(det)
                dbc.disable_gain_stab(det)
        else:
            warnings.warn('{0} does not contain gain_stab setting for det: {1}...disabling gain_stabilization'.format(config_file,det))
            dbc.disable_gain_stab(det)
                          
                
        if det in fine_gain:
            print 'Setting Fine Gain for {0} to: {1}'.format(det,fine_gain[det])
            dbc.getDet(det).set_fine_gain(fine_gain[det])
        else:
            warnings.warn('{0} does not contain fine_gain setting for det: {1} ...setting to default=1'.format(config_file,det))
            dbc.set_fine_gain(det,1)

    dbc.do_startup_checks()
            
    ##########################################################################'
    ########################## Starting Run Loop  ############################'
    ##########################################################################'

    #Setting up Queue for logging to Disk 
    qFile=mp.Queue()
    pFile=WriteToFileProcess(qFile,dLog)
    pFile.start()

    
    

    dbc.start_acquisition()
    
    
    #LOOP
    for s in range(nSamples):
        #check for message to make any changes
        try:
            change_message = MESSAGE_Q.get_nowait()
            #make all changes from messages here
            print change_message
        except Queue.Empty:
            pass
        
        
        #print 'Acquiring Sample {0}'.format(s)

        #print 'Acquiring Sample {0}'.format(s)
        sample=dbc.getSample(duration=sample_duration)

        #send data to write file thread
       
        qFile.put(sample)
        
        #send data to Kafka
        
        data_messaging.publishMessage(sample)
        
        #messagedata = json.dumps(sample)

        #print messagedata
        #try:
        #    data_messaging.producer.send_messages(topic, messagedata)
        #except LeaderNotAvailableError:
        #    time.sleep(1)
        #    'here'
        #    data_messaging.producer.send_messages(topic, messagedata)
        
                

    print '##########################################################################'
    print '###################### Wrapping up Acquisition ###########################'
    print '##########################################################################'
    tHold=2#seconds
    print 'Waiting {0} seconds for processes to finish'.format(tHold)
    pFile.shutdown()
    data_messaging.producer.send_messages(topic,'STOP')
    time.sleep(tHold)
    print 'WriteToFileProcess state: {0}'.format(pFile.is_alive())
    print '##########################################################################'
    print '######################## Acquisition Complete ############################'
    print '##########################################################################'
    
