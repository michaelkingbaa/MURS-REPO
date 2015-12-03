#!/usr/bin/env python2
'''
Created by S. Henshaw 21 Oct. 2015
This is the main daq code for running ortec digibases.  It uses multiprocessing as well queue
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
            
        print 'Exiting Logger.run()'
        self._logger.cleanup()

    def shutdown(self):
        print 'Shutdown initiated'
        self.exit.set()


        
######################### Main Execution Portion #########################
##########################################################################        
if __name__ == '__main__':
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
    ##################### Parsing Command Line Arguments   ##############################
    parser = argparse.ArgumentParser()
    parser.add_argument("--check",action="store_true",default=False,
                        help="Check to see if Digibases are connected")
    parser.add_argument("-t","--time",default=defaultSamplePeriod,type=float,
                        help="Total Acquisition time in seconds. Must be between {0}-{1} seconds".format(minAcqTime,maxAcqTime))
    parser.add_argument("--sample_duration",default=defaultSamplePeriod,type=float,
                        help="Time Period for each sample in seconds.  Must be less than total time and greater than {0} seconds. (see -h for help)".format(minSamplePeriod))
    parser.add_argument("--log_period",default=defaultLogPeriod,type=float,
                        help="Log Buffer Length in seconds.  Must be greater than {0} seconds".format(minLogPeriod))
    parser.add_argument("-f","--file",default=defaultFileName,type=str,
                        help="Name of data file.  Default is {0}".format(defaultFileName))
    parser.add_argument("--directory",default=defaultDirectory,type=str,
                        help="Directory to store Data File.  Default is {0}".format(defaultDirectory))
    parser.add_argument("--config_file",default=defaultConfigFile,type=str,
                        help="Name of config file for detector settings. Default is {0}".format(defaultConfigFile))
    parser.add_argument("--spoof_digibase",default=False,action="store_true",
                        help="Use this to check code without having digibase connected")
    args=parser.parse_args()
    # if len(sys.argv) <=1:
    #     parser.print_help()
    #     exit()
    # print '##############################################################################'
    # print '####################### Controller Acquisition Setup #########################'
    # print '##############################################################################'
    #
    # if args.check:
    #     print 'Performing Check to see if we can connect to Digibases'
    #     dbc=DigiBaseController()
    #     exit()
    #
    # if not minAcqTime <= args.time <=maxAcqTime:
    #     raise RuntimeError('time: {0}  must be between {1} - {2} seconds. (use -h for help)'.format(args.time,minAcqTime,maxAcqTime))
    #
    # if args.sample_duration>args.time:
    #     raise RuntimeError('Sample Duration must be less than Acquisition Time')
    # if args.sample_duration<minSamplePeriod:
    #     raise RuntimeError('Sample Duration must be greater than {0} seconds'.format(minSamplePeriod))
    # if args.log_period<=minLogPeriod:
    #     raise RuntimeError('Sample Duration must be greater than {0} seconds'.format(minSamplePeriod))
    #
    # if not os.path.exists(os.path.abspath(args.directory)):
    #     raise RuntimeError('Log Directory does not exist!...Cannot set log to: {0}'.format(args.directory))
    #
    # fileName=os.path.join(os.path.abspath(args.directory),args.file)
    #
    # if os.path.exists(fileName):
    #     warnings.warn('Log file already exists!! file: {0} may be overwritten!!'.format(fileName))
    #
    # if not os.path.exists(os.path.abspath(args.config_file)):
    #     raise RuntimeError('Detector Configuration File: {0} Not Found!!'.format(args.config_file))
    #
    # print 'Acquisition Time set to: {0} s'.format(args.time)
    # print 'Sample Duration set to {0} s'.format(args.sample_duration)
    # print 'Log file: {0}'.format(fileName)
    # print 'Writing Log to Disk every {0} seconds'.format(args.log_period)
    #
    # nSamples=int(args.time*1.0/args.sample_duration)
    # nLogSamples=max(int(args.log_period/args.sample_duration),1)
    # print 'Logging data every {0} samples = {1} seconds'.format(nLogSamples,args.log_period)
    # print 'Detector Configuration File: {0}'.format(args.config_file)

    print '###############################################################################'
    print '######################### Class Constructors ##################################'
    print '###############################################################################'
    if args.spoof_digibase:
        warnings.warn("Spoofing Digibase Input for debug purposes")
        dbc=DigiBaseSpoofer()
    else:
        dbc=DigiBaseController()
    # dLog=DataLogger(fileName,nLogSamples)

    print '###############################################################################'
    print '######################### Applying Settings  ##################################'
    print '###############################################################################'

    #Getting Detector Settings from .ini file
    # with open(args.config_file,'r') as f:
    #     data=json.load(f)
    #
    #     hv_setting=data[u'hv_setting']
    #     gain_stab_pars=data[u'gain_stab_pars']
    #     fine_gain=data[u'fine_gain']

    #Making sure there is a setting in .ini for each digibase connected otherwise setting default
    for det in dbc.getDetList():

        import pdb; pdb.set_trace()
        #Applying HV Settings
        if det in hv_setting:
            print 'Setting det: {0} HV to: {0} V'.format(det,hv_setting[det])
            dbc.setHV(det,hv_setting[str(det)])
        else:
            warnings.warn('{0} does not contain HV setting entry for det: {1}...setting to default 1000V'.format(args.config_file,det))
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
            warnings.warn('{0} does not contain gain_stab setting for det: {1}...disabling gain_stabilization'.format(args.config_file,det))
            dbc.disable_gain_stab(det)
                          
                
        if det in fine_gain:
            print 'Setting Fine Gain for {0} to: {1}'.format(det,fine_gain[det])
            dbc.getDet(det).set_fine_gain(fine_gain[det])
        else:
            warnings.warn('{0} does not contain fine_gain setting for det: {1} ...setting to default=1'.format(args.config_file,det))
            dbc.set_fine_gain(det,1)

    dbc.do_startup_checks()
            
    print '##########################################################################'
    print '########################## Starting Run Loop  ############################'
    print '##########################################################################'

    #Setting up Queue for logging to Disk 
    qFile=mp.Queue()
    pFile=WriteToFileProcess(qFile,dLog)
    pFile.start()

    #Setting up messaging queue for graphics and/or sending to sigma
    port = "5556"
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    topic = 1001

    dbc.start_acquisition()
    for s in range(nSamples):
        print 'Acquiring Sample {0}'.format(s)

        #print 'Acquiring Sample {0}'.format(s)
        sample=dbc.getSample(duration=args.sample_duration)
        qFile.put(sample)

        messagedata = json.dumps(sample)
        #print "%d %s" % (topic, messagedata)
        socket.send("%d %s" % (topic, messagedata))

    print '##########################################################################'
    print '###################### Wrapping up Acquisition ###########################'
    print '##########################################################################'
    tHold=2#seconds
    print 'Waiting {0} seconds for processes to finish'.format(tHold)
    pFile.shutdown()
    time.sleep(tHold)
    print 'WriteToFileProcess state: {0}'.format(pFile.is_alive())
    print '##########################################################################'
    print '######################## Acquisition Complete ############################'
    print '##########################################################################'
    
