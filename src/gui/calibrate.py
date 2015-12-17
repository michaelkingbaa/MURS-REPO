import sys
sys.path.append('../')
from ortec.controller import DigiBaseController
from pyqtgraph.Qt import QtGui,QtCore
import pyqtgraph as pg
import warnings
import sys
import numpy as np
import time
import argparse
import zmq
import json


class AcquisitionThread(QtCore.QThread):
    def __init__(self,controller=None):
        QtCore.QThread.__init__(self)
        #Subsribing to ZMQ Thread
        self._context=zmq.Context()
        self._socket=self._context.socket(zmq.SUB)
        self._socket.connect("tcp://localhost:5556")
        topicfilter = "1001"
        self._socket.setsockopt(zmq.SUBSCRIBE, topicfilter)
        self._runFlag=False

    def run(self):
#        for s in range(1):
        while self._runFlag:
            #print 'Acquiring Sample {0}'.format(s)
            #print 'Acquiring Sample'
            try:
                print 'recieving packets'
                pkt=self._socket.recv()
            except:
                print 'got an exception'
                break
            topic=pkt[:5]
            msg=pkt[5:]
            
            #topic,msg=pkt.split('{')
            print 'Topic: ',topic
            print 'Msg: ', msg
            sample=json.loads(msg)
            print 'Got Sample'
            self.emit( QtCore.SIGNAL('New Sample'),sample )
        return

    def startRun(self):
        self._runFlag=True
        self.run()

    def stopRun(self):
        self._runFlag=False

class DAQWindow(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)

        #Setting up main Window
        self.setGeometry(300,300,1024,768)
        self.setWindowTitle('This is a test')
        self.layout=QtGui.QHBoxLayout()

        #Control Panel (left side)
        cntrlPanelFrame=QtGui.QFrame()
        cntrlPanelFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self._cntrlPanelLayout=QtGui.QVBoxLayout()
        cntrlPanelFrame.setLayout(self._cntrlPanelLayout)
        self.layout.addWidget(cntrlPanelFrame)

        #Plot Panel (Right Side)
        self._pltLayout=QtGui.QGridLayout()
        self.layout.addLayout(self._pltLayout)

        self.setLayout(self.layout)

        
        #Setting up Control Panel Layout
        hvframe=QtGui.QFrame()
        hvframe.setFrameShape(QtGui.QFrame.StyledPanel)
        self._cntrlPanelLayout.addWidget(hvframe)
        
        hvpanel=QtGui.QFormLayout()
        hvframe.setLayout(hvpanel)
        
        self._cbDetSelect = QtGui.QComboBox(self)
        self._cbDetSelect.addItem("None")
        hvpanel.addRow("Detector",self._cbDetSelect)
        
        self._hvInput=QtGui.QLineEdit(self)
        hvpanel.addRow("New High Voltage: ",self._hvInput)

        self._btnHVSet = QtGui.QPushButton("Set HV")
        self._btnHVSet.clicked.connect(self.setHV)       

        self._btnHVCancel = QtGui.QPushButton("Cancel")
        self._btnHVCancel.clicked.connect(self.cancelHV)       

        hvpanel.addRow(self._btnHVSet,self._btnHVCancel)
        
        #Plotting Tools
        plotToolFrame=QtGui.QFrame()
        plotToolFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self._cntrlPanelLayout.addWidget(plotToolFrame)

        plotToolLayout=QtGui.QFormLayout()
        plotToolFrame.setLayout(plotToolLayout)
        
        self._sourceSelect=QtGui.QComboBox(self)
        self._sourceSelect.addItem("None")
        self._sourceSelect.addItem("Cs-137")
        self._sourceSelect.addItem("Co-60")
        self._sourceSelect.addItem("Eu-152")
        self._sourceSelect.addItem("Ra-226")
        self._sourceSelect.addItem("Background")
        self._sourceSelect.currentIndexChanged.connect(self.updateSourceLines)

        #list of current sources being drawn
        self._sourcesDrawn=[]
        self._sources={'Cs-137':{'color':'r',
                                 'energies':[661.657]},
                       'Co-60':{'color':'y',
                                'energies':[1173.237,1332.501]},
                       'Eu-152':{'color':'b',
                                 'energies':[1408.006, 39.9063, 121.7817, 344.2785, 778.904, 964.079, ]},
                       'Th-232':{'color':'v',
                                 'energies':[2614.533, 238.632, 583.191]},
                       'Ra-226':{'color':'m',
                                 'energies':[609.312, 78.27083233, 295.224, 351.932, 1120.287, 1238.11,1388.26552846, 1758.93149563, 2204.21, 2447.86]},
                       'Background':{'color':'g',
                                     'energies':[1460.83,2614.533]}
        }

        self._sourceMultiSelectBox=QtGui.QCheckBox("Show Multiple")
        self._btnSourceClear=QtGui.QPushButton("Clear")
        self._btnSourceClear.clicked.connect(self.clearSourceLines)

        plotToolLayout.addRow("Source: ",self._sourceSelect)
        plotToolLayout.addRow("",self._sourceMultiSelectBox)
        plotToolLayout.addRow("",self._btnSourceClear)
        
        
        
        
        acqBtnLayout=QtGui.QHBoxLayout()
        self._btnStart=QtGui.QPushButton("Start")
        self._btnStart.clicked.connect(self.startAcq)
        acqBtnLayout.addWidget(self._btnStart)

        self._btnStop=QtGui.QPushButton("Stop")
        self._btnStop.clicked.connect(self.stopAcq)
        acqBtnLayout.addWidget(self._btnStop)

        self._btnClear=QtGui.QPushButton("Clear")
        self._btnClear.clicked.connect(self.clearSpectrum)
        acqBtnLayout.addWidget(self._btnClear)
        self._cntrlPanelLayout.addLayout(acqBtnLayout)

        
        #self._cntrlPanelLayout.addWidget(self._cbDetSelect,0,0)
        
        #self._cntrlPanelLayout.addWidget(self._hvInput,0,1)

        #self._cntrlPanelLayout.addWidget(self._btnHVSet,1,0)



        #Setting up Plot Layout
        self._pwSpectrum=pg.PlotWidget(title='Spectrum')
        self._pwSpectrum.plot(range(1024),np.zeros((1024,)))
        self._pwSpectrumLog=pg.PlotWidget(title='Log Spectrum')
        self._pwSpectrumLog.plot(range(1024),np.ones((1024,)))
        self._pwGGC=pg.PlotWidget(title='Gamma Gross Counts')
        
        self._pltLayout.addWidget(self._pwSpectrum,0,0)
        self._pltLayout.addWidget(self._pwSpectrumLog,1,0)
        self._pltLayout.addWidget(self._pwGGC,2,0)
        self._pltLayout.setRowStretch(0,3)
        self._pltLayout.setRowStretch(1,3)
        self._pltLayout.setRowStretch(2,1)

        #Making Initial Plots
        self._dets=[]
        self._spSum={}
        self._times={}
        self._gGC={}
        self.show()
        self._colors=['w','r','b','y','g','m']

    def startAcq(self):
        print 'Starting Acquisition'
        self.emit( QtCore.SIGNAL('Start Acquisition') )

    def stopAcq(self):
        print 'Stopping Acquisition'
        self.emit( QtCore.SIGNAL('Stop Acquisition') )

        
    def clearSpectrum(self):
        print 'Clearing Spectrum'
        self.updatePlots(sample=None)

    def setDetectors(self,detList):
        for d in detList:
            self._dets.append(d)
            self._cbDetSelect.addItem(d)
    def addDetector(self,det):
        self._dets.append(det)
        self._cbDetSelect.addItem(det)

    def setHV(self):
        det=str(self._cbDetSelect.currentText())
        hv=float(self._hvInput.text())
        if hv >0 and hv <1200.:
            sig={'det':det,'hv':hv}
            self.emit( QtCore.SIGNAL('Set HV'),sig )
            print 'Setting High Voltage for {0} to {1} V'.format(det,hv)
        else:
            warnings.warn('HV must be between 0-1200V...ignorning input: {0}'.format(hv))

    def cancelHV(self):
        self._hvInput.setText('')

    def updateSourceLines(self,e):
        sourceName=str(self._sourceSelect.itemText(e))
        print 'UpdateSourceLines',sourceName,len(self._sourcesDrawn)
        if len(self._sourcesDrawn) >0:
            print 'checkin multibox'
            if not self._sourceMultiSelectBox.isChecked():
                warnings.warn('Cannot Draw Source...multi source is not checked')
                return

        self._sourcesDrawn.append(sourceName)
        print 'Calling draw: ',sourceName
        self.drawSourceLines([sourceName])


    def drawSourceLines(self,sourceList):
        print 'Source List to Draw: ',sourceList
        for src in sourceList:
            channels=getChannelFromEnergy(self._sources[src]['energies'])
            for ch in channels:
                self._pwSpectrum.addLine(x=ch,pen=self._sources[src]['color'])
                self._pwSpectrumLog.addLine(x=ch,pen=self._sources[src]['color'])
        
    def clearSourceLines(self):
        print 'Clearing Source Lines'
        self._sourcesDrawn=[]
        self.drawCurrentSpectra()

    def drawCurrentSpectra(self):
        for i,det in enumerate(self._spSum.keys()):
            if i is 0:
                cF=True
            else:
                cF=False
            self._pwSpectrum.plot(range(len(self._spSum[det])),self._spSum[det],clear=cF,pen=self._colors[i % len(self._colors)])
            self._pwSpectrumLog.plot(range(len(self._spSum[det])),self._spSum[det],clear=cF,pen=self._colors[i % len(self._colors)])
            self._pwSpectrumLog.setLogMode(y=True)
            self._pwGGC.plot(self._times[det],self._gGC[det],clear=cF,pen=self._colors[i % len(self._colors)])
            
        
    def updatePlots(self,sample=None):
        if sample is None:
            #If no sample...clearing spectrum
            for det in self._spSum.keys():
                self._spSum[det]=np.ones((1024,),dtype=np.int)
        else:
            for i,det in enumerate(sample.keys()):
                if det not in self._spSum.keys():
                    print 'Adding New Detector to GuiWindow'
                    if det not in self._dets:
                        self.addDetector(det)
                    self._spSum[det]=np.ones((1024,),dtype=np.int)
                    self._times[det]=[]
                    self._gGC[det]=[]


                self._spSum[det]+=sample[det]['spectrum']
                self._times[det].append(sample[det]['time'])
                self._gGC[det].append(np.sum(sample[det]['spectrum'],axis=0))


        #Updating Plots
        self.drawCurrentSpectra()
        self.drawSourceLines(self._sourcesDrawn)
        pg.QtGui.QApplication.processEvents()
        return
    
        
if __name__=="__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c","--check",help="Only check GUI...will exit after check",action="store_true")
    args=parser.parse_args()
    
    app=QtGui.QApplication(sys.argv)
    dg=DAQWindow()

    if args.check:
        raw_input('Hit Enter to Exit')
        exit()

    #dbc=DigiBaseController()


    #dg.setDetectors(dbc.getDetList())
    acqThread=AcquisitionThread(controller=None)
    dg.connect(acqThread, QtCore.SIGNAL("New Sample"), dg.updatePlots)
    #dg.connect(dg,QtCore.SIGNAL("Set HV"),dbc.setHV)
    dg.connect(dg,QtCore.SIGNAL("Start Acquisition"), acqThread.startRun)
    dg.connect(dg,QtCore.SIGNAL("Stop Acquisition"), acqThread.stopRun)
    acqThread.start()
    app.exec_()
    #emc.closeSensors()

