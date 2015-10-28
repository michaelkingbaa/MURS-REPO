import os
import sys
import h5py
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import argparse

class reader(object):
    #pull the necessary data from the h5 file into a dictionary
    def __init__(self,fileName):
	if os.path.splitext(fileName)[1]=='.h5':
	    if os.path.isfile(fileName):
		self.parseFile(fileName)
	    else:
		raise ValueError('No such file exists')
	else:
	    raise ValueError('Invalid file extension')
    def parseFile(self,fileName):
	self.data={}
	with h5py.File(fileName,'r') as f:
	    for sn in f.keys():
		self.data[sn]={}
		for key in f[sn]:
		    self.data[sn][key]=f[sn][key][:]
	
class plotter(object):
    #plot the data from the dictionary created
    def __init__(self,plotType,dataDict):
	for text in plotType:
	    colors='mgrkcb'
	    if text == 'S':
		#sum spectrum
		figS,axS=plt.subplots(figsize=(17,10))
		index=0
		for sn in dataDict.keys():
		    sumSpectrum=np.sum(dataDict[sn]['spectrum'][4:],axis=0)
		    lines = axS.semilogy(range(len(sumSpectrum)),sumSpectrum,colors[index],label=sn)
		    l=plt.legend()
		    index=index+1
		xMin,xMax,yMin,yMax=axS.axis()
		axS.axis((90,120,2000,30000))
		axS.set_xlabel('Bin')
		axS.set_ylabel('Count')
		index=0
		for text in l.get_texts():
		    text.set_color(colors[index])
		    index=index+1
		

	    if text == 'W':
		#waterfall colormap plots
		figC = plt.subplots(figsize=(17,10))
		axC,plotC={},{}
		index,colorMin,colorMax=0,1,80
		subplotArray=[(2,2),(1,3),(2,1),(1,0),(0,2),(0,1)]
		colors='mgrkcb'
		listSpectra={}
		for sn in dataDict.keys():
		    axC[sn]=plt.subplot2grid((3,4),subplotArray[index])
		    listSpectra[sn]=dataDict[sn]['spectrum'][4:]
		    # if np.abs(listSpectra[sn]).max() > colorMax:
			# colorMax=np.abs(listSpectra[sn]).max()
		    h = axC[sn].pcolorfast(listSpectra[sn],cmap='rainbow',norm=LogNorm(10),vmin=colorMin,vmax=colorMax)
		    plotC[sn] = plt.colorbar(h,ax=axC[sn])
		    axC[sn].set_title(sn,color=colors[index])
		    index=index+1

	plt.show()

def main():
    ## Parsing Command Line Arguements ##
    parser = argparse.ArgumentParser()
    parser.add_argument("-f","--file",type=str,help="Name of data file (default is DataLog_[timestamp].h5")
    parser.add_argument("-p","--plot_type",type=tuple,help="Type of plots")
    args=parser.parse_args()
    
    ## calling classes ##
    dataRaw=reader("DataLogs/"+args.file)
    plotter(args.plot_type,dataRaw.data)

if __name__=='__main__':
    main()
