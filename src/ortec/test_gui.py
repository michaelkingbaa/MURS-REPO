import sys
import zmq
from PyQt4 import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
import json
from threading import Thread
from gui_daq import daq


class Acquisition(QtCore.QThread):
    def __init__(self):
        QtCore.QThread.__init__(self)
        port = '5556'
        context = zmq.Context()
        self.socket = context.socket(zmq.SUB)
        self.socket.connect("tcp://localhost:%s" % port)
        topicfilter = "1001"
        self.socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

        
    def run(self, flag):
        while flag:
            try:
                messagedata = self.socket.recv(flags=zmq.NOBLOCK)
                topic = messagedata[:5]
                msg = messagedata[5:]
                dict = json.loads(msg)
                for key in dict.keys():
                    print dict[key]['time']
                flag = False
            except zmq.Again as e:
                pass
        return dict
            
class SpectraPlotWidget(pg.PlotWidget):
    '''Plot widget subclassing the pyqtgraph plot widget.
     This plots sin(x + phase) on the interval [-pi, pi].
     If the update function is called, the phase value is incremented and replotted.
     '''
    def __init__(self):
       
        pg.PlotWidget.__init__(self)
        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Spectra')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Channel')
        # axis.enableAutoSIPrefix(False)

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Counts/Second')
        # axis.enableAutoSIPrefix(False)


        # Plot the data
        x = range(1024)
        y = range(1024,0,-1)
        self.line = self.plot(x,y)

    def update(self, dict):
        x = range(1024)
        for key in dict.keys():
            y = dict[key]['spectrum']
            self.line.setData(x,y)
  

    
#if __name__=='__main__':
def gui():
    #thread = Thread(target = daq, kwargs =dict(spoof_digibase = True,time = 10))
    #thread.start()
    #thread.join()
    app = QtGui.QApplication(sys.argv)
    mainWindow = QtGui.QMainWindow()
    # Set pyqtgraph to use white background/black foreground
    # It defaults to black background/white foreground otherwise
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')
     
    plotWidget = SpectraPlotWidget()
    # Add the widget to the window and set the window title
    mainWindow.setCentralWidget(plotWidget)
    mainWindow.setWindowTitle('Simple Plot')
    
    Flag = True

     
    acqThread = Acquisition()
    dict = acqThread.run(Flag)
    plotWidget.update(dict)
     
     
     

    #timer = QtCore.QTimer()
    #timer.timeout.connect(plotWidget.update(dict))
    #loopTime = 20
    #timer.start(loopTime)
    
    mainWindow.show()
    app.exec_()
    #thread.join()
     
     
    

    

   

    
