__author__ = 'chivers'

import player as pl
import matplotlib.pyplot as plt
from PyQt4 import QtGui
import sys


class mursSoundEditorWindow(QtGui.QWidget):

    def __init__(self,file1,file2):
        super(mursSoundEditorWindow,self).__init__()
        self.syncObj = mursGPSynch(file1,file2)



class mursGPSynch:

    def __init__(self,file1,file2):
        print "Loading " + file1
        self.c1 = pl.mursClip(file1)
        print "Loading " + file2
        self.c2 = pl.mursClip(file2)
        print "Loading " + file1 + " wav array"
        self.wav1 = self.c1.clip.audio.to_soundarray()
        print "Loading " + file2 +  "wav array"
        self.wav2 = self.c1.clip.audio.to_soundarray()
        print "Completed Load Process"

def main():
    # parse command line options
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mp4file1','-m1',default=None)
    parser.add_argument('--mp4file2','-m2',default=None)
    args = parser.parse_args()

    print args.mp4file1
    print args.mp4file2

    app = QtGui.QApplication(sys.argv)

    if args.mp4file1 and args.mp4file2:
        mainWindow = QtGui.QMainWindow()
        syncWin = mursSoundEditorWindow(args.mp4file1,args.mp4file2)
        mainWindow.setCentralWidget(syncWin)
        mainWindow.setWindowTitle('MURS GoPro Syncronization')
        mainWindow.show()
        app.exec_()
        app.deleteLater()   # For some reason this solves a segfault issue triggered when closing the app
    else:
        print "Require both file1 and file2 for processing"
        exit()

if __name__ == "__main__":
    main()