from controller import digibase 
import plotter as plt
import time
import sys
from PyQt4 import QtGui

def main():
    det=digibase()
    app=QtGui.QApplication(sys.argv)
    ag=plt.AppGui()
    det.clear_spectrum()
    det.start_acquisition()
    for i in range(100):
        x=time.time()
        sp=det.get_spectrum()
        det.clear_spectrum()
        print 'time to get: ',(time.time()-x)
        ag.update(sp)
        time.sleep(.1)


    
    raw_input('hit a key to exit')

if __name__=="__main__":
    main()
    

'''    
    plotWidget = pg.plot(title='Testing...')
pg.show()
det.start_acquisition()
plot={}
for i in range(10):
    d=det.get_spectrum()
    plot[i]=pg.plot(range(len(d)),d,clear=True)
    pg.QtGui.QApplication.processEvents()
    time.sleep(1)

raw_input('hit a key to exit')
'''
