import pyqtgraph as pg
import numpy as np
from PyQt4 import QtGui
import time
class AppGui(QtGui.QWidget):
    def __init__(self):
        super(AppGui,self).__init__()
        self.initUI()
        
    def initUI(self):
        self.setGeometry(300, 300, 1024, 768)        

        
        self.setWindowTitle('Ortec Acquisition')    
        self.pGC=pg.PlotWidget(title='Gamma Gross Counts')

        self.pSpectra=pg.PlotWidget(title="Gamma Spectra")

        self._sp_cumm=None
        self._sp_inst=None
        self._gGC=np.array([])
        
        self.layout=QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.pGC,0,0)
        self.layout.addWidget(self.pSpectra, 1,0)
        self.layout.setRowStretch(0,1)
        self.layout.setRowStretch(1,6)
        
        self.show()
        time.sleep(3)

    
    def update(self,spectra):
        self._gGC=np.append(self._gGC,np.sum(spectra,axis=0))
        if self._sp_cumm is not None:
            self._sp_cumm+=spectra
            self._sp_inst=spectra
        else:
            self._sp_cumm=np.array(spectra)
            self._sp_inst=np.array(spectra)
            
        self.pGC.plot(range(len(self._gGC)),self._gGC,clear=True)
        self.pSpectra.plot(range(len(self._sp_cumm)),self._sp_cumm,pen='r',clear=True)
        self.pSpectra.plot(range(len(self._sp_inst)),self._sp_inst)
        pg.QtGui.QApplication.processEvents()

    
