from controller import digibase 
import pyqtgraph as pg
import time
import sys
from PyQt4 import QtGui

det=digibase()
plotWidget = pg.plot(title='Testing...')
pg.show()
det.start_acquisition()
plot={}
for i in range(5):
    d=det.get_spectrum()
    det.clear_spectrum()
    plot[i]=pg.plot(range(len(d)),d,clear=True)
    pg.QtGui.QApplication.processEvents()
    time.sleep(1)

raw_input('hit a key to exit')
