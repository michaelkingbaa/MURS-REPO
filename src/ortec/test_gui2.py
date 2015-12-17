from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
import zmq
import json
import sys




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
        axis.setLabel('Counts')
        # axis.enableAutoSIPrefix(False)

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Channel')
        # axis.enableAutoSIPrefix(False)
        self.line = self.plot()


class CountsPlotWidget(pg.PlotWidget):
    '''Plot widget subclassing the pyqtgraph plot widget.
     This plots sin(x + phase) on the interval [-pi, pi].
     If the update function is called, the phase value is incremented and replotted.
     '''
    def __init__(self):
        pg.PlotWidget.__init__(self)
        # Enable the plot grid
        self.showGrid(x=True, y=True)

        # Set the title
        self.setTitle('Total Counts')

        # Set the left axis label
        axis = self.getAxis('left')
        axis.setLabel('Counts')
        # axis.enableAutoSIPrefix(False)

        # Set the bottom axis label
        axis = self.getAxis('bottom')
        axis.setLabel('Time')
        # axis.enableAutoSIPrefix(False)
        self.line = self.plot()




def update():
    global spectra, data, total_counts, time
    dict = get_data()
    color_mask = ['w','b','g','y','r','p']
    for i,key in enumerate(dict.keys()):
        if key not in data.keys():
            data[key] = np.ones(1024)
            total_counts[key] = []
            time[key] = []
            #print dict[key]['time']
            #print data
        data[key] += dict[key]['spectrum']
        total_counts[key].append(sum(dict[key]['spectrum']))
        time[key].append(dict[key]['time'])
        if i ==0:
            spectraWidget.clear()
            #spectra.setData(data[key],pen = color_mask[i])
    
        spectraWidget.addItem(pg.PlotCurveItem(data[key], pen=color_mask[i]))
        countWidget.addItem(pg.PlotCurveItem(time[key],total_counts[key],pen=color_mask[i]))
#        counts.setData(time[key],total_counts[key],pen='r')
        app.processEvents()     

def get_data():
    flag = True
    while flag:
        try:
            messagedata = socket.recv(flags=zmq.NOBLOCK)
            topic = messagedata[:5]
            msg = messagedata[5:]
            dict = json.loads(msg)
            flag = False
        except zmq.Again as e:
            pass
    return dict



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWindow = QtGui.QMainWindow()

     # Set pyqtgraph to use white background/black foreground
    # It defaults to black background/white foreground otherwise
    pg.setConfigOption('background', 'w')
    pg.setConfigOption('foreground', 'k')

    spectraWidget = SpectraPlotWidget()
    countWidget = CountsPlotWidget()
    centralWidget = QtGui.QWidget()
    # Add the widget to the window and set the window title
    layout = QtGui.QGridLayout()
    layout.addWidget(spectraWidget, 0, 0)
    layout.addWidget(countWidget, 0,1)
    #mainWindow.setCentralWidget(spectraWidget)
 #   mainWindow.setCentralWidget(countWidget)
    mainWindow.setCentralWidget(centralWidget)
    centralWidget.setLayout(layout)
    mainWindow.setWindowTitle('Simple Plot')

    spectra = spectraWidget.line
    counts = countWidget.line
    

    data = {}
    time = {}
    total_counts = {}
    port = '5556'
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:%s" % port)
    topicfilter = "1001"
    socket.setsockopt(zmq.SUBSCRIBE, topicfilter)

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(10)
    
    #if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #$   QtGui.QApplication.instance().exec_()
    mainWindow.show()
    app.exec_()
