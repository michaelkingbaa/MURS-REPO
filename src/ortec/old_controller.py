#dev=usb.core.find(find_all=1)
#idVendor=2605, idProduct=31

def listIDs(devList):
    for cfg in devList:
        sys.stdout.write('Decimal VendorID=' + str(cfg.idVendor) + ' & ProductID=' + str(cfg.idProduct) + '\n')
        sys.stdout.write('Hexadecimal VendorID=' + hex(cfg.idVendor) + ' & ProductID=' + hex(cfg.idProduct) + '\n\n')


class CMD():
    FPGA_INIT=0x0004
    FPGA_LOAD=0x0005
    FPGA_TEST=0x0006
    FPGA_RESET=0x0011
    FPGA_VERSION=0x0012
        
class digibase():
    def __init__(self):
        self.dev=usb.core.find(idVendor=2605, idProduct=31)
        if self.dev is None:
            raise ValueError('No Digibase Connected')
        elif type(self.dev) is type([]):
            print 'Found %d Digibase(s)'%len(self.dev)
            for dev in self.dev:
                self.configFPGA(dev)
        else:
            print 'Found Single Digibase'
            self.configFPGA(self.dev)
            
    def configFPGA(self,dev):
        print 'Configuring the FPGA'
        print dev
        print dev.bNumConfigurations

        dev.set_configuration()
   
        com=chr(CMD.FPGA_TEST)
        com+=struct.pack('>H',3)
        com+=chr(0)
        dev.write(1,com)
        r=dev.read(1,7)
        print r
#        dev.write(1,FPGACONFIGCOMMAND.INITFPGA)
            
