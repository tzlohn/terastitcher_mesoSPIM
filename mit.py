from PyQt5 import QtWidgets,QtCore
from Channel_sorting import sortChannel
from LR_sorting import sortLR
import sys,os

class LR_GroupBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None):
        super().__init__(parent)

        self.unstitchedFileLabel=QtWidgets.QLabel("Unstitched file location")
        self.unstitchedFileLocation = QtWidgets.QLineEdit(self)
        self.unstitchedFileLocation.setReadOnly(True)
        self.reloadSortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadSortedfilebutton.setText("locates the directory")
        self.reloadSortedfilebutton.clicked.connect(self.askdirectory)

        self.XYStitchButton = QtWidgets.QPushButton(self)
        self.XYStitchButton.setText("generate xml and stitch")

        self.grouplayout = QtWidgets.QGridLayout()
        self.grouplayout.addWidget(self.unstitchedFileLabel,0,0)
        self.grouplayout.addWidget(self.reloadSortedfilebutton,0,1)
        self.grouplayout.addWidget(self.unstitchedFileLocation,1,0,1,2)
        self.grouplayout.addWidget(self.XYStitchButton,2,0,1,2)
        self.setLayout(self.grouplayout)
    
    def askdirectory(self):
        self.SortedFileLocation = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.unstitchedFileLocation.setText(self.SortedFileLocation)        

class DVTab(QtWidgets.QWidget):
    def __init__(self,parent = None):
        super().__init__(parent)
        
        self.LeftBox = LR_GroupBox(self)
        self.LeftBox.setTitle("Left")

        self.RightBox = LR_GroupBox(self)
        self.RightBox.setTitle("Right")

        self.LRMergeBox = QtWidgets.QGroupBox(self)
        self.LRMergeBox.setTitle("Left-Right merge")

        self.RawFileLabel = QtWidgets.QLabel("raw file directory")
        self.RawFileLocation = QtWidgets.QLineEdit(self)
        self.RawFileLocation.setReadOnly(True)
        self.reloadUnsortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadUnsortedfilebutton.setText("locates the directory")
        self.reloadUnsortedfilebutton.clicked.connect(self.askdirectory)

        self.LRSplitButton = QtWidgets.QPushButton(self)
        self.LRSplitButton.setText("Split Left and Right")
        self.LRSplitButton.clicked.connect(self.splitLR)

        self.tabLayout = QtWidgets.QGridLayout()
        self.tabLayout.addWidget(self.RawFileLabel,0,0,1,1)
        self.tabLayout.addWidget(self.reloadUnsortedfilebutton,0,1,1,1)
        self.tabLayout.addWidget(self.RawFileLocation,1,0,1,4)
        self.tabLayout.addWidget(self.LRSplitButton,2,0,1,4)
        self.tabLayout.addWidget(self.LeftBox,3,0,4,2)
        self.tabLayout.addWidget(self.RightBox,3,2,4,2)
        self.tabLayout.addWidget(self.LRMergeBox,7,0,2,4)
        self.setLayout(self.tabLayout)

    def askdirectory(self):
        self.unSortedFileLocation = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.RawFileLocation.setText(self.unSortedFileLocation)        

    def splitLR(self):
        #sortLR(os.getcwd())    
        return 0    

class ChannelTab(QtWidgets.QWidget):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.DVtabs = QtWidgets.QTabWidget(parent=self)
        sides = ["ventral","dorsal"]
        for side in sides:
            self.DVtabs.addTab(DVTab(parent),side)

        self.DVtabs.resize(600,450)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowTitle("Stitching workpanel")
        self.channel_tabs = QtWidgets.QTabWidget(parent=self)

        current_folder = os.getcwd()
        channel_folders = self.splitChannels()
        for a_channel_folder in channel_folders:
            self.channel_tabs.addTab(ChannelTab(self), a_channel_folder)

        self.channel_tabs.resize(600,450)

    def splitChannels(self):    
        #channel_folder = sortChannel(os.getcwd())
        channel_folder = ["test1","test2","test3"]
        return channel_folder


class InitWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select your progress")
        self.createWork = QtWidgets.QPushButton(text = "create a new stitching project", parent=self)
        self.createWork.setCheckable(True)
        self.createWork.clicked.connect(self.generateMeta)
        self.continueWork = QtWidgets.QPushButton(text = "open an ongoing stitching project ",parent=self)
        self.continueWork.clicked.connect(self.popupMain)
        self.createWork.setGeometry(QtCore.QRect(10,10,200,50))
        self.continueWork.setGeometry(QtCore.QRect(10,70,200,50))
    
    def generateMeta(self):

        self.createWork.setDisabled(True)
        self.continueWork.setDisabled(True)

        self.DataFolder = QtWidgets.QFileDialog.getExistingDirectory(self,"select the directory where RAW data were stored")
        os.chdir(self.DataFolder)

        self.prerequisiteWidget = QtWidgets.QWidget()
        self.preLayout = QtWidgets.QGridLayout()
        
        self.askSideLabel = QtWidgets.QLabel("please select the side of the images in this directory")
        self.askSideWidget = QtWidgets.QComboBox(self)
        self.askSideWidget.addItems(["ventral","dorsal","nose"])
        
        self.askFilenameLabel = QtWidgets.QLabel("give a name for the stitching project")
        self.askFilename = QtWidgets.QLineEdit(self)

        self.confirmbutton = QtWidgets.QPushButton(self,text = "done")
        self.confirmbutton.clicked.connect(self.getParameters)

        self.preLayout.addWidget(self.askSideLabel, 0, 0)
        self.preLayout.addWidget(self.askSideWidget, 1, 0)
        self.preLayout.addWidget(self.askFilenameLabel, 2, 0)
        self.preLayout.addWidget(self.askFilename, 3, 0)
        self.preLayout.addWidget(self.confirmbutton, 4, 0)
        self.prerequisiteWidget.setLayout(self.preLayout)
        self.prerequisiteWidget.show()
            
    def getParameters(self):
        self.side = self.askSideWidget.currentText()
        self.filename = self.askFilename.text()
        self.prepare_meta(self.filename)
        self.prerequisiteWidget.hide()
        mainWindow = MainWindow(self)
        mainWindow.show()
    
    def popupMain(self):
        self.metaFile = QtWidgets.QFileDialog.getOpenFileName(self,"select a meta file (.txt) to open a existed project")

    def prepare_meta(self,filename):
        meta_name = filename[0] + "_meta.txt"
        with open(meta_name,"w") as meta:
            meta.write("=== system parameters ===\n")
            meta.write("[pixel size of x (um)] :\n")
            meta.write("[pixel size of y (um)] :\n")
            meta.write("[z step size (um)] :\n")
            meta.write("[pixel counts in x] :\n")
            meta.write("[pixel counts in y] :\n")
            meta.write("[x positions_Right] :\n")
            meta.write("[x positions_Left] :\n")
            meta.write("=== progress ===\n")
            meta.write("=== file location ===\n")
            

        
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = InitWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    