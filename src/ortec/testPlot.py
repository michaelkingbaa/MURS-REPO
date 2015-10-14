import os
import h5py
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
fName=os.path.abspath('./DataLog-2015-10-02T16-44-49Z.h5')

data={}
with h5py.File(fName,'r') as f:
    for sn in f.keys():
        data[sn]={}
        for key in f[sn]:
            data[sn][key]=f[sn][key][:]

# print data.keys()


#Colormap plot
# fig1={}
# ax1={}
# plot={}
# for folder in data.keys():
#     fig1[folder],ax1[folder]=plt.subplots()
#     h = ax1[folder].pcolorfast(data[folder]['spectrum'], cmap='rainbow', norm=LogNorm(10))
#     plot[folder] = plt.colorbar(h,ax=ax1[folder])
# plt.show()

# time vs. sum
# f,ax=plt.subplots()
# for sn in data.keys():
#     t=data[sn]['time']
#     gGC=np.sum(data[sn]['spectrum'],axis=1)
#     ax.plot(t,gGC)
# plt.show()

# Sum Spectra File
fig2,ax2=plt.subplots()
ytextpos=10**1
colors='bgrcmk'
colorindex=0
for sn in data.keys():
    Spectrum=np.sum(data[sn]['spectrum'],axis=0)
    line, = ax2.semilogy(range(len(Spectrum)),Spectrum,colors[colorindex],label=sn)
    plt.legend(handles=line)
    # ax2.text(75,ytextpos,sn,color=colors[colorindex])
    colorindex=colorindex+1
    ytextpos=ytextpos/10**.5
# ax2.axvline(110, linewidth=1, color='r')

# format plot
xMin,xMax,yMin,yMax=ax2.axis()
ax2.axis((70,120,yMin,yMax))
ax2.set_xlabel('Bin')
ax2.set_ylabel('Count')

plt.show()
