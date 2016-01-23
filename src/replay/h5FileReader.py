__author__ = 'chivers'

import h5py as h5
import numpy as np

class mursH5FileReader:

    def __init__(self, filename):
        try:
            self.file = h5.File(filename,'r')
            self.sn = self.getSerialNumbers()
        except:
            print "ERROR: mursH5FileReader initializing " , sys.exc_info()[0]
            self.file = []
            raise

    def getSerialNumbers(self):
        if self.file:
            return self.file.keys()

    def getRecordLength(self):

        try:
            ds = self.file[self.sn[0]]
        except KeyError:
            print "ERROR: Invalid Serial Number"
            return None
        except:
            print sys.exc_info()[0]
            return None

        try:
            t = ds['time']
        except KeyError:
            print "ERROR: Invalid format - No timestamps"
            return None
        except:
            print sys.exc_info()[0]
            return None

        return len(t)

    def getDataRecord(self, elemNumber):

        rec = {}
        for key in self.sn:
            sensorRec = {}
            ds = self.file[key]
            sensorRec['fine_gain'] = ds['fine_gain'][elemNumber]
            sensorRec['fine_gain_act'] = ds['fine_gain'][elemNumber]
            sensorRec['fine_gain_set'] = ds['fine_gain_set'][elemNumber]
            sensorRec['gain_stab_enable'] = ds['gain_stab_enable'][elemNumber]
            sensorRec['gain_stab_max'] = ds['gain_stab_max'][elemNumber]
            sensorRec['gain_stab_mid'] = ds['gain_stab_mid'][elemNumber]
            sensorRec['gain_stab_min'] = ds['gain_stab_min'][elemNumber]
            sensorRec['hv_act'] = ds['hv_act'][elemNumber]
            sensorRec['hv_actual'] = ds['hv_actual'][elemNumber]
            sensorRec['hv_set'] = ds['hv_set'][elemNumber]
            sensorRec['livetime'] = ds['livetime'][elemNumber]
            sensorRec['lld_set'] = ds['lld_set'][elemNumber]
            sensorRec['lt_preset'] = ds['lt_preset'][elemNumber]
            sensorRec['offset_act'] = ds['offset_act'][elemNumber]
            sensorRec['offset_set'] = ds['offset_set'][elemNumber]
            sensorRec['offset_stab_max'] = ds['offset_stab_max'][elemNumber]
            sensorRec['offset_stab_mid'] = ds['offset_stab_mid'][elemNumber]
            sensorRec['offset_stab_min'] = ds['offset_stab_min'][elemNumber]
            sensorRec['realtime'] = ds['realtime'][elemNumber]
            sensorRec['rt_preset'] = ds['rt_preset'][elemNumber]
            sensorRec['spectrum'] = ds['spectrum'][elemNumber]
            sensorRec['time'] = ds['time'][elemNumber]
            sensorRec['uld_set'] = ds['uld_set'][elemNumber]
            sensorRec['width'] = ds['width'][elemNumber]

            rec[key] = sensorRec

        return rec

