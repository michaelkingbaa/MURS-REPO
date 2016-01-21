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

    def get_value(self):
        #Returns a list of bit values
        tmp=[ord(self._byte) & 2**i !=0 for i in range(8)]
        return tmp

    def set_bytes(self,bytestr):
        self._byte=bytestr

    def get_bytes(self):
        return self._byte

    def get_name(self):
        return self._name
    
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
        #print 'Getting {0} value:  Len={1}, bytes: {2}'.format(self._name,len(self._bytes),repr(self._bytes))
        if len(self._bytes) ==1:
            val= unpack('B',self._bytes)[0]
            return val
        elif len(self._bytes)==2:
            val= unpack('H',self._bytes)[0]
            return val
        elif len(self._bytes)==4:
            val=unpack('I',self._bytes)[0]
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
    
    def get_byte_string(self):
        bytes=[i.get_bytes() for i in self._byteList]
        #print bytes
        return ''.join(bytes)

    #### High Voltage ####
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

    def set_enable_hv(self,value):
        index=self._regName.index('control')
        if value in [0,1]:
            self._byteList[index].set_bit(6,value)
            self._byteList[self._regName.index('control2')].set_bit(2,value)
        else:
            raise ValueError('set_enable_hv value must be 0,1')

    def check_HV_ADC(self):
	#high when bias supply ADC is busy converting
	index=self.regName.index('status')
	return self._byteList[index].get_bytes()[3]

    #### Fine Gain ####
    def set_fine_gain(self,fg):
        if fg >=0.4 and fg <=1.2:
            index=self._regName.index('fine_gain_set')
            val=int(fg*2**22) | 1<<23
            self._byteList[index].set_value(val)
        else:
            raise ValueError('fg must be between 0.4-1.2')

    def get_fine_gain(self):
        index=self._regName.index('fine_gain_act')
        tmp=self._byteList[index].get_value()/2.**22
        return tmp
        
    #### Gain Stabalization ####
    def set_enable_gain_stab(self,value):
        index=self._regName.index('control')
        if value in [0,1]:
            self._byteList[index].set_bit(4,value)
        else:
            raise ValueError('set_enable_gain_stab value must be 0,1')

    def set_gain_stab_pars(self,minVal, midVal, maxVal):
        names=['gain_stab_min','gain_stab_mid','gain_stab_max']
        pars=[minVal,midVal,maxVal]
        valid=[i > 0 and i < 1024 for i in pars]
        if all(valid):
            for i,v in enumerate(pars):
                index=self._regName.index(names[i])
                self._byteList[index].set_value(v)

    #### Offset Stabalization ####
    def get_enable_offset_stab(self):
	index=self.regName.index('control')
	return self._byteList[index].get_bytes()[5]

    def set_enable_offset_stab(self,value):
        index=self._regName.index('control')
        if value in [0,1]:
            self._byteList[index].set_bit(5,value)
        else:
            raise ValueError('set_enable_offset_stab value must be 0,1')

    def get_offset(self):
	index=self._regName.index('offset_act')
	return self._byteList[index].get_bytes()

    def set_offset(self,offset):
	index=self._regName.index('offset_set')
	self._byteList[index].set_bytes(offset)

    def get_offset_stab_pars(self):
        names=['offset_stab_min','offset_stab_mid','offset_stab_max']
	pars=[]
        for index in names:
            pars.append(self._byteList[index].get_value())
	return pars

    def set_offset_stab_pars(self,minVal, midVal, maxVal):
        names=['offset_stab_min','offset_stab_mid','offset_stab_max']
        pars=[minVal,midVal,maxVal]
        valid=[i > 0 and i < 1024 for i in pars]
        if all(valid):
            for i,v in enumerate(pars):
                index=self._regName.index(names[i])
                self._byteList[index].set_value(v)

    #### Data ####
    def get_clear_counters(self):
	index=self.regName.index('control2')
	self._byteList[index].get_bytes()[0]

    def set_clear_counters(self,value):
	index=self.regName.index('control2')
	if value in [0,1]:
	    self._byteList[index].set_bit(0,value)

    def get_enable_overflow(self):
	index=self.regName.index('control2')
	return self._byteList[index].get_bytes()[6]

    def set_enable_overflow(self,value):
        index=self._regName.index('control2')
        if value in [0,1]:
            self._byteList[index].set_bit(6,value)
        else:
            raise ValueError('set_enable_overflow value must be 0,1')

    def get_fake_ADC(self):
	index=self.regName.index('control2')
	self._byteList[index].get_bytes()[1]

    def set_fake_ADC(self,value):
	index=self.regName.index('control2')
	if value in [0,1]:
	    self._byteList[index].set_bit(1,value)

    def get_mem_size(self): # uncalled
        index=self.regName.index('mem_size')
        return self._byteList[index].get_bytes()
        
    def set_mem_size(self,value):
	index=self.regName.index('mem_size')
	self._byteList[index].set_value(value)

    def get_mem_start(self):
	index=self.regName.index('mem_start')
	return self._byteList[index].get_bytes()

    def set_mem_start(self,value):
	index=self.regName.index('mem_start')
	self._byteList[index].set_value(value)

    def get_fifo_count(self):
	index=self.regName.index('ff_count')
	self._byteList[index].get_bytes()

    #### Acquisition ####
    def set_acq_start(self,value):
        if value is 0 or value is 1:
            index=self._regName.index('control')
            self._byteList[index].set_bit(1,value)
        else:
            raise ValueError('acq_start bit must be 1 or 0')

    def check_collect(self):
	# returns collection status active/inactive
	index=self.regName.index('status')
	return self._byteList[index].get_bytes()[0]

    def get_width(self):
	# converted to units of us (microseconds)
	index=self.regName.index('width')
	return self._byteList[index].get_value()/16

    def set_width(self,shapeTime):
	# shaping time in us (microseconds)
	index=self.regName.index('width')
	self._byteList[index].set_value(int(shapeTime*16))

    def get_PHA_mode(self): 
	# 0 is list mode, 1 is PHA
	index=self.regName.index('control')
	return self._byteList[index].get_bytes()[0]

    def set_PHA_mode(self,value):
	index=self.regName.index('control')
	if value in [0,1]:
	    self._byteList[index].set_bit(0,value)
	else:
	    raise ValueError('set_PHA_mode value must be 0,1')

    def reset(self,value):
	index=self.regName.index('control')
	self._byteList[index].set_bit(7,value)

    #### Time ####
    def get_enable_livetime_preset(self):
	index=self.regName.index('control')
	return self._byteList[index].get_bytes()[2]

    def set_enable_livetime_preset(self,value):
	index=self.regName.index('control')
	if value in [0,1]:
	    self._byteList[index].set_bit(2,value)
	else:
	    raise ValueError('set_enable_livetime_preset value must be 0,1')

    def get_livetime_preset(self):
	#converted to seconds
	index=self.regName.index('lt_preset')
	return 0.02*self._byteList[index].get_value()

    def set_livetime_preset(self,ltPreset):
	#ltPreset in seconds
	index=self.regName.index('lt_preset')
	self._byteList[index].set_value(ltPreset*50)

    def get_livetime(self):
	index=self.regName.index('livetime')
	return 0.02*self._byteList[index].get_value()

    def get_enable_realtime_preset(self):
	index=self.regName.index('control')
	return self._byteList[index].get_bytes()[3]

    def set_enable_realtime_preset(self,value):
	index=self.regName.index('control')
	if value in [0,1]:
	    self._byteList[index].set_bit(3,value)
	else:
	    raise ValueError('set_enable_realtime_preset value must be 0,1')

    def get_realtime(self):
	index=self.regName.index('realtime')
	return 0.02*self._byteList[index].get_value()

    #### Discriminators ####
    def get_LLD(self):
	#did not incorporate conversion mess 
	index=self.regName.index('lld_set')
	return self._byteList[index].get_value()

    def set_LLD(self,lldSet):
	#conversion
	index=self.regName.index('lld_set')
	self._byteList[index].set_value()

    def get_ULD(self):
	index=self.regName.index('uld_set')
	return self._byteList[index].get_value()

    def set_ULD(self,uldSetting):
	index=self.regName.index('uld_set')
	self._byteList[index].set_value(uldSetting)

    #### Insight Module ####
    def check_insight_module(self):
	#high when module has a waveform ready to transmit
	index=self.regName.index('status')
	return self._byteList[index].get_bytes()[2]

    def get_insight_control(self):
	index=self.regName.index('insight_ctl')
	return self._byteList[index].get_bytes()

    def set_insight_control(self,bytestr):
	index=self.regName.index('insight_ctl')
	self._byteList[index].set_bytes(bytestr)

    #### Enable Input ####
    def check_enable_input(self):
	#state of enable input
	index=self.regName.index('status')
	return self._byteList[index].get_bytes()[1]

    def get_enable_input_control(self):
	index=self.regName.index('aux_ctl')
	return self._byteList[index].get_bytes()

    def set_enable_input_control(self,bytestr):
	index=self.regName.index('aux_ctl')
	self._byteList[index].set_bytes(bytestr)

    def get_enable_input_count(self):
	index=self.regName.index('auxE_cnt')
	return self._byteList[index].get_bytes()

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
        self._controlRegister.set_enable_overflow(1)

        #Writing CR to the FPGA
        self.write_control_register()
        

        
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
        #tmp=self.read_control_register()
        cr=self._controlRegister.get_byte_string()
        msg=self.CMD_SETCONTROL+cr
        self._cnct.bulkWrite(self.eP_SEND,msg,self.TIMEOUT)
        self._cnct.bulkRead(self.eP_RECV,0,self.TIMEOUT)
        CR=self.read_control_register()
        #print 'Control Register Written Successfully!'
        self._controlRegister.set_from_bytes(CR)

    #### High Voltage ####
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

    def check_HV_ADC(self):
	return self._controlRegister.get_HV_ADC()

    #### Fine Gain ####
    def set_fine_gain(self,value):
        #print 'in FPGA...set fine gain to: ',value
        self._controlRegister.set_fine_gain(value)
        self.write_control_register()
	self.write_control_register() #need to run this twice for discriminators
        return self.get_fine_gain()

    def get_fine_gain(self):
        return self._controlRegister.get_fine_gain()

    #### Gain Stabalization ####
    def enable_gain_stab(self):
        self._controlRegister.set_enable_gain_stab(1)
        self.write_control_register()

    def disable_gain_stab(self):
        self._controlRegister.set_enable_gain_stab(0)
        self.write_control_register()

    def set_gain_stab_pars(self,minVal, midVal, maxVal):
        self._controlRegister.set_gain_stab_pars(minVal,midVal,maxVal)
        self.write_control_register()

    #### Offset Stabalization ####
    def get_enable_offset_stab(self):
	return self._controlRegister.get_enable_offset_stab()

    def set_enable_offset_stab(self,value):
	self._controlRegister.set_enable_offset_stab(value)
	self.write_control_register()

    def get_offset(self):
	return self._controlRegister.get_offset()

    def set_offset(self,offset):
	self._controlRegister.set_offset(offset)
	self.write_control_register()
	self._controlRegister.set_offset(0x8000 | offset)
	self.write_control_register()

    def get_offset_stab_pars(self):
	return self._controlRegister.get_offset_stab_pars()

    def set_offset_stab_pars(self,minVal, midVal, maxVal):
        self._controlRegister.set_offset_stab_pars(minVal,midVal,maxVal)
        self.write_control_register()

    #### Data ####
    def clear_data(self):
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_CLEARDATA,self.TIMEOUT)
        self._cnct.bulkRead(self.eP_RECV,0,self.TIMEOUT)

    def show_data(self):
#        nBytes=self._controlRegister.get_mem_size()
        nBytes=4097
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_SHOWDATA,self.TIMEOUT)
        r=self._cnct.bulkRead(self.eP_RECV,nBytes,self.TIMEOUT)
        return r

    def get_enable_overflow(self):
	return self._controlRegister.get_enable_overflow()

    def get_clear_counters(self):
	return self._controlRegister.get_clear_counters()

    def set_clear_counters(self,value):
	self._controlRegister.set_clear_counters(self,value)
	self.write_control_register()

    def get_fake_ADC(self,value):
	return self._controlRegister.get_fake_ADC()	

    def set_fake_ADC(self,value):
	self._controlRegister.set_fake_ADC(value)
	self.write_control_register()

    def set_mem_size(self,memSize):
	self._controlRegister.set_mem_size(memSize)
	self.write_control_register()

    def get_mem_start(self):
	return self._controlRegister.get_mem_start()

    def set_mem_start(self,memStart):
	self._controlRegister.set_mem_start(memStart)
	self.write_control_register()

    def get_fifo_count(self):
	return self._controlRegister.get_fifo_count()

    #### Acquisition ####
    def start_acq(self):
        self._controlRegister.set_acq_start(1)
        self.write_control_register()

    def check_collect(self):
	return self._controlRegister.check_collect()

    def get_width(self):
	return self._controlRegister.get_width()

    def set_width(self,shapeTime):
	self._controlRegister.set_width(shapeTime)
	self.write_control_register()

    def get_PHA_mode(self):
	return self._controlRegister.get_PHA_mode()

    def set_PHA_mode(self,PHAmode):
	self._controlRegister.set_PHA_mode(PHAmode)
	self.write_control_register()
    
    def reset(self):
	self._controlRegister.reset(1)
	self.write_control_register()
	os.system('sleep 0.05')
	self._controlRegister.reset(0)
	self.write_control_register

    #### Time ####
    def get_enable_livetime_preset(self):
	return self._controlRegister.get_enable_livetime_preset()

    def set_enable_livetime_preset(self,value):
	self._controlRegister.set_enable_livetime_preset(value)
	self.write_control_register()

    def get_livetime_preset(self):
	return self._controlRegister.get_livetime_preset(self)

    def get_livetime(self):
	return self._controlRegister.get_livetime()

    def set_livetime_preset(self,ltPreset):
	self._controlRegister.get_livetime_preset(self,ltPreset)
	self.write_control_register()

    def get_enable_realtime_preset(self):
	return self._controlRegister.get_enable_realtime_preset()

    def set_enable_realtime_preset(self,value):
	self._controlRegister.set_enable_realtime_preset(value)
	self.write_control_register()

    def get_realtime(self):
	return self._controlRegister.get_realtime()

    #### Discriminator ####
    def get_LLD(self):
	return self._controlRegister.get_LLD()

    def set_LLD(self,lldSet):
	self._controlRegister.set_LLD(lldSet)
	self.write_control_register()

    def get_ULD(self):
	return self._controlRegister.get_ULD()

    def set_ULD(self,uldBin):
	self._controlRegister.set_ULD(0x8000 | uldBin)
	self.write_control_register()
	self._controlRegister.set_ULD(uldBin)
	self.write_control_register()

    #### Insight Module ####
    def check_insight_module(self):
	return self._controlRegister.check_insight_module()

    def get_insight_control(self):
	return self._controlRegister.get_insight_control()

    def set_insight_control(self,bytestr):
	self._controlRegister.set_insight_control()
	self.write_control_register()

    #### Enable Input ####
    def check_enable_input(self):
	return self._controlRegister.check_enable_input()

    def get_enable_input_control(self):
	return self._controlRegister.get_enable_input_control()

    def set_enable_input_control(self):
	self._controlRegister.set_enable_input_control()
	self.write_control_register()

    def get_enable_input_count(self):
	return self._controlRegister.get_enable_input_count()

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
        #print 'Constructing digiBase object with S/N: {0}'.format(sn)
        #self._usbCon=USBContext()
        #self._dev=self._usbCon.getByVendorIDAndProductID(self.vID,self.pID)
        #if self._dev is  None:
        #    raise RuntimeError("No Digibase Connected")

        #print 'Connected to Digibase S/N: ',self._dev.getSerialNumber()
        if sn is None or dev is None:
            raiseRuntimeError('DigiBase() must have sn anD dev in constructor')
        self._dev=dev
        self._cnct=self._dev.open()
        self._cnct.claimInterface(0)
        self._microCon=MicroController(self._cnct)
        self._fpga=self._microCon.initializeFPGA()
        # print 'WARNING!!! Default HV is set to 0, use set_hv(volts=val) to set to appropriate value'

    def get_settings(self):
        return self._fpga.getRegisterSettings()

    #### High Voltage ####
    def enable_hv(self):
        self._fpga.enable_hv()

    def disable_hv(self):
        self._fpga.disable_hv()

    def set_hv(self,volts):
	#Parameters for stepping voltage
        vmin=0#volts
        vmax=1200#volts

        vold=self._fpga.get_hv()
        volts=float(volts)
        #print 'Adjusting HV: {0}-->{1}'.format(vold,volts)
        if not (volts >=vmin and volts <=vmax):
            raise ValueError('cannot set_hv to volts={0}...Range is {1}-{2} V'.format(volts,vmin,vmax))
        val=self._fpga.set_hv(volts)
        return val 

    def get_hv(self):
        return self._fpga.get_hv_actual()

    def check_HV_ADC(self):
	return self._fpga.get_HV_ADC()

    #### Fine Gain ####
    def set_fine_gain(self,value):
        #print 'Setting Fine Gain to: ',value
        self._fpga.set_fine_gain(value)

    def get_fine_gain(self):
        return self._fpga.get_fine_gain() 

    #### Gain Stabalization ####
    def enable_gain_stab(self):
        self._fpga.enable_gain_stab()

    def disable_gain_stab(self):
        self._fpga.disable_gain_stab()
        
    def set_gain_stab_pars(self,minVal,midVal,maxVal):
        self._fpga.set_gain_stab_pars(minVal,midVal,maxVal)

    #### Offset Stabalization ####
    def get_enable_offset_stab(self):
	return self._fpga.get_enable_offset_stab()

    def set_enable_offset_stab(self,value):
	self._fpga.set_enable_offset_stab(value)

    def get_offset(self):
	return self._fpga.get_offset()

    def set_offset(self,offset):
	self._fpga.set_offset(offset)

    def get_offset_stab_pars(self):
	return self._fpga.get_offset_stab_pars()

    def set_offset_stab_pars(self,minVal, midVal, maxVal):
        self._fpga.set_offset_stab_pars(minVal,midVal,maxVal)

    #### Aquisition ####
    def start_acquisition(self):
        self._fpga.start_acq()

    def check_collect(self):
	return self._fpga.check_collect()

    def get_width(self):
	return self._fpga.get_width()

    def set_width(self,shapeTime):
	self._fpga.set_width(shapeTime)

    def get_PHA_mode(self):
	self._fpga.get_PHA_mode()

    def set_PHA_mode(self,PHAmode):
	self._fpga.set_PHA_mode(PHAmode)

    def reset(self):
	self._fpga.reset()

    #### Data ####        
    def get_spectrum(self):
        d=self._fpga.show_data()
        reg=self._fpga.read_control_register()
        # print repr(reg[0:4]),repr(reg[42:44])
        tmp=struct.unpack('%dI'%(len(d)/4),d)
        return tmp

    def clear_spectrum(self):
        self._fpga.clear_data()

    def get_enable_overflow(self):
	return self._fpga.get_enable_overflow()

    def get_clear_counters(self):
	return self._fpga.get_clear_counters()

    def set_clear_counters(self,value):
	self._fpga.set_clear_counters(self,value)

    def get_fake_ADC(self,value):
	return self._fpga.get_fake_ADC()	

    def set_fake_ADC(self,value):
	self._fpga.set_fake_ADC(value)

    def set_mem_size(self,memSize):
	self._fpga.set_mem_size(memSize)

    def get_mem_start(self):
	return self._fpga.get_mem_start()

    def set_mem_start(self,memStart):
	self._fpga.set_mem_size(memStart)

    def get_fifo_count(self):
	return self._fpga.get_fifo_count()

    #### Time ####
    def get_enable_livetime_preset(self):
	return self._fpga.get_enable_livetime_preset()

    def set_enable_livetime_preset(self,value):
	self._fpga.set_enable_livetime_preset(value)

    def get_livetime_preset(self):
	return self._fpga.get_livetime_preset(self)

    def set_livetime_preset(self,ltPreset):
	self._fpga.get_livetime_preset(self,ltPreset)

    def get_livetime(self):
	return self._controlRegister.get_livetime()

    def get_enable_realtime_preset(self):
	return self._fpga.get_enable_realtime_preset()

    def set_enable_realtime_preset(self,value):
	self._fpga.set_enable_realtime_preset(value)

    def get_realtime(self):
	return self._fpga.get_realtime()

    #### Discriminator ####
    def get_LLD(self):
	return self._fpga.get_LLD()

    def set_LLD(self,lldSet):
	self._fpga.set_LLD(lldSet)

    def get_ULD(self):
	return self._fpga.get_ULD()

    def set_ULD(self,uldBin):
	self._fpga.set_ULD(uldBin)

    #### Insight Module ####
    def check_insight_module(self):
	return self._fpga.check_insight_module()

    def get_insight_control(self):
	return self._fpga.get_insight_control()

    def set_insight_control(self,btyestr):
	return self._fpga.set_insight_control(bytestr)

    #### Enable Input ####
    def check_enable_input(self):
	return self._fpga.check_enable_input()

    def get_enable_input_control(self):
	return self._fpga.get_enable_input_control()

    def set_enable_input_control(self,bytestr):
	self._fpga.set_enable_input_control(bytestr)

    def get_enable_input_count(self):
	return self._fpga.get_enable_input_count()

class DigiBaseController(object):
    vID=2605
    pID=31
    def __init__(self, producer,topic):
        print 'Constructing DigiBaseController()'

        ####THIS IS WHRERE USB DEVICES ARE MANAGED and will have to be checekd at a higher level
        self._dets={}
        self._acquireFlag=False
        self._usbCon=USBContext()
        devlist=self._usbCon.getDeviceList()
        self._dev={}
        #print 'Found {0} USB Connections...Scanning for Digibases'.format(len(devlist))
        for dev in devlist:
            try:
                vid=dev.getVendorID()
                pid=dev.getProductID()
                if vid == self.vID and pid == self.pID:
                    #print 'DIGIBASE Found...getting S/N'
                    sn=dev.getSerialNumber()
                    print 'Found Digibase with SN: {0}'.format(sn)
                    self._dev[sn]=dev
            except Exception as  e:
                print 'There was an exception',e
                pass

        if len(self._dev.keys()) <=0:
            print 'No Digibase Connected'
            producer.send_messages(topic,'STOP')
            raise RuntimeError("No Digibase Connected")
        
        else:
            for sn,dev in self._dev.items():
                #print 'Getting Serial Number and Constructing Digibase for: ',sn
                self._dets[sn]=DigiBase(sn,dev)

    #### High Voltage ####
    def setHV(self,det,volts):
        if det in self._dets.keys():
            self._dets[det].set_hv(volts)
        else:
            raiseRuntimeError('No Det to set HV in DigiBaseController')

    def check_HV_ADC(self,det):
        if det in self._dets.keys():
            self._dets[det].check_HV_ADC()
        else:
            raiseRuntimeError('No Det to check HV ADC in DigiBaseController')

    #### Gain Stabalization ####
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

    #### Offset Stabalization ####
    def enable_offset_stab(self,det=None):
        if det is None:
            for det in self._dets:
                self._dets[det].set_enable_offset_stab(1)
        elif det in self._dets.keys():
            self._dets[det].set_enable_offset_stab(1)
        else:
            raise ValueError('enable_offset_stab called with invalid det: {0}'.format(det))

    def disable_offset_stab(self,det=None):
        if det is None:
            for det in self._dets:
                self._dets[det].set_enable_gain_stab(0)
        elif det in self._dets.keys():
            self._dets[det].set_enable_gain_stab(0)
        else:
            raise ValueError('disable_offset_stab called with invalid det: {0}'.format(det))

    def get_offset_stab_pars(self,det):
	if det in self._dets:
	     self._dets[det].get_offset_stab_pars()

    def set_offset_stab_pars(self,det,minVal,midVal,maxVal):
        if det in self._dets.keys():
            self._dets[det].set_offset_stab_pars(minVal,midVal,maxVal)
        else:
            raise ValueError('set_gain_stab_pars called with invalid det: {0}'.format(det))


    #### Data ####
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

    def clear_counters(self,det):
	if det in self._dets:
	    self._dets[det].set_clear_counters(self,1)
	    self._dets[det].set_clear_counters(self,0)
	    if self._dets[det].get_clear_counters(self)!=0:
		raise ValueError('Issue in clearing counters')

    def set_mem_size(self,det,memSize):
	if det in self._dets:
	    self._dets[det].set_mem_size(memSize)
        else:
            raise RuntimeError('No Det to set MEMSIZE')

    def get_mem_start(self,det):
	if det in self._dets:
	    self._dets[det].get_mem_start()
        else:
            raiseRuntimeError('No Det to get MEMSTART')

    def set_mem_start(self,det,memStart):
	if det in self._dets:
	    self._dets[det].set_mem_size(memStart)
        else:
            raiseRuntimeError('No Det to set MEMSTART')

    def get_fifo_count(self,det):
	if det in self._dets:
	    self._dets[det].get_fifo_count()

    #### Acquisition ####
    def start_acquisition(self):
        t=time.time()
        self._acquireFlag=True
        for det in self._dets.values():
            det.start_acquisition()
        return t

    def check_collect(self,det):
        if det in self._dets.keys():
            self._dets[det].check_collect()
        else:
            raiseRuntimeError('No Det to check collection status')

    def get_width(self,det):
	if det in self._dets.keys():
	    self._dets[det].get_width()

    def set_width(self,det,shapeTime):
	if det in self._dets:
	    self._dets[det].set_width(shapeTime)
	    self.reset(det)

    def get_PHA_mode(self,det):
	if det in self._dets:
	    self._dets[det].get_PHA_mode()
        else:
            raiseRuntimeError('No Det to get PHA Mode')

    def set_PHA_mode(self,det,PHAmode):
	if det in self._dets:
	    self._dets[det].set_PHA_mode(PHAmode)
        else:
            raiseRuntimeError('No Det to set PHA Mode')

    def reset(self,det):
	if det in self._dets:
	    self._dets[det].reset()

    def do_startup_checks(self):
        tHold=5
        print 'Waiting {0} seconds for Dets to Stabilize'.format(tHold)
        time.sleep(5)

    def getDetList(self):
        return self._dets.keys()

    def getDet(self,detName):
        return self._dets[detName]

    #### Time ####
    def get_enable_livetime_preset(self,det):
	if det in self._dets:
	    self._dets[det].get_enable_livetime_preset()
        else:
            raiseRuntimeError('No Det to get enable livetime preset')

    def set_enable_livetime_preset(self,det,value):
	if det in self._dets:
	    self._dets[det].set_enable_livetime_preset(value)
        else:
            raiseRuntimeError('No Det to set enable livetime preset')

    #### Insight Module ####
    #status bit 2, get/set insight ctl

    #### Enable Input ####
    #status bit 1,

    #### Discriminator ####
    #get LLD/ULD
    def set_LLD(self,det,lldBin):
	if det in self._dets:
	    uFG = np.uint32(self._dets[det].get_fine_gain() & 0x7FFFFF)>>6
	    self._dets[det].set_LLD(np.uint32(float(lldBin)*0x100000/float(uFG)*512))

    def set_ULD(self,det,uldBin):
	if det in self_dets:
	    self._dets[det].set_ULD(uldBin)

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

    def do_startup_checks(self):
        tHold=5
        print 'Waiting {0} seconds for Dets to Stabilize'.format(tHold)
        time.sleep(5)
        
if __name__=="__main__":
   sys.exit('Cannot call Controller from command line...Try using python daq.py -h for instructions')
