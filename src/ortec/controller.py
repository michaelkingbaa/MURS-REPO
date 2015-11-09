#!/usr/bin/env python2
'''
Created by S. Henshaw 2 Sept. 2015
Modification to support mulitprocess added on 21 Oct. 2015

Ortec Vendor ID: 2605  Product ID=31
'''
import os
import sys
from struct import pack,unpack
import struct
from usb1 import USBContext
import time
import numpy as np
from logger import DataLogger
import argparse
import json
import datetime as dt

class BitRegister(object):
    def __init__(self,name,initByte):
        #initByte is a bytestring
        self._name=name
        self._byte=initByte
        return 

    def set_bit(self,index,value):
        #index = 0-7 and value is True/False (1/0)
        tmp=ord(self._byte)
        mask=1<<index
        tmp&=~mask
        if value:
            tmp|=mask
        self._byte=chr(tmp)
        return
    def set_value(self,intVal):
        if type(intVal) is not type(int()):
            raise ValueError('intValue must be of type int')
        self._byte=chr(intVal)
    
    def get_bytes(self):
        return self._byte

    def set_bytes(self,bytestr):
        self._byte=bytestr

    def get_name(self):
        return self._name

    def get_value(self):
        #Returns a list of bit values
        tmp=[ord(self._byte) & 2**i !=0 for i in range(8)]
        return tmp
    
class ByteRegister(object):
    def __init__(self,name,initBytes):
        self._name=name
        self._bytes=initBytes
        return
    
    def get_name(self):
        return self._name

    def get_bytes(self):
        return self._bytes

    def set_bytes(self,bytestr):
        self._bytes=bytestr
    
    def set_value(self,intValue):
        if type(intValue) is not type(int()):
            raise ValueError('Set Value but be of type int in ByteRegister')
        if len(self._bytes) ==1:
            self._bytes=pack('B',intValue)
        elif len(self._bytes)==2:
            self._bytes=pack('H',intValue)
        elif len(self._bytes)==4:
            self._bytes=pack('I',intValue)
                

    def get_value(self):
        print 'Getting {0} value:  Len={1}, bytes: {2}'.format(self._name,len(self._bytes),repr(self._bytes))
        if len(self._bytes) ==1:
            val= unpack('B',self._bytes)[0]
            print val
            return val
        elif len(self._bytes)==2:
            val= unpack('H',self._bytes)[0]
            print val
            return val
        elif len(self._bytes)==4:
            val=unpack('I',self._bytes)[0]
            print val
            return val
        else:
            raise Exception('Bytes wrong length: {0}'.format(len(self._bytes)))
            
class ControlRegister(object):
    #This contains the objects of interest, all others set to zero
    def __init__(self, bytestr=''):
        if bytestr is not '':
            self.set_from_bytes(bytestr)
            self._regName=[i.get_name() for i in self._byteList]
            return 
        else:
            print 'Setting Control Register to Defaults'    
            self.set_defaults()
            self._regName=[i.get_name() for i in self._byteList]
            return 

    def set_from_bytes(self,bytestring):
        if len(bytestring) !=80:
            raise RuntimeError("Invalid # of bytes to set_from_bytes in Control Register: {0}".format(len(bytestring)))
        b=list(bytestring)
        self._byteList=[BitRegister('control',b[0]),
                        BitRegister('status',b[1]),
                        ByteRegister('width',b[2]),
                        ByteRegister('hv_act',b[3]),
                        ByteRegister('spare_0',b[4]),
                        BitRegister('insight_ctl',b[5]),
                        ByteRegister('aux_io',b[6]),
                        BitRegister('aux_ctl',b[7]),
                        ByteRegister('ff_count',''.join(b[8:12])),
                        ByteRegister('fine_gain_act',''.join(b[12:16])),
                        ByteRegister('fine_gain_set',''.join(b[16:20])),
                        ByteRegister('lld_set',''.join(b[20:24])),
                        ByteRegister('lt_preset',''.join(b[24:28])),
                        ByteRegister('livetime',''.join(b[28:32])),
                        ByteRegister('rt_preset',''.join(b[32:36])),
                        ByteRegister('realtime',''.join(b[36:40])),
                        ByteRegister('uld_set',''.join(b[40:42])),
                        ByteRegister('hv_set',''.join(b[42:44])),
                        ByteRegister('aux0_cnt',''.join(b[44:48])),
                        ByteRegister('aux1_cnt',''.join(b[48:52])),
                        ByteRegister('auxE_cnt',''.join(b[52:56])),
                        ByteRegister('gain_stab_max',''.join(b[56:58])),
                        ByteRegister('gain_stab_mid',''.join(b[58:60])),
                        ByteRegister('gain_stab_min',''.join(b[60:62])),
                        ByteRegister('offset_act',''.join(b[62:64])),
                        ByteRegister('offset_set',''.join(b[64:66])),
                        ByteRegister('offset_stab_max',''.join(b[66:68])),
                        ByteRegister('offset_stab_mid',''.join(b[68:70])),
                        ByteRegister('offset_stab_min',''.join(b[70:72])),
                        ByteRegister('mem_size',''.join(b[72:74])),
                        ByteRegister('mem_start',''.join(b[74:76])),
                        BitRegister('control2',''.join(b[76])),
                        ByteRegister('spare_1',''.join(b[77:80]))]
        return 

    def set_defaults(self):
        self._byteList=[BitRegister('control',chr(1)),
                        BitRegister('status',chr(0)),
                        ByteRegister('width',chr(24)),
                        ByteRegister('hv_act',chr(0)),
                        ByteRegister('spare_0',chr(0)),
                        BitRegister('insight_ctl',chr(0)),
                        ByteRegister('aux_io',chr(0)),
                        BitRegister('aux_ctl',chr(0x3)),
                        ByteRegister('ff_count',chr(0)*4),
                        ByteRegister('fine_gain_act',pack('I',0x200000)),
                        ByteRegister('fine_gain_set',pack('I',0x200000 | 1<<23)),
                        ByteRegister('lld_set',pack('I',1280*8)),
                        ByteRegister('lt_preset',pack('I',0)),
                        ByteRegister('livetime',pack('I',0)),
                        ByteRegister('rt_preset',pack('I',0)),
                        ByteRegister('realtime',pack('I',0)),
                        ByteRegister('uld_set',pack('H',1023)),
                        ByteRegister('hv_set',pack('H',0)),
                        ByteRegister('aux0_cnt',pack('I',0)),
                        ByteRegister('aux1_cnt',pack('I',0)),
                        ByteRegister('auxE_cnt',pack('I',0)),
                        ByteRegister('gain_stab_max',pack('H',0)),
                        ByteRegister('gain_stab_mid',pack('H',0)),
                        ByteRegister('gain_stab_min',pack('H',0)),
                        ByteRegister('offset_act',pack('H',0)),
                        ByteRegister('offset_set',pack('H',0)),
                        ByteRegister('offset_stab_max',pack('H',0)),
                        ByteRegister('offset_stab_mid',pack('H',0)),
                        ByteRegister('offset_stab_min',pack('H',0)),
                        ByteRegister('mem_size',pack('H',64)),
                        ByteRegister('mem_start',pack('H',0)),
                        BitRegister('control2',chr(0)),
                        ByteRegister('spare_1',chr(0)*3)]
        return 

    def get_settings(self):
        settings={}
        exclude=['spare_1']
        for reg in self._byteList:
            if reg.get_name() not in exclude:
                settings[reg.get_name()]=reg.get_value()
        return settings
    
    def set_hv_actual(self,volts):
        hvsetting=int(volts/1.25)
        index=self._regName.index('hv_set')
        self._byteList[index].set_value(hvsetting)

    def get_hv_actual(self):
        index=self._regName.index('hv_act')
        tmp_lo=self._byteList[index].get_value()
        index=self._regName.index('status')
        tmp_hi=self._byteList[index].get_value()[5:7]
        return (tmp_lo | tmp_hi[0]<<8 | tmp_hi[1]<<9)*1.25#return value in volts

    def set_fine_gain(self,fg):
        if fg >=0.4 and fg <=1.2:
            index=self._regName.index('fine_gain_set')
            val=int(fg*2**22)
            self._byteList[index].set_value(val)
        else:
            raise ValueError('fg must be between 0.4-1.2')

    def get_fine_gain(self):
        index=self._regName.index('fine_gain_act')
        tmp=self._byteList[index].get_value()/2.**22
        return tmp
        
    def get_byte_string(self):
        bytes=[i.get_bytes() for i in self._byteList]
        #print bytes
        return ''.join(bytes)
    
    def set_enable_hv(self,value):
        index=self._regName.index('control')
        if value in [0,1]:
            self._byteList[index].set_bit(6,value)
            self._byteList[self._regName.index('control2')].set_bit(2,value)
        else:
            raise ValueError('set_enable_hv value must be 0,1')

    def set_enable_gain_stab(self,value):
        index=self._regName.index('control')
        if value in [0,1]:
            self._byteList[index].set_bit(4,value)
        else:
            raise ValueError('set_enable_hv value must be 0,1')

    def set_gain_stab_pars(self,minVal, midVal, maxVal):
        names=['gain_stab_min','gain_stab_mid','gain_stab_max']
        pars=[minVal,midVal,maxVal]
        valid=[i > 0 and i < 1024 for i in pars]
        if all(valid):
            for i,v in enumerate(pars):
                index=self._regName.index(names[i])
                self._byteList[index].set_value(v)
        
    def get_mem_size(self):
        index=self.regName.index('mem_size')
        return self._byteList[index].get_bytes()
        
    def set_acq_start(self,value):
        if value is 0 or value is 1:
            index=self._regName.index('control')
            self._byteList[index].set_bit(1,1)
        else:
            raise ValueError('acq_start bit must be 1 or 0')
            
    ### MARK INCORPORATING THE OVERFLOW ##
    def set_enable_overflow(self,value):
        index=self._regName.index('control2')
        if value in [0,1]:
            self._byteList[index].set_bit(6,value)
        else:
            raise ValueError('set_enable_overflow value must be 0,1')

class FPGA(object):
    eP_SEND=8
    eP_RECV=2

    TIMEOUT=300
    
    CMD_SETCONTROL=chr(0)
    CMD_SHOWCONTROL=chr(1)
    CMD_CLEARDATA=chr(4)
    CMD_SHOWDATA=chr(128)
    
    def __init__(self,cnct):
#        print '\tConstructing FPGA...'
        self._cnct=cnct

        #Getting Initial Values from the FPGA
        self._controlRegister=ControlRegister(self.read_control_register())
        #print 'Initial Values from the FPGA:'
        #print repr(self._controlRegister.get_byte_string())

#        print '\tSetting Defaults'
        self._controlRegister.set_defaults()
        #print repr(self._controlRegister.get_byte_string())

        #Setting the Appropriate Settings
        self._controlRegister.set_enable_hv(1)

        #Writing CR to the FPGA
        self.write_control_register()
        
        ##Mark #Setting the Overflow Channel
        self._controlRegister.set_enable_overflow(1)

        
    def read_control_register(self):
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_SHOWCONTROL,self.TIMEOUT)
        r=self._cnct.bulkRead(self.eP_RECV,80,self.TIMEOUT)
        return r

    def getRegisterSettings(self):
        CR=self.read_control_register()
        self._controlRegister.set_from_bytes(CR)
        settings=self._controlRegister.get_settings()
        settings['gain_stab_enable']=int(settings['control'][4])
        settings['hv_actual']=self._controlRegister.get_hv_actual()
        settings['fine_gain']=self._controlRegister.get_fine_gain()
        exclude=['control','status','insight_ctl','spare_0','aux_io','aux_ctl','ff_count','aux0_cnt',
                 'aux1_cnt','auxE_cnt','mem_size','mem_start','control2','spare_1']
        for key in exclude:
            if key in settings:
                del settings[key]

        return settings

        
    def write_control_register(self):
        tmp=self.read_control_register()
        cr=self._controlRegister.get_byte_string()
        msg=self.CMD_SETCONTROL+cr
        self._cnct.bulkWrite(self.eP_SEND,msg,self.TIMEOUT)
        self._cnct.bulkRead(self.eP_RECV,0,self.TIMEOUT)
        CR=self.read_control_register()
        print 'Control Register Written Successfully!'
        self._controlRegister.set_from_bytes(CR)

    def clear_data(self):
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_CLEARDATA,self.TIMEOUT)
        self._cnct.bulkRead(self.eP_RECV,0,self.TIMEOUT)

    def show_data(self):
#        nBytes=self._controlRegister.get_mem_size()
        nBytes=4097
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_SHOWDATA,self.TIMEOUT)
        r=self._cnct.bulkRead(self.eP_RECV,nBytes,self.TIMEOUT)
        return r

    def start_acq(self):
        self._controlRegister.set_acq_start(1)
        self.write_control_register()
    
    def enable_hv(self):
        self._controlRegister.set_enable_hv(1)
        self.write_control_register()

    def disable_hv(self):
        self._controlRegister.set_enable_hv(0)
        self.write_control_register()

    def set_hv(self,volts):
        self._controlRegister.set_hv_actual(volts)
        self.write_control_register()
        return self._controlRegister.get_hv_actual()

    def get_hv(self):
        return self._controlRegister.get_hv_actual()

    def set_fine_gain(self,value):
        self._controlRegister.set_fine_gain(value)

    def get_fine_gain(self):
        return self._controlRegister.get_fine_gain()
    
    def enable_gain_stab(self):
        self._controlRegister.set_enable_gain_stab(1)
        self.write_control_register()

    def disable_gain_stab(self):
        self._controlRegister.set_enable_gain_stab(0)
        self.write_control_register()

    def set_gain_stab_pars(self,minVal, midVal, maxVal):
        self._controlRegister.set_gain_stab_pars(minVal,midVal,maxVal)
        self.write_control_register()

    
class MicroController(object):
    #Microcontroller EndPoints  from ORTEC Docs
    eP_SEND=1
    eP_RECV=1

    #Commands to send to MC that execute on FPGA
    FPGA_INIT=0x0004
    FPGA_LOAD=0x0005
    FPGA_TEST=0x0006
    FPGA_RESET=0x0011
    FPGA_VERSION=0x0012

    #USB Connection Timeout
    TIMEOUT=800
    
    #firmware for FPGA
    dirname=os.path.dirname(__file__)
    rbfFile=os.path.join(os.path.abspath(dirname),'digiBaseRH.rbf')

    #Max Data Size (ORTEC driver requirement)
    MAX_MSG_SIZE=65536

    def __init__(self,cnct):
#        print '\tInitializing MicroController'
        if not os.path.isfile(self.rbfFile):
            raise ValueError('Firware file Does Not Exist: %s'%self.rbfFile)
        else:
            self._cnct=cnct
            #self._fpga=self.initializeFPGA()


    def initializeFPGA(self):
        while True:
            try:
                self.send(self.FPGA_TEST)
                self.send(self.FPGA_RESET)
#                print '\tFPGA is configured'
                return FPGA(self._cnct)
                break
            except RuntimeError as e:
                print 'initalize FPGA Exception: ', e
                self.send(self.FPGA_INIT)
                with open(self.rbfFile,'rb') as f:
                    self.send(self.FPGA_LOAD,data=f.read())
                pass

            
    def send(self, command,rspLen=0,data=''):
        '''
        Message Structure to the MC is as follows:
        ##################################### SEND #########################################
        Offset      Name                Description
        0           COMMAND             one of the fpga commands (see above) e.g. FPGA_INIT
        1           RESPONSE LENGTH     length of response in bytes (typically 2)
        2           NULL                This is always 0
        3->N+4      DATA0-N             Optional Data to send (used for firmware)

        USB sends commands in 64 byte packets.  If the send message length %64==0 then you
        must send an additional zero length packet ('') to terminate the command
        ################################### RECIEVE #######################################
        Offset      Name         Description
        0           ERR_MAC      Macro error code (0=success)
        1           ERR_MIC      Micro error code (0=success)
        2->N+2      DATA0-N      Optional Data to send (used for firmware)
        ###################################################################################
        '''
        #Accounting for ERR_MAC & ERR_MIC in Response Length 
        rspLen+=2

        #Container for Data returned in response (will be returned
        response=b''

        #Packing the message to be sent
        hdr=chr(command)
        hdr+=pack('>H',rspLen)
        hdr+=chr(0)

        #Packing optional data into message (passed as argument)
        dpkts=[data[i:i+self.MAX_MSG_SIZE] for i in range(0,len(data),self.MAX_MSG_SIZE)]


        #Sending Packets and getting response
        if len(dpkts)>0:
            for i in dpkts:
                msg=hdr+i
                self._cnct.bulkWrite(self.eP_SEND,msg,self.TIMEOUT)
                if len(msg)%64==0:
                    self._cnct.bulkWrite(self.eP_SEND,b'',self.TIMEOUT)

                recv=self._cnct.bulkRead(self.eP_RECV,rspLen,self.TIMEOUT)
                if len(recv)<2:
                    raise RuntimeError('MC Response invalid length: %s'%r.encode('hex'))
                if ord(recv[0]) !=0 or ord(recv[1]) !=0:
                    raise RuntimeError('MC Response Error:  MAC: %s, MIC: %s'%(ord(r[0]),ord(r[1])))
                response+=recv[2:]
        else:
            self._cnct.bulkWrite(self.eP_SEND,hdr,self.TIMEOUT)
            recv=self._cnct.bulkRead(self.eP_RECV,rspLen,self.TIMEOUT)
            if len(recv)<2:
                raise RuntimeError('MC Response invalid length: %s'%recv.encode('hex'))
            if ord(recv[0]) !=0 or ord(recv[1]) !=0:
                raise RuntimeError('MC Response Error:  MAC: %s, MIC: %s'%(ord(recv[0]),ord(recv[1])))
            response+=recv[2:]
        return response
    
                    
            

    
class DigiBase(object):
    vID=2605
    pID=31
    def __init__(self,sn=None,dev=None):
        print 'Constructing digiBase object with S/N: {0}'.format(sn)
        #self._usbCon=USBContext()
        #self._dev=self._usbCon.getByVendorIDAndProductID(self.vID,self.pID)
        #if self._dev is  None:
        #    raise RuntimeError("No Digibase Connected")

        #print 'Connected to Digibase S/N: ',self._dev.getSerialNumber()
        if sn is None or dev is None:
            raiseRuntimeError('DigiBase() must have sn an dev in constructor')
        self._dev=dev
        self._cnct=self._dev.open()
        self._cnct.claimInterface(0)
        self._microCon=MicroController(self._cnct)
        self._fpga=self._microCon.initializeFPGA()
        print 'WARNING!!! Default HV is set to 0, use set_hv(volts=val) to set to appropriate value'

    def enable_hv(self):
        self._fpga.enable_hv()

    def disable_hv(self):
        self._fpga.disable_hv()

    def set_hv(self,volts):
        vold=self._fpga.get_hv()

        volts=float(volts)
        print 'Adjusting HV: {0}-->{1}'.format(vold,volts)
        if not (volts >=0 and volts <=1200):
            raise ValueError('cannot set_hv to volts={0}...Range is {1}-{2} V'.format(volts,vmin,vmax))
        val=self._fpga.set_hv(volts)
        return val 

        
    def set_hv_steps(self,volts):
        #Parameters for stepping HV
        vmin=0#volts
        vmax=1200#volts
        vstep=100.#Volts
        tstep=1e-4#seconds
        
        vold=self._fpga.get_hv()

        volts=float(volts)
        print 'Adjusting HV: {0}-->{1}'.format(vold,volts)
        if not (volts >=0 and volts <=1200):
            raise ValueError('cannot set_hv to volts={0}...Range is {1}-{2} V'.format(volts,vmin,vmax))
        
        nSteps=(volts-vold)/vstep
        sign=np.sign(nSteps)
        nSteps=int(max(abs(nSteps),1))

        #Stepping Voltage by 10 V increments
        for i in xrange(nSteps):
            v=vold+i*vstep*sign
            print 'Stepping Voltage to: {0} V'.format(v)
            self._fpga.set_hv(v)
            time.sleep(tstep)

        #Now we are sure we are within 10 V so set to actual value
        val=self._fpga.set_hv(volts)
        if nSteps>3:
            print 'Letting HV stabilize for 5 seconds'
            time.sleep(5)
        return val

    def get_hv(self):
        return self._fpga.get_hv_actual()
    
    def set_fine_gain(self,value):
        self._fpga.set_fine_gain(value)

    def get_fine_gain(self):
        return self._fpga.get_fine_gain()    

    def get_settings(self):
        return self._fpga.getRegisterSettings()
    
    def start_acquisition(self):
        self._fpga.start_acq()
        
    def get_spectrum(self):
        d=self._fpga.show_data()
        reg=self._fpga.read_control_register()
        
        print repr(reg[0:4]),repr(reg[42:44])
        tmp=struct.unpack('%dI'%(len(d)/4),d)
        return tmp

    def clear_spectrum(self):
        self._fpga.clear_data()

    def enable_gain_stab(self):
        self._fpga.enable_gain_stab()

    def disable_gain_stab(self):
        self._fpga.disable_gain_stab()
        
    def set_gain_stab_pars(self,minVal,midVal,maxVal):
        self._fpga.set_gain_stab_pars(minVal,midVal,maxVal)
        


class DigiBaseController(object):
    vID=2605
    pID=31
    def __init__(self):
        print 'Constructing DigiBaseController()'
        self._dets={}
        self._acquireFlag=False
        self._usbCon=USBContext()
        devlist=self._usbCon.getDeviceList()
        self._dev={}
        print 'Found {0} USB Connections...Scanning for Digibases'.format(len(devlist))
        for dev in devlist:
            try:
                vid=dev.getVendorID()
                pid=dev.getProductID()
                if vid == self.vID and pid == self.pID:
                    print 'DIGIBASE Found...getting S/N'
                    sn=dev.getSerialNumber()
                    print 'Found Digibase with SN: {0}'.format(sn)
                    self._dev[sn]=dev
            except Exception as  e:
                print 'There was an exception',e
                pass

        if len(self._dev.keys()) <=0:
            raise RuntimeError("No Digibase Connected")
        else:
            for sn,dev in self._dev.items():
                print 'Getting Serial Number and Constructing Digibase for: ',sn
                self._dets[sn]=DigiBase(sn,dev)

    def start_acquisition(self):
        t=time.time()
        self._acquireFlag=True
        for det in self._dets.values():
            det.start_acquisition()
        return t

    def clear_sample(self):
        for det in self._dets.values():
            det.clear_spectrum()
    
    def getSample(self,duration):
        if not self._acquireFlag:
            self.start_acquisition()

        st=time.time()
        self.clear_sample()
        time.sleep(duration)
        sp={}
        for sn,det in self._dets.items():
            sp[sn]={}
            sp[sn]['time']=st
            sp[sn]['spectrum']=det.get_spectrum()
            settings=det.get_settings()
            for key,value in settings.items():
                sp[sn][key]=value
        return sp

    def getDetList(self):
        return self._dets.keys()

    def getDet(self,detName):
        return self._dets[detName]

    
    def setHV(self,det,volts):
        if det in self._dets.keys():
            self._dets[det].set_hv(volts)
        else:
            raiseRuntimeError('No Det to set HV in DigiBaseController')

    def enable_gain_stab(self,det=None):
        if det is None:
            for det in self._dets:
                self._dets[det].enable_gain_stab()
        elif det in self._dets.keys():
            self._dets[det].enable_gain_stab()
        else:
            raise ValueError('enable_gain_stab called with invalid det: {0}'.format(det))

    def disable_gain_stab(self,det=None):
        if det is None:
            for det in self._dets:
                self._dets[det].disable_gain_stab()
        elif det in self._dets.keys():
            self._dets[det].disable_gain_stab()
        else:
            raise ValueError('disable_gain_stab called with invalid det: {0}'.format(det))


    def set_gain_stab_pars(self,det,minVal,midVal,maxVal):
        if det in self._dets.keys():
            self._dets[det].set_gain_stab_pars(minVal,midVal,maxVal)
        else:
            raise ValueError('set_gain_stab_pars called with invalid det: {0}'.format(det))

    def do_startup_checks(self):
        tHold=5
        print 'Waiting {0} seconds for Dets to Stabilize'.format(tHold)
        time.sleep(5)
        
class DigiBaseSpoofer(object):
    def __init__(self):
        print 'Spoofing class of Digibase'

    def start_acquisition(self):
        print 'Starting Acquisition'

    def clear_sample(self):
        return

    def getSample(self, duration):
        time.sleep(duration)
        sample={'db1001':{'time':time.time(),'spectrum':range(1024)}}
        return sample

    def getDetList(self):
        return ['db1001']

    def getDet(self,detname):
        return
    def setHV(self,det,volts):
        return
    def enable_gain_stab(self,det=None):
        return
    def disable_gain_stab(self,det=None):
        return
    def set_gain_stab_pars(self,det,minVal,midVal,maxVal):
        return
    def set_fine_gain(self,det,value):
        return
        
if __name__=="__main__":
   sys.exit('Cannot call Controller from command line...Try using python daq.py -h for instructions')
