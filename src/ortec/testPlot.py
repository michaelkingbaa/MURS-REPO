import os
import h5py
import matplotlib.pyplot as plt
from matplotlib.colors import PowerNorm, LogNorm
import numpy as np
fName=os.path.abspath('./DataLog-2015-09-16T19-28-55Z.h5')

data={}
with h5py.File(fName,'r') as f:
    for sn in f.keys():
        data[sn]={}
        for key in f[sn]:
            data[sn][key]=f[sn][key][:]

print data.keys()

f,ax=plt.subplots()

#Colormap plot
fig1={}
ax1={}
plot={}
for folder in data.keys():
    fig1[folder],ax1[folder]=plt.subplots()
    h = ax1[folder].pcolorfast(data[folder]['spectrum'], cmap='rainbow', norm=PowerNorm(.5))
    plot[folder] = plt.colorbar(h,ax=ax1[folder])

plt.show()

# time vs. sum
for sn in data.keys():
    t=data[sn]['time']
    gGC=np.sum(data[sn]['spectrum'],axis=1)
    
    ax.plot(t,gGC)

plt.show()

