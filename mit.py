from PyQt5 import QtWidgets,QtCore
from Channel_sorting import sortChannel
from LR_sorting import sortLR
import sys,os,re

def find_key_from_meta(all_line_string,key):
    a_line = "nothing should be the same"
    n = -1
    while a_line != key and n < len(all_line_string):
        n = n+1
        pattern = re.compile(r"[\[](%s)[\]] \:(.*)?\n"%key)
        a_line_all = pattern.findall(all_line_string[n])
        if not a_line_all:
            a_line = "nothing should be the same"
        else: 
            a_line = a_line_all[0][0]
            value = a_line_all[0][1]
    
    if not value:
        return [n,"not_a_value"] 
    else:    
        return [n,value]

def edit_meta(metaFile,key,value):
    new_line = "["+ key + "]" + " : " + str(value) +"\n"
    meta = open(metaFile,"r")
    all_lines = meta.readlines()
    meta.close()
    [line_sn,value] = find_key_from_meta(all_lines,key)
    all_lines[line_sn] = new_line

    if line_sn < len(all_lines):
        with open(metaFile,"w") as meta:
            meta.writelines(all_lines)
    """        
    elif line_sn == len(all_lines):
        with open(self.metaFile,"a") as meta:
            meta.writelines(all_lines)
    """

class LR_GroupBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None, side = None):
        super().__init__(parent)

        self.unstitchedFileLabel=QtWidgets.QLabel("Unstitched file location")
        self.unstitchedFileLocation = QtWidgets.QLineEdit(self)
        self.unstitchedFileLocation.setReadOnly(True)
        self.reloadSortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadSortedfilebutton.setText("Browse...")
        self.reloadSortedfilebutton.clicked.connect(self.askdirectory)

        self.XYStitchButton = QtWidgets.QPushButton(self)
        self.XYStitchButton.setText("generate xml and stitch")
        self.XYStitchButton.clicked.connect(self.XYstitch)

        self.grouplayout = QtWidgets.QGridLayout()
        self.grouplayout.addWidget(self.unstitchedFileLabel,0,0)
        self.grouplayout.addWidget(self.reloadSortedfilebutton,0,1)
        self.grouplayout.addWidget(self.unstitchedFileLocation,1,0,1,2)
        self.grouplayout.addWidget(self.XYStitchButton,2,0,1,2)
        self.setLayout(self.grouplayout)
    
    def askdirectory(self):
        self.SortedFileLocation = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.unstitchedFileLocation.setText(self.SortedFileLocation)

    def XYstitch(self):
        pass        

class DVTab(QtWidgets.QWidget):
    def __init__(self,parent = None, DV = None):
        super().__init__(parent)
        self.pars_channelTab = parent
        self.DV = DV

        self.LeftBox = LR_GroupBox(self,side = "Left")
        self.LeftBox.setTitle("Left")
        self.LeftBox.setDisabled(True)

        self.RightBox = LR_GroupBox(self,side = "Right")
        self.RightBox.setTitle("Right")
        self.RightBox.setDisabled(True)

        self.LRMergeBox = QtWidgets.QGroupBox(self)
        self.LRMergeBox.setTitle("Left-Right merge")

        self.RawFileLabel = QtWidgets.QLabel("raw file directory")
        self.RawFileLocation = QtWidgets.QLineEdit(self)

        with open(self.pars_channelTab.pars_initWindow.metaFile,"r") as meta:
            self.current_line = self.DV + " raw file"
            all_lines = meta.readlines()
            [SN,file_location] = find_key_from_meta(all_lines,self.current_line)
            if file_location != "Not assigned":
                self.RawFileLocation.setText(file_location)
                self.file_location = file_location
        
        self.RawFileLocation.setReadOnly(True)
        self.reloadUnsortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadUnsortedfilebutton.setText("Browse...")
        self.reloadUnsortedfilebutton.clicked.connect(self.askdirectory)

        self.LRSplitButton = QtWidgets.QPushButton(self)
        self.LRSplitButton.setText("Split Left and Right, and save to tiff")
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
        self.file_location = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.RawFileLocation.setText(self.file_location)
        edit_meta(self.pars_channelTab.pars_initWindow.metaFile,self.current_line,self.file_location)        

    def splitLR(self):
        #sortLR(self.file_location)
        key_left = self.DV+" left file"
        key_right = self.DV+" right file"
        self.left_location = self.file_location + "/Left"
        self.right_location = self.file_location + "/Right"
        edit_meta(self.pars_channelTab.pars_initWindow.metaFile,key_left,self.left_location)
        edit_meta(self.pars_channelTab.pars_initWindow.metaFile,key_right,self.right_location)
        self.LeftBox.unstitchedFileLocation.setText(self.left_location)
        self.RightBox.unstitchedFileLocation.setText(self.right_location)
        self.LeftBox.setDisabled(False)
        self.RightBox.setDisabled(False)
          
class ChannelTab(QtWidgets.QWidget):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.pars_mainWindow = parent
        self.DVtabs = QtWidgets.QTabWidget(parent=self)
        
        sides = ["ventral","dorsal"]
        for side in sides:
            self.DVtabs.addTab(DVTab(parent, DV = side),side)

        self.DVtabs.resize(600,450)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowTitle("Stitching workpanel")
        self.channel_tabs = QtWidgets.QTabWidget(parent=self)

        self.pars_initWindow = parent
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
        self.metaFile = self.prepare_meta(self.filename)
        if self.side == "ventral":
            edit_meta(self.metaFile,"ventral raw file",self.DataFolder)
        elif self.side == "dorsal":
            self.edit_meta("dorsal raw file",self.DataFolder)       
        self.prerequisiteWidget.hide()
        self.mainWindow = MainWindow(self)
        self.mainWindow.show()
        
    def popupMain(self):
        self.metaFile = QtWidgets.QFileDialog.getOpenFileName(self,"select a meta file (.txt) to open a existed project")

    def prepare_meta(self,filename):
        meta_name = filename + "_meta.txt"
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
            meta.write("[ventral raw file] : Not assigned\n")
            meta.write("[ventral left file] : Not assigned\n")
            meta.write("[ventral right file] : Not assigned\n")
            meta.write("[dorsal raw file] : Not assigned\n")
            meta.write("[dorsal left file] : Not assigned\n")
            meta.write("[dorsal right file] : Not assigned\n")

        return meta_name
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = InitWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    