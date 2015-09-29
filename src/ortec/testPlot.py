import os
import h5py
import matplotlib.pyplot as plt
import numpy as np
fName=os.path.abspath('./DataLog-2015-09-29T15-43-35Z.h5')

data={}
with h5py.File(fName,'r') as f:
    for sn in f.keys():
        data[sn]={}
        for key in f[sn]:
            data[sn][key]=f[sn][key][:]

print data.keys()

f,ax=plt.subplots()
for sn in data.keys():
    t=data[sn]['time']
    gGC=np.sum(data[sn]['spectrum'],axis=1)
    
    ax.plot(t,gGC)

plt.show()

