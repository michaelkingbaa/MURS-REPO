'''
Created by S. Henshaw 2 Sept. 2015

Ortec Vendor ID: 2605  Product ID=31

'''
import os
import sys
from struct import pack
import struct
from usb1 import USBContext
import time
import numpy as np
'''
!!!!!!!!!!!!!!!! IMPORTANT NOTE   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

Need to make a BitRegister Class that handles 1 Byte and can 
set the bits appropriately

Need to make a ByteRegister Class that just handles setting 
some # of bytes appropriately. 

Then have Control Register instantiate either of the above for 
each of the sections in the doc.

Make each register type have the same get_bytes() method so that 
it can be iterated over to make the entire Control Register


'''
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

    def set_value(self,intValue):
        if type(intValue) is not type(int()):
            raise ValueError('Set Value but be of type int in ByteRegister')
        if len(self._bytes) ==1:
            self._bytes=chr(intValue)
        elif len(self._bytes)==2:
            self._bytes=pack('H',intValue)
        elif len(self._bytes)==4:
            self._bytes=pakc('I',intValue)

class ControlRegister(object):
    #This contains the objects of interest, all others set to zero
    def __init__(self, bytes=''):
        if bytes is not '':
            if len(bytes) != 80:
                raise RuntimeError("Invalid # bytes in Control Register Initial: %d"%len(bytes))
            print 'Setting Control Register from bytes'
            self.set_from_bytes(bytes)
            self._regName=[i.get_name() for i in self._byteList]
            return 
        else:
            print 'Setting Control Register to Defaults'    
            self.set_defaults()
            self._regName=[i.get_name() for i in self._byteList]
            return 

    def set_from_bytes(self,bytestring):
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
                        ByteRegister('hv_set',pack('H',790)),
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

    def set_hv_actual(self,volts):
        hvsetting=int(volts/1.25)
        index=self._regName.index('hv_set')
        self._byteList[index].set_value(hvsetting)
    
    def get_byte_string(self):
        bytes=[i.get_bytes() for i in self._byteList]
        #print bytes
        return ''.join(bytes)
    
    def set_enable_hv(self,value):
        index=self._regName.index('control')
        self._byteList[index].set_bit(6,1)

    def get_mem_size(self):
        index=self.regName.index('mem_size')
        return self._byteList[index].get_bytes()
        
    def set_acq_start(self,value):
        if value is 0 or value is 1:
            index=self._regName.index('control')
            self._byteList[index].set_bit(1,1)
        else:
            raiseValueError('acq_start bit must be 1 or 0')

class FPGA(object):
    eP_SEND=8
    eP_RECV=2

    TIMEOUT=300
    
    CMD_SETCONTROL=chr(0)
    CMD_SHOWCONTROL=chr(1)
    CMD_CLEARDATA=chr(4)
    CMD_SHOWDATA=chr(128)
    
    def __init__(self,cnct):
        print 'Constructing FPGA...'
        self._cnct=cnct

        #Getting Initial Values from the FPGA
        self._controlRegister=ControlRegister(self.read_control_register())
        print 'Initial Values from the FPGA:'
        print repr(self._controlRegister.get_byte_string())

        print 'Setting Defaults: ',
        self._controlRegister.set_defaults()
        print repr(self._controlRegister.get_byte_string())

        #Setting the Appropriate Settings
        self._controlRegister.set_enable_hv(1)

        #Writing CR to the FPGA
        self.write_control_register()
        

        
    def read_control_register(self):
        self._cnct.bulkWrite(self.eP_SEND,self.CMD_SHOWCONTROL,self.TIMEOUT)
        r=self._cnct.bulkRead(self.eP_RECV,80,self.TIMEOUT)
        return r

    def write_control_register(self):
        tmp=self.read_control_register()
        cr=self._controlRegister.get_byte_string()
        msg=self.CMD_SETCONTROL+cr
        self._cnct.bulkWrite(self.eP_SEND,msg,self.TIMEOUT)
        self._cnct.bulkRead(self.eP_RECV,0,self.TIMEOUT)
        tmp=self.read_control_register()
        print 'Control Register Written Successfully!'

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
    TIMEOUT=300
    
    #firmware for FPGA
    rbfFile=os.path.abspath('./digiBaseRH.rbf')

    #Max Data Size (ORTEC driver requirement)
    MAX_MSG_SIZE=65536

    def __init__(self,cnct):
        print 'Initializing MicroController'
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
                print 'FPGA is configured'
                return FPGA(self._cnct)
                break
            except RuntimeError as e:
                print e
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
    
                    
            

    
class digibase(object):
    vID=2605
    pID=31
    def __init__(self):
        print 'Constructing digiBase'
        self._usbCon=USBContext()
        self._dev=self._usbCon.getByVendorIDAndProductID(self.vID,self.pID)
        if self._dev is  None:
            raise RuntimeError("No Digibase Connected")
        print 'Connected to Digibase S/N: ',self._dev.getSerialNumber()
        self._cnct=self._dev.open()
        self._cnct.claimInterface(0)
        self._microCon=MicroController(self._cnct)
        self._fpga=self._microCon.initializeFPGA()

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

if __name__=="__main__":
    print 'Hello World'
    db=digibase()
    db.start_acquisition()
    for i in range(10):
        d=db.get_spectrum()
        #db.clear_spectrum()
        print len(d),d[50:60],type(d[50])
        time.sleep(1)

    
