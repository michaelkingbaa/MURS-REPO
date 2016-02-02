from PyQt4 import QtGui, QtCore
import numpy as np
import pyqtgraph as pg
from pyqtgraph.ptime import time
import zmq
import json
import sys
from pyqtgraph.dockarea import *
from kafka import KafkaConsumer, KafkaClient, SimpleConsumer
sys.path.append('/Users/nicolekelley/git_repos/murs/src/messaging')
from mursavro import mursArrayMessage 



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

class SpectrogramWidget(pg.PlotWidget):
    def __init__(self):
        pg.PlotWidget.__init__(self)
        self.img = pg.ImageView()
        #self.img.setImage(autoRange=True)
        self.img.view.setAspectLocked(False)
        


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


class ButtonWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.startBtn = QtGui.QPushButton('Start Data Acquisition',self)
        self.startBtn.clicked.connect(self.start)
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.startBtn)
        
    def start(self):
        print "hello"
        


def update():
    global spectra, data, total_counts, time
    dict = get_data()
    if dict == 'STOP':
        exit()
           ###FIGURE OUT HOW TO END NICELY
    color_mask = ['w','b','g','y','r','m']
    for i,key in enumerate(dict.keys()):
        if key not in data.keys():
            data[key] = np.ones(1024)
            total_counts[key] = []
            time[key] = []
            #print dict[key]['time']
            #print data
        #keep running average of spectra
        data[key] += dict[key]['spectrum']
        total_counts[key].append(sum(dict[key]['spectrum']))
        time[key].append(dict[key]['time'])
        
        if i ==0:
            spectraWidget.clear()
            #spectra.setData(data[key],pen = color_mask[i])
    
        spectraWidget.addItem(pg.PlotCurveItem(data[key], pen=color_mask[i]))
        countWidget.addItem(pg.PlotCurveItem(time[key],total_counts[key],pen=color_mask[i]))
#        countWidget.addItem(pg.PlotCurveItem(total_counts[key],time[key],pen=color_mask[i]))
        #spectrogramWidget.image(
#        counts.setData(time[key],total_counts[key],pen='r')
        app.processEvents()     

def get_data():
    
    msg = consumer.next()
    #    msg = consumer.next(consumer_timeout_ms=100)
    if msg.value != 'STOP':
        dict = data_handler.decode(msg.value)
        #dict = json.loads(msg.value)
        print dict['15226068']['time']

    else:
        return 'STOP'
    #self.signal.emit(dict) #to emit to spectrogram
    return dict



app = QtGui.QApplication(sys.argv)
mainWindow = QtGui.QMainWindow()
area = DockArea()
mainWindow.setCentralWidget(area)
mainWindow.resize(1000,1200)
mainWindow.setWindowTitle('MURS Real Time Data')

d1 = Dock('Specta',size=(500,300)) #spectra plot
d2 = Dock('Total Counts',size=(500,300)) #total counts plot
#d3 = Dock('Controls',size=(2,4))
#d4 = Dock('Waterfall',size=(300,1200))
area.addDock(d1, 'bottom')
area.addDock(d2, 'top')
#area.addDock(d3, 'top')
#area.addDock(d4,'left')


    
# Set pyqtgraph to use white background/black foreground
# It defaults to black background/white foreground otherwise
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')


spectraWidget = SpectraPlotWidget()
countWidget = CountsPlotWidget()
d1.addWidget(spectraWidget)
d2.addWidget(countWidget)
    
#buttonWidget = ButtonWidget()
#d3.addWidget(buttonWidget)

#spectrogramWidget = SpectrogramWidget()
#d4.addWidget(spectrogramWidget)

spectra = spectraWidget.line
counts = countWidget.line

    

data = {}
time = {}
total_counts = {}

#KAFKA consumer
wanted_client = 'localhost:9092'
data_schema = '../messaging/mursArray.avsc'
data_topic = 'data_messages'
while not 'data_messages' in KafkaClient(wanted_client).topic_partitions.keys():
        print 'waiting for data Client'
        time.sleep(1)
consumer = KafkaConsumer(data_topic, bootstrap_servers=wanted_client)
#print consumer.get_partition_offsets('data_messages',0,-1,1)

data_handler = mursArrayMessage(data_schema, data_topic, wanted_client)


#For sending button messages
port = '5556'
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:%s" % port)
topic = '1001'




timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0.5)


#print "sending message"
#socket.send(topic+'Hola')

if __name__ == '__main__':
    mainWindow.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
    
    app.exec_()
