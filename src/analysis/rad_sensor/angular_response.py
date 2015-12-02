#need list_file, folder and background_file defined before running


import h5py
import matplotlib
import matplotlib.pylab as mpl
import numpy as np
import csv
import math
from lmfit import minimize, Parameters, Parameter, report_fit

#make gaussian - make this a seperate function
def gaussian(params, x, data):
    area = params['area'].value
    mu = params['mu'].value
    sigma = params['sigma'].value
    
    fnc = area/(sigma*np.sqrt(2.*np.pi))*np.exp(-(x-mu)**2/(2.*sigma**2))
    #mpl.plot(x,data)
    #mpl.plot(x,fnc)
    return fnc - data

def angular_response(folder, list_file, background_file):

    list_of_files=open(folder+list_file,'r')
    a=csv.reader(list_of_files)
    angle=[]
    file=[]
    for row in a:
        angle.append(row[0])
        file.append(row[1])
        for i in range(len(angle)):
            angle[i]=float(angle[i])
    
    cts_vs_chan={}
    data_time={}
    bg_sub={}
    peak_cts={}
    compton_cts={}
    ratio={}
    tot_counts={}
    q=0

    for j,i in enumerate(file):
        hold_string=folder+'data/'+i
        f=h5py.File(hold_string,"r")
    
    #get data structure ready cts_vs_chan[detector][angle] holds data
        if q==0:
            for key in f.keys():
                cts_vs_chan[key]={}
                data_time[key]={}
                bg_sub[key]={}
                peak_cts[key]={}
                compton_cts[key]={}
                ratio[key]={}
                tot_counts[key]={}
                q=1
    #fill data structure
        for key in f.keys():    
            cts_vs_chan[key]['%02i'%j]=np.sum(f[key]['spectrum'],axis=0)
            t=f[key]['time']
            data_time[key]['%02i'%j]=max(t)-min(t)
#get background
    bg_vs_chan={}
    bg_time={}
    f=h5py.File(folder+'background/'+background_file,"r")
    for key in f.keys():
        bg_vs_chan[key]=np.sum(f[key]['spectrum'],axis=0)
        bg_time[key]=max(f[key]['time'])-min(f[key]['time'])
#background subtract
    for key in f.keys():
        for i in range(0,len(angle)):
            bg_sub[key]['%02i'%i] = cts_vs_chan[key]['%02i'%i]/data_time[key]['%02i'%i] - bg_vs_chan[key]/bg_time[key]
            tot_counts[key]['%02i'%i]=np.sum(bg_sub[key]['%02i'%i])


#fit peak

#get data to be fitted-loop here
    roi=[90,120]
    xdata = np.arange(90.,120.)
    for key in f.keys(): 
        for i in range(0,len(angle)):
            ydata = bg_sub[key]['%02i'%i][roi[0]:roi[1]]

            x1 = xdata[0]
            x2 = xdata[-1]
            y1 = ydata[0]
            y2 = ydata[-1]

            params = Parameters()
            #initial guesses
            g = np.empty([3])
            g[0] = (1./3)*(np.amax(ydata) - np.mean([y1,y2]))*(x2-x1) #area
            g[1] = np.mean(roi) #mu
            g[2] = (x2-x1)/10. #sigma

            params.add('area',g[0])
            params.add('mu',g[1])
            params.add('sigma',g[2])

        
            fit = minimize(gaussian, params,args=(xdata,ydata))
            end_values = fit.params.valuesdict()
            peak_cts[key]['%02i'%i]=end_values['area']
        
        #now find comptonized part
        #lets say everything past 3sigma to the left of the center of the gaussian is comptonized
            last_comp = end_values['mu'] - 3.*end_values['sigma']
        
       
            compton_cts[key]['%02i'%i] = sum(np.clip(bg_sub[key]['%02i'%i][:last_comp],0,100000))
            ratio[key]['%02i'%i] = peak_cts[key]['%02i'%i] / compton_cts[key]['%02i'%i]

    
    all_things={}
    all_things['compton_cts']=compton_cts
    all_things['ratio']=ratio
    all_things['peak_cts']=peak_cts
    all_things['tot_counts']=tot_counts
    all_things['angle']=angle
    return(all_things)
