from PyQt5 import QtWidgets,QtCore
from Channel_sorting import sortChannel
from LR_sorting import sortLR
from xml_XY_stitching import xml_XY
from Transpose_then_save2D import trapoSave
import xml_LR_fuser
import sys,os,re,shutil

def find_key_from_meta(all_line_string,key):
    a_line = "nothing should be the same"
    n = -1
    while a_line == "nothing should be the same" and n < len(all_line_string):
        n = n+1
        current_str = all_line_string[n]
        pattern = re.compile(r"[\[](%s)[\]] \: (.*)?\n"%key)
        a_line_all = pattern.findall(current_str)
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
    new_line = "["+ key.replace("\\","") + "]" + " : " + str(value) +"\n"
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

def run_terastitcher(xmlname ,output_folder, volout_plugin, imout_format = "tif",is_onlymerge = False):    
    if is_onlymerge == False:
        string = 'terastitcher --import --projin=\"' + xmlname + '\"'
        os.system(string)
        os.system('terastitcher --displcompute --projin="xml_import.xml"')
        os.system('terastitcher --displproj --projin="xml_displcomp.xml"')
        os.system('terastitcher --displthres --projin="xml_displproj.xml" --threshold=0.7')
        os.system('terastitcher --placetiles --projin="xml_displthres.xml"')
    string = 'terastitcher --merge --projin=\"xml_merging.xml\" --volout=\"' + output_folder + '\" --volout_plugin=\"' +volout_plugin + '\" --imout_format=' + imout_format +' --imout_depth=\"16\" --libtiff_uncompress'
    os.system(string)

def get_text_from_meta(metaFile,key):    
    with open(metaFile,"r") as meta:
        all_lines = meta.readlines()
        [SN,text] = find_key_from_meta(all_lines,key)    
        return text

def get_file_location_of_terastitched_file(root_folder,new_name):    
    isDir = True
    folder = root_folder
    while isDir:
        listdir = os.listdir(folder)        
        for item in listdir:
            new_item = os.path.join(folder,item)
            if os.path.isdir(new_item):
                isDir = True
                folder = new_item
                break
            else:
                isDir = False
    os.chdir(folder)            
    the_file = os.listdir(folder)
    os.rename(the_file[0],new_name)
    shutil.move(new_name,root_folder)
    return os.path.join(root_folder,new_name)
       
class LR_MergeBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.parent = parent
        self.merge_folder = self.parent.file_location + "\LR_fusion"
        self.LR_matchButton = QtWidgets.QPushButton(self)
        self.LR_matchButton.setText("match their dimension and generate xml")
        self.LR_matchButton.clicked.connect(self.prep_LR_merge)

        self.LR_mergeButton = QtWidgets.QPushButton(self)
        self.LR_mergeButton.setText("Merge left and right")
        self.LR_mergeButton.clicked.connect(self.LR_merge)
        #self.LR_mergeButton.setDisabled(True)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.LR_matchButton,0,0,0,1)
        self.layout.addWidget(self.LR_mergeButton,1,0,0,1)
        self.setLayout(self.layout)

    def prep_LR_merge(self):
        left_line = self.parent.DV + " left stitched"
        right_line = self.parent.DV + " left stitched"
        self.left_file = get_text_from_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,left_line)
        self.right_file = get_text_from_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,right_line)
        #self.LR_mergeButton.setDisabled(False)
        xml_LR_fuser.matchLR_to_xml(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,self.merge_folder,self.left_file,self.right_file)
    
    def LR_merge(self):
        key = self.parent.DV + " raw file"
        os.chdir(self.merge_folder)
        os.mkdir("merged")
        run_terastitcher("terastitcher_for_LR.xml","merged","TiledXY|3Dseries")
        output_location = get_file_location_of_terastitched_file(self.merge_folder+"/merged","LR_merged")
        key = self.parent.DV + " merged image"
        edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key,output_location)

class LR_GroupBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None, side = None):
        super().__init__(parent)
        self.side = side
        self.parent = parent
        self.unstitchedFileLabel=QtWidgets.QLabel("Unstitched file location")
        self.unstitchedFileLabel.setMaximumHeight(15)
        self.unstitchedFileLocation = QtWidgets.QLineEdit(self)
        key = parent.DV + " " + side + " file"
        file_location = get_text_from_meta(parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key)
        if file_location != "Not assigned":
            self.unstitchedFileLocation.setText(file_location)

        self.unstitchedFileLocation.setReadOnly(True)
        self.reloadSortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadSortedfilebutton.setText("Browse...")
        self.reloadSortedfilebutton.clicked.connect(self.askdirectory)
        
        self.XYStitchButton = QtWidgets.QPushButton(self)
        self.XYStitchButton.setText("generate xml and stitch")
        self.XYStitchButton.clicked.connect(self.XYstitch)

        self.grouplayout = QtWidgets.QGridLayout()
        self.grouplayout.addWidget(self.unstitchedFileLabel,0,0,1,1)
        self.grouplayout.addWidget(self.reloadSortedfilebutton,0,1,1,1)
        self.grouplayout.addWidget(self.unstitchedFileLocation,1,0,1,2)
        self.grouplayout.addWidget(self.XYStitchButton,2,0,1,2)
        self.setLayout(self.grouplayout)
    
    def askdirectory(self):
        self.SortedFileLocation = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.unstitchedFileLocation.setText(self.SortedFileLocation)

    def XYstitch(self):
        # possible bug: the file location is not end with /Left or /Right
        # xml is in FileLocation, which will be chdir in xml_XY
        # after stitching, the file location for fusion file can be saved to meta file with /LR_fusion appended
        FileLocation = self.unstitchedFileLocation.text()
        os.chdir(FileLocation)
        [meta_data,self.merge_folder] = xml_XY(FileLocation)
        os.chdir(FileLocation)
        os.mkdir("XY_stitched")
        run_terastitcher("terastitcher_for_XY.xml","XY_stitched", "TiledXY|3Dseries")
        for key in meta_data.keys():
            edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile, key, meta_data[key])
        meta_key = self.parent.DV + " " + self.side + " stitched"
        new_file_location = get_file_location_of_terastitched_file(FileLocation+"\XY_stitched","XY_stitched.tif")
        edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,meta_key,new_file_location)

class DVFusionTab(QtWidgets.QWidget):
    def __init__(self, parent = None, channel = None):
        super().__init__(parent)

        self.transpose_in_2D = QtWidgets.QPushButton(self)
        self.transpose_in_2D.setText("pre-processing the image")
        self.transpose_in_2D.clicked.connect(self.transpose_then_save)

        self.open_image_folders = QtWidgets.QPushButton(self)
        self.open_image_folders.setText("open the folders containing images")
        self.open_image_folders.clicked.connect(self.open_folders)

        self.label_WidthShift = QtWidgets.QLabel(parent = self,text = "please enter the shift in width in the image:")
        self.shift_in_Width = QtWidgets.QLineEdit(self)

        self.label_HeightShift = QtWidgets.QLabel(parent = self,text = "please enter the shift in height in the image:")
        self.shift_in_Height = QtWidgets.QLineEdit(self)

        self.generate_DV_xml = QtWidgets.QPushButton(self)
        self.generate_DV_xml.setText("match the dimension of DV images and generate xml")
        self.generate_DV_xml.clicked.connect(self.match_DV_fusion)

        self.fuse_DV = QtWidgets.QPushButton(self)
        self.fuse_DV.setText("DV fusion!!")
        self.fuse_DV.clicked.connect(self.DV_fusion)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.transpose_in_2D, 0,0,1,4)
        self.layout.addWidget(self.open_image_folders, 1,0,1,4)
        self.layout.addWidget(self.label_WidthShift,2,0,1,3)
        self.layout.addWidget(self.shift_in_Width,2,0,3,1)
        self.layout.addWidget(self.label_HeightShift,3,0,1,3)
        self.layout.addWidget(self.shift_in_Height,3,0,3,1)
        self.layout.addWidget(self.generate_DV_xml,4,0,1,4)
        self.layout.addWidget(self.fuse_DV,5,0,1,4)
        self.setLayout(self.layout)        

    def transpose_then_save(self):
        trapoSave()
    
    def open_folders(self):
        pass

    def match_DV_fusion(self):
        pass

    def DV_fusion(self):
        pass

class DVTab(QtWidgets.QWidget):
    def __init__(self,parent = None, DV = None):
        super().__init__(parent)
        self.pars_channelTab = parent
        self.DV = DV

        self.RawFileLabel = QtWidgets.QLabel("raw file directory")
        self.RawFileLocation = QtWidgets.QLineEdit(self)
        self.RawFileLabel.setMaximumHeight(15)

        self.current_line = self.DV + " raw file"
        self.file_location = get_text_from_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,self.current_line)
        if self.file_location != "Not assigned":
            self.file_location = self.file_location + "/"+parent.channel
            self.RawFileLocation.setText(self.file_location)
        
        self.LeftBox = LR_GroupBox(self,side = "left")
        self.LeftBox.setTitle("Left")
        #self.LeftBox.setDisabled(True)

        self.RightBox = LR_GroupBox(self,side = "right")
        self.RightBox.setTitle("Right")
        #self.RightBox.setDisabled(True)

        self.LRMergeBox = LR_MergeBox(self)
        self.LRMergeBox.setTitle("Left-Right merge")
                        
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
        self.tabLayout.addWidget(self.LeftBox,3,0,2,2)
        self.tabLayout.addWidget(self.RightBox,3,2,2,2)
        self.tabLayout.addWidget(self.LRMergeBox,5,0,2,4)
        self.setLayout(self.tabLayout)

    def askdirectory(self):
        self.file_location = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.RawFileLocation.setText(self.file_location)
        edit_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,self.current_line,self.file_location)        

    def splitLR(self):
        sortLR(self.file_location)
        key_left = self.DV+" left file"
        key_right = self.DV+" right file"
        self.left_location = self.file_location + "/Left"
        self.right_location = self.file_location + "/Right"
        edit_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key_left,self.left_location)
        edit_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key_right,self.right_location)
        self.LeftBox.unstitchedFileLocation.setText(self.left_location)
        self.RightBox.unstitchedFileLocation.setText(self.right_location)
        self.LeftBox.setDisabled(False)
        self.RightBox.setDisabled(False)
          
class ChannelTab(QtWidgets.QWidget):
    def __init__(self,parent = None, channel = None):
        super().__init__(parent)
        self.channel = channel
        self.pars_mainWindow = parent
        self.DVtabs = QtWidgets.QTabWidget(parent=self)
        
        sides = ["ventral","dorsal"]
        for side in sides:
            self.DVtabs.addTab(DVTab(parent = self, DV = side),side)
        self.DVtabs.addTab(DVFusionTab(parent = self, channel = channel),"fusion")

        self.DVtabs.resize(600,500)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowTitle("Stitching workpanel")
        self.resize(600,500)
        self.channel_tabs = QtWidgets.QTabWidget(parent=self)

        self.pars_initWindow = parent
        #channel_folders = self.splitChannels()
        channel_folders = ["channel_647"]
        for a_channel_folder in channel_folders:
            self.channel_tabs.addTab(ChannelTab(parent = self,channel = a_channel_folder), a_channel_folder)
        print(self.channel_tabs)
        self.channel_tabs.resize(600,450)

    def splitChannels(self):    
        channel_folder = sortChannel(os.getcwd())
        return channel_folder


class InitWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select your progress")
        self.createWork = QtWidgets.QPushButton(text = "create a new stitching project", parent=self)
        self.createWork.setCheckable(True)
        self.createWork.clicked.connect(self.generateMeta)
        self.continueWork = QtWidgets.QPushButton(text = "continue a stitching project ",parent=self)
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
        self.metaFile = self.DataFolder+"/"+self.metaFile
        if self.side == "ventral":
            edit_meta(self.metaFile,"ventral raw file",self.DataFolder)
        elif self.side == "dorsal":
            self.edit_meta("dorsal raw file",self.DataFolder)       
        self.prerequisiteWidget.hide()
        self.mainWindow = MainWindow(self)
        self.mainWindow.show()
        
    def popupMain(self):
        metaFileName = QtWidgets.QFileDialog.getOpenFileName(self,"select a meta file (.txt) to open a existed project")
        cwd = os.getcwd()
        self.metaFile = os.path.join(cwd,metaFileName[0])
        self.mainWindow = MainWindow(self)    
        """
        with open(self.metaFile,"r") as meta:
            all_lines = meta.readlines()
        pattern = re.compile(r"[\[](.*)[\]] : (.*)")
        all_items = pattern.findall(all_lines)
        
        metas = dict()
        for n in len(all_items[0]):
            metas[all_items[0][n]] = all_items[1][n]
        """
        self.mainWindow.show()

    def prepare_meta(self,filename):
        meta_name = filename + "_meta.txt"
        with open(meta_name,"w") as meta:
            meta.write("=== system parameters ===\n")
            meta.write("[pixel size of x (um)] : \n")
            meta.write("[pixel size of y (um)] : \n")
            meta.write("[z step size (um)] : \n")
            meta.write("[pixel counts in x] : \n")
            meta.write("[pixel counts in y] : \n")
            meta.write("[x positions right] : \n")
            meta.write("[x positions left] : \n")
            meta.write("=== progress ===\n")
            meta.write("=== file location ===\n")
            meta.write("[ventral raw file] : Not assigned\n")
            meta.write("[ventral left file] : Not assigned\n")
            meta.write("[ventral right file] : Not assigned\n")
            meta.write("[ventral left stitched] : Not assigned\n")
            meta.write("[ventral right stitched] : Not assigned\n")
            meta.write("[ventral merged image] : Not assinged\n")
            meta.write("[dorsal raw file] : Not assigned\n")
            meta.write("[dorsal left file] : Not assigned\n")
            meta.write("[dorsal right file] : Not assigned\n")
            meta.write("[dorsal left stitched] : Not assigned\n")
            meta.write("[dorsal right stitched] : Not assigned\n")
            meta.write("[dorsal merged image] : Not assinged\n")

        return meta_name
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = InitWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    