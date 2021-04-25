from PyQt5 import QtWidgets,QtCore
from Channel_sorting import sortChannel
from LR_sorting import sortLR
from xml_XY_stitching import xml_XY
from Teratranspose import teratranspose
import xml_LR_merge
import xml_DV_fusion
import sys,os,re,shutil,glob,time,math
from psutil import virtual_memory
from multiprocessing import Process

def find_key_from_meta(all_line_string,key):
    #print(key)
    a_line = "nothing should be the same"
    n = -1
    while a_line == "nothing should be the same" and n < len(all_line_string):
        n = n+1
        current_str = all_line_string[n]
        pattern = re.compile(r"[\[](%s)[\]]( \:)? (.*)?\n"%key)
        a_line_all = pattern.findall(current_str)
        if not a_line_all:
            a_line = "nothing should be the same"
        else: 
            a_line = a_line_all[0][0]
            value = a_line_all[0][-1]
    
    if not value:
        return [n,"not_a_value"] 
    else:    
        return [n,value]

def edit_meta(metaFile,key,value):
    new_line = "["+ key.replace("\\","") + "]" + " : " + str(value) +"\n"
    meta = open(metaFile,"r")
    all_lines = meta.readlines()
    meta.close()
    [line_sn,old_value] = find_key_from_meta(all_lines,key)
    if old_value != "Not assigned" and old_value != "not_a_value" and old_value != str(value):
        msg = "\"%s\" has been assigned to %s."%(key,old_value)
        msgWindow = QtWidgets.QMessageBox()
        msgWindow.setIcon(QtWidgets.QMessageBox.Question)
        msgWindow.setWindowTitle("Replace value in meta")
        msgWindow.setText(msg)
        msgWindow.setInformativeText("Do you want to update it to the new value?")
        msgWindow.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        
        retval = msgWindow.exec_()
        if retval == 16384: # 16384 is the value for QMessageBox.Yes
            all_lines[line_sn] = new_line
            print("\"%s\" is changed from %s to %s"%(key, old_value, str(value)))
            write = True
        else:
            write = False
        #print("%s has been assigned to %s. Please change it in meta editor\n"%(key,old_value))
    else:
        all_lines[line_sn] = new_line
        write = True
    
    if write:
        if line_sn < len(all_lines):
            with open(metaFile,"w") as meta:
                meta.writelines(all_lines)

def run_terastitcher(xmlname ,output_folder, volout_plugin, file_size = 0, imout_format = "tif",is_onlymerge = False):    
    if is_onlymerge == False:
        if not os.path.exists("xml_import.xml"):
            string = 'terastitcher --import --projin=\"' + xmlname + '\"'
            os.system(string)

        mem = virtual_memory()
        if not file_size == 0:
            slice_no = mem.free*0.8/file_size//4
            #print(slice_no)
            time.sleep(1)

        if output_folder == "XY_stitched":
            file_size = 2048*2048*2
            slice_no = mem.free*0.8/file_size//4
            if(slice_no > 350):
                slice_no = 350
            string = 'terastitcher --displcompute --projin="xml_import.xml" --sD=0 --subvoldim=%d'%int(slice_no)            
        elif output_folder == "DV_Fusion":
            string = 'terastitcher --displcompute --projin="xml_import.xml" --sV=75 --sH=75 --sD=75 --subvoldim=%d'%int(slice_no)
        elif file_size == 0:
            string = 'terastitcher --displcompute --projin="xml_import.xml"'
        else:
            string = 'terastitcher --displcompute --projin="xml_import.xml" --subvoldim=%d'%int(slice_no)
        
        if not os.path.exists("xml_displcomp.xml"):
            value = os.system(string)
            while value != 0:
                slice_no = slice_no-5
                string = 'terastitcher --displcompute --projin="xml_import.xml" --sD=0 --subvoldim=%d'%int(slice_no)
                value = os.system(string)
            print("subvoldim = %d"%slice_no)     

        if not os.path.exists("xml_merging.xml"):
            os.system('terastitcher --displproj --projin="xml_displcomp.xml"')
            if output_folder == "DV_Fusion":
                os.system('terastitcher --displthres --projin="xml_displproj.xml" --threshold=0.5')
            else:
                os.system('terastitcher --displthres --projin="xml_displproj.xml" --threshold=0.7')
            os.system('terastitcher --placetiles --projin="xml_displthres.xml"')
        
        string = 'terastitcher --merge --projin=\"xml_merging.xml\" --volout=\"' + output_folder + '\" --volout_plugin=\"' +volout_plugin + '\" --imout_format=' + imout_format +' --imout_depth=\"16\" --libtiff_uncompress'
        os.system(string)
    else:
        string = 'terastitcher --merge --projin=\"'+ xmlname + '\" --volout=\"' + output_folder + '\" --volout_plugin=\"' +volout_plugin + '\" --imout_format=' + imout_format +' --imout_depth=\"16\" --libtiff_uncompress'
        os.system(string)
    
    if output_folder != "DV_Fusion":
        print("Moving the stitched file to an appropriate directory...")

def xml_edit_directory(xml_file,dirs):
    with open(xml_file,"r") as xml:
        texts = xml.readlines()
        xml.close()
    
    result = []
    n = -1
    while not result:
        n = n+1
        pattern = re.compile(r"    <stacks_dir value=(.*)\n")
        result = pattern.findall(texts[n])
        if result:
            result = result[0]

    new_line = '    <stacks_dir value="%s" />\n'%dirs
    texts[n] = new_line

    result = []
    n = -1    
    while not result:
        n = n+1
        if n >= len(texts):
            break
        pattern = re.compile(r"(    <mdata_bin.*)")
        result = pattern.findall(texts[n])
        if result:
            result = result[0]
    
    if n != len(texts):
        del texts[n]
        #texts.remove(result)

    with open(xml_file,"w") as xml:
        xml.writelines(texts)

def get_text_from_meta(metaFile,key):    
    with open(metaFile,"r") as meta:
        all_lines = meta.readlines()
        [SN,text] = find_key_from_meta(all_lines,key)    
        return text

def goTerminalDir(root_folder):
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
    return folder    

def get_file_location_of_terastitched_file(root_folder,new_name):    
    folder = goTerminalDir(root_folder)
    os.chdir(folder)            
    the_file = os.listdir(folder)
    os.rename(the_file[0],new_name)
    shutil.move(new_name,root_folder)
    return os.path.join(root_folder,new_name)

def rename_stitched_2D(root_folder,channel_id):
    folder = goTerminalDir(root_folder)
    os.chdir(folder)
    all_tif = glob.glob("*.tif")
    for idx,a_tif in enumerate(all_tif):
        name_id= (len(str(len(all_tif)))-len(str(idx)))*"0"+str(idx)
        new_name = "C0"+str(channel_id)+"_Z"+name_id+".tif"
        os.rename(a_tif,new_name)
       
class LR_MergeBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.parent = parent
        self.merge_folder = self.parent.file_location + "/LR_fusion"
        self.meta_file = parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile
        
        self.Left_stitched_label = QtWidgets.QLabel(self,text = "Stitched left image:")
        self.Left_stitched_file = QtWidgets.QLineEdit(self)
        self.browse_left_stitched = QtWidgets.QPushButton(self)
        self.browse_left_stitched.setText("Browse...")
        self.browse_left_stitched.clicked.connect(lambda key = "left",key2 = "left": self.askFile(key,key2))
        
        key = self.parent.pars_channelTab.channel + " " +parent.DV + " left stitched"
        file_location = get_text_from_meta(self.meta_file,key)
        if file_location != "Not assigned":
            self.Left_stitched_file.setText(file_location)
        self.Left_stitched_file.setReadOnly(True)

        self.Right_stitched_label = QtWidgets.QLabel(self,text ="Stitched right image:")
        self.Right_stitched_file = QtWidgets.QLineEdit(self)
        self.browse_right_stitched = QtWidgets.QPushButton(self)
        self.browse_right_stitched.setText("Browse...")
        self.browse_right_stitched.clicked.connect(lambda key = "right", key2 = "right": self.askFile(key,key2))
        
        key = self.parent.pars_channelTab.channel + " " +parent.DV + " right stitched"
        file_location = get_text_from_meta(self.meta_file,key)
        if file_location != "Not assigned":
            self.Right_stitched_file.setText(file_location)
        self.Right_stitched_file.setReadOnly(True)

        self.middle_shift_label = QtWidgets.QLabel(self,text ="Middle position:")
        self.middle_shift = QtWidgets.QLineEdit(self)
        
        key = self.parent.DV + " middle of x"
        middle_x = get_text_from_meta(self.meta_file,key)
        if not middle_x == "not_a_value":
            self.middle_shift.setText(middle_x)
        else:
            self.middle_shift.setText("0")
        if not self.parent.pars_channelTab.is_main_channel:
            self.middle_shift.setDisabled(True)    

        self.LR_matchButton = QtWidgets.QPushButton(self)
        self.LR_matchButton.setText("match their dimension and generate xml")
        self.LR_matchButton.clicked.connect(self.prep_LR_merge)

        self.LR_mergeButton = QtWidgets.QPushButton(self)
        self.LR_mergeButton.setText("merge left and right")
        self.LR_mergeButton.clicked.connect(self.LR_merge)
        #self.LR_mergeButton.setDisabled(True)
        
        self.Left_stitched_label.setGeometry(35,20,150,25)
        self.browse_left_stitched.setGeometry(455,20,80,25)
        self.Left_stitched_file.setGeometry(35,50,500,25)
        self.Right_stitched_label.setGeometry(35,85,150,25)
        self.browse_right_stitched.setGeometry(455,85,80,25)
        self.Right_stitched_file.setGeometry(35,115,500,25)
        self.middle_shift_label.setGeometry(35,150,80,25)
        self.middle_shift.setGeometry(130,150,80,25)
        self.LR_matchButton.setGeometry(35,180,500,25)
        self.LR_mergeButton.setGeometry(35,210,500,25)
        """
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.LR_matchButton,0,0,0,1)
        self.layout.addWidget(self.LR_mergeButton,1,0,0,1)
        self.setLayout(self.layout)
        """

    def askFile(self,key2,key):
        self.FileLocation = QtWidgets.QFileDialog.getOpenFileName(self)
        if key == "right":
            self.Right_stitched_file.setText(self.FileLocation[0])
        if key == "left":
            self.Left_stitched_file.setText(self.FileLocation[0])    
        meta_file = self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile
        kw = self.parent.pars_channelTab.channel+ " " + self.parent.DV + " " + key + " "+ "stitched"
        edit_meta(meta_file,kw,self.FileLocation[0])

    def prep_LR_merge(self):
        self.left_file = self.Left_stitched_file.text()
        self.right_file = self.Right_stitched_file.text()
        """
        meta_file = self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile
        merge_proc = Process(target=xml_LR_merge.matchLR_to_xml, args=(meta_file,self.merge_folder,self.left_file,self.right_file,self.parent.pars_channelTab.is_main_channel,self.parent.DV)) 
        parameters = merge_proc.start()
        """
        middle_x = float(self.middle_shift.text())
        parameters = xml_LR_merge.matchLR_to_xml\
            (self.meta_file,self.merge_folder,self.left_file,self.right_file,self.parent.pars_channelTab.is_main_channel,self.parent.DV, pos_zero = middle_x)
        print("preprocessing for Left-Right merging is finished.")
        if parameters != False:
            parameters.append(middle_x)
            keys = [" left cutting pixel"," right cutting pixel"," left overlap"," right overlap"," LR pixel difference in x"," LR pixel difference in y", " middle of x" ]
            for n in range(len(parameters)):
                par_key = self.parent.DV + keys[n]
                edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,par_key,parameters[n])

    def LR_merge(self):
        key = self.parent.DV + " raw file"
        os.chdir(self.merge_folder)
        if not os.path.isdir("merged"):
            os.mkdir("merged")
        os.chdir("right_rot")
        tifnames = glob.glob("*.tif")
        single_file_size = os.stat(tifnames[0]).st_size
        os.chdir(self.merge_folder)
        if self.parent.pars_channelTab.is_main_channel:
            run_terastitcher("terastitcher_for_LR.xml","merged","TiledXY|3Dseries",single_file_size)
            key = self.parent.DV + " LR merged"
            edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key,self.merge_folder+"/xml_merging.xml")
        else:
            with open(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,"r") as meta:
                im_info = meta.readlines()
                key = self.parent.DV + " LR merged" 
                [sn,xml_file] = find_key_from_meta(im_info,key)
                current_xml = shutil.copy(xml_file,self.merge_folder)
                xml_edit_directory(current_xml,self.merge_folder)
            run_terastitcher(current_xml,"merged","TiledXY|3Dseries",single_file_size,is_onlymerge=True)            
        output_location = get_file_location_of_terastitched_file(self.merge_folder+"/merged","LR_merged.tif")
        print("LR merging is done.")
        key = self.parent.pars_channelTab.channel + " " + self.parent.DV + " merged image"
        edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key,output_location)

class LR_GroupBox(QtWidgets.QGroupBox):
    def __init__(self,parent = None, side = None):
        super().__init__(parent)
        self.side = side
        self.parent = parent
        self.unstitchedFileLabel=QtWidgets.QLabel("Unstitched file location")
        self.unstitchedFileLabel.setMaximumHeight(15)
        self.unstitchedFileLocation = QtWidgets.QLineEdit(self)
        key = self.parent.pars_channelTab.channel + " " +parent.DV + " " + side + " file"
        file_location = get_text_from_meta(parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,key)
        if file_location != "Not assigned":
            self.unstitchedFileLocation.setText(file_location)

        self.unstitchedFileLocation.setReadOnly(True)
        self.reloadSortedfilebutton = QtWidgets.QPushButton(self)
        self.reloadSortedfilebutton.setText("Browse...")
        self.reloadSortedfilebutton.clicked.connect(self.askdirectory)
        
        self.XYStitchButton = QtWidgets.QPushButton(self)
        self.XYStitchButton.setText("generate xml and stitch in XY")
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
  
        meta_file = self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile
        kw = self.parent.pars_channelTab.channel+ " " + self.parent.DV + " " + self.side + " "+ "file"
        edit_meta(meta_file,kw,self.SortedFileLocation)

    def XYstitch(self):
        # possible bug: the file location is not end with /Left or /Right
        # xml is in FileLocation, which will be chdir in xml_XY
        # after stitching, the file location for fusion file can be saved to meta file with /LR_fusion appended
        FileLocation = self.unstitchedFileLocation.text()
        os.chdir(FileLocation)
        if not os.path.isdir("XY_stitched"):
            os.mkdir("XY_stitched")
        if self.parent.pars_channelTab.is_main_channel:
            [meta_data,self.merge_folder] = xml_XY(FileLocation)
            os.chdir(FileLocation)
            run_terastitcher("terastitcher_for_XY.xml","XY_stitched", "TiledXY|3Dseries")
            for key in meta_data.keys():
                if key == "x positions "+self.side:
                    input_key = self.parent.DV + " " + key
                else:
                    input_key = key
                edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile, input_key, meta_data[key])
            meta_key = self.parent.pars_channelTab.channel + " " + self.parent.DV + " " + self.side + " stitched"
            new_file_location = get_file_location_of_terastitched_file(FileLocation+"/XY_stitched","XY_stitched.tif")
            edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,meta_key,new_file_location)
            xml_location = FileLocation + "/xml_merging.xml"
            xml_location_key = self.parent.DV + " " + self.side + " XY"
            edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,xml_location_key,xml_location) 
        else:
            os.chdir("..")   
            if os.path.exists("LR_fusion"):
                pass
            else:
                os.mkdir("LR_fusion")
            os.chdir(FileLocation)

            with open(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,"r") as meta:
                im_info = meta.readlines()
                key = self.parent.DV + " " + self.side + " XY" 
                [sn,xml_file] = find_key_from_meta(im_info,key)
                shutil.copy(xml_file,FileLocation)
                current_xml = FileLocation+"/xml_merging.xml"
                xml_edit_directory(current_xml,FileLocation)
                self.edit_xml(current_xml,FileLocation)
            run_terastitcher(current_xml,"XY_stitched", "TiledXY|3Dseries",is_onlymerge=True)
            meta_key = self.parent.pars_channelTab.channel + " " + self.parent.DV + " " + self.side + " stitched"
            new_file_location = get_file_location_of_terastitched_file(FileLocation+"/XY_stitched","XY_stitched.tif")
            edit_meta(self.parent.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,meta_key,new_file_location)
        print("XY stitching is finished")            

    def edit_xml(self,xml_file,current_folder):
        os.chdir(current_folder)
        all_tif = glob.glob("*.tif")
        with open(xml_file,"r") as xml:
            all_lines = xml.readlines()
            xml.close()
        
        for ind,a_line in enumerate(all_lines):
            pattern = re.compile(r"(.*IMG_REGEX=)\"(.*)(_\d\d\d_nm.*)\"")
            name = pattern.findall(a_line)
            if not name:
                continue
            else:
                name_prefix = name[0][1]
                pattern = re.compile(r'%s(.*)'%name_prefix)
                name_postfix = "not a value"
                n = -1
                while name_postfix == "not a value":
                    n = n+1
                    result = pattern.findall(all_tif[n])
                    if not result:
                        continue
                    else:
                        name_postfix = result[0]
                        new_name = name[0][0]+"\""+name_prefix+name_postfix+"\">\n"
                all_lines[ind] = new_name

        with open(xml_file,"w") as xml:
            xml.writelines(all_lines)
            xml.close()

class DVFusionTab(QtWidgets.QWidget):
    def __init__(self, parent = None, channel = None):
        super().__init__(parent)
        self.parent = parent
        self.channel = channel

        self.selectDorsalText = QtWidgets.QLabel(parent = self, text = "Select the dorsal file if not assigned")
        self.selectVentralText = QtWidgets.QLabel(parent = self, text = "Select the ventral file if not assigned")
        self.DorsalFile = QtWidgets.QLineEdit(self)
        self.dorsal_line = channel + " dorsal merged image"
        self.Dorsal_location = get_text_from_meta(self.parent.pars_mainWindow.pars_initWindow.metaFile,self.dorsal_line)
        if self.Dorsal_location != "Not assigned":
            self.DorsalFile.setText(self.Dorsal_location)
        self.ventral_line = channel + " ventral merged image"
        self.Ventral_location = get_text_from_meta(self.parent.pars_mainWindow.pars_initWindow.metaFile,self.ventral_line)
        self.VentralFile = QtWidgets.QLineEdit(self)
        if self.Ventral_location != "Not assigned":
            self.VentralFile.setText(self.Ventral_location)
        self.selectDorsal = QtWidgets.QPushButton(self)
        self.selectDorsal.setText("Browse...")
        self.selectDorsal.clicked.connect(lambda :self.askdirectory(self.DorsalFile))
        self.selectVentral = QtWidgets.QPushButton(self)
        self.selectVentral.setText("Browse...")
        self.selectVentral.clicked.connect(lambda :self.askdirectory(self.VentralFile))

        self.transpose_in_2D = QtWidgets.QPushButton(self)
        self.transpose_in_2D.setText("pre-processing the image")
        self.transpose_in_2D.clicked.connect(self.transpose_then_save)

        self.open_image_folders = QtWidgets.QPushButton(self)
        self.open_image_folders.setText("open the folders containing images")
        self.open_image_folders.clicked.connect(self.open_folders)

        self.label_WidthShift = QtWidgets.QLabel(parent = self,text = "please enter the shift in width:")
        self.shift_in_Width = QtWidgets.QLineEdit(self)

        self.label_HeightShift = QtWidgets.QLabel(parent = self,text = "please enter the shift in height:")
        self.shift_in_Height = QtWidgets.QLineEdit(self)

        self.label_DepthShift = QtWidgets.QLabel(parent = self,text = "please enter the shift in depth:")
        self.shift_in_Depth = QtWidgets.QLineEdit(self)

        self.generate_DV_xml = QtWidgets.QPushButton(self)
        self.generate_DV_xml.setText("match the dimension of DV images and generate xml")
        self.generate_DV_xml.clicked.connect(self.match_DV_fusion)


        meta_file = self.parent.pars_mainWindow.pars_initWindow.metaFile
        key = "dorsal relative to ventral shift in width"
        width = get_text_from_meta(meta_file,key)
        key = "dorsal relative to ventral shift in height"
        height = get_text_from_meta(meta_file,key)
        key = "dorsal relative to ventral shift in depth"
        depth = get_text_from_meta(meta_file,key)
        key = "dorsal relative to ventral shift in depth"
        self.shift_in_Width.setText(width)
        self.shift_in_Height.setText(height)
        self.shift_in_Depth.setText(depth)
        if not self.parent.is_main_channel:    
            self.shift_in_Width.setDisabled(True)
            self.shift_in_Height.setDisabled(True)
            self.shift_in_Depth.setDisabled(True)
            self.generate_DV_xml.setDisabled(True)

        self.fuse_DV = QtWidgets.QPushButton(self)
        self.fuse_DV.setText("DV fusion!!")
        self.fuse_DV.clicked.connect(self.DV_fusion)

        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.selectDorsalText, 0,0,1,3)
        self.layout.addWidget(self.DorsalFile,1,0,1,4)
        self.layout.addWidget(self.selectDorsal,0,3,1,1)
        self.layout.addWidget(self.selectVentralText, 2,0,1,3)
        self.layout.addWidget(self.VentralFile,3,0,1,4)
        self.layout.addWidget(self.selectVentral,2,3,1,1)
        self.layout.addWidget(self.transpose_in_2D, 5,0,1,2)
        self.layout.addWidget(self.open_image_folders, 5,2,1,2)
        self.layout.addWidget(self.label_WidthShift,6,0,1,2)
        self.layout.addWidget(self.shift_in_Width,6,2,1,2)
        self.layout.addWidget(self.label_HeightShift,7,0,1,2)
        self.layout.addWidget(self.shift_in_Height,7,2,1,2)
        self.layout.addWidget(self.label_DepthShift,8,0,1,2)
        self.layout.addWidget(self.shift_in_Depth,8,2,1,2)
        self.layout.addWidget(self.generate_DV_xml,9,0,1,4)
        self.layout.addWidget(self.fuse_DV,10,0,1,4)
        self.setLayout(self.layout)

    def askdirectory(self,SideFileWidget):
        self.file_location = QtWidgets.QFileDialog.getOpenFileName(self)
        SideFileWidget.setText(self.file_location[0])         

    def transpose_then_save(self):
        DV_folder = QtWidgets.QFileDialog.getExistingDirectory(self)
        os.chdir(DV_folder)
        meta_file = self.parent.pars_mainWindow.pars_initWindow.metaFile
        key = self.channel + " dorsal ventral fusion"
        edit_meta(meta_file,key,DV_folder)
        if self.parent.is_main_channel:
            teratranspose(self.VentralFile.text(),self.DorsalFile.text(),DV_folder,meta_file)
        else:
            teratranspose(self.VentralFile.text(),self.DorsalFile.text(),DV_folder,meta_file,False)
            x_shift = self.shift_in_Width.text() 
            z_shift = self.shift_in_Height.text()
            y_shift = self.shift_in_Depth.text()
            xml_DV_fusion.generate_xml(int(x_shift),int(z_shift),int(y_shift),DV_folder,meta_file)  
    
    def open_folders(self):
        key = self.channel + " dorsal ventral fusion"
        self.DV_folder = get_text_from_meta(self.parent.pars_mainWindow.pars_initWindow.metaFile, key)
        ventral_path = os.path.realpath(self.DV_folder+"/ventral_image/")
        dorsal_path = os.path.realpath(self.DV_folder+"/dorsal_image/")
        try:
            os.startfile(ventral_path)
            os.startfile(dorsal_path)
        except:
            pass

    def match_DV_fusion(self):
        key = self.channel + " dorsal ventral fusion"
        meta_file = self.parent.pars_mainWindow.pars_initWindow.metaFile
        DV_folder = get_text_from_meta(meta_file, key)
        os.chdir(DV_folder)
        if self.parent.is_main_channel:
            x_shift = get_text_from_meta(meta_file, "dorsal relative to ventral shift in width")
            z_shift = get_text_from_meta(meta_file, "dorsal relative to ventral shift in height")
            y_shift = get_text_from_meta(meta_file, "dorsal relative to ventral shift in depth")
            
            if x_shift != "not_a_value":
                if x_shift != self.shift_in_Width.text():
                    print("x shift has been assigned with value %s"%x_shift)
                    x_shift = int(self.shift_in_Width.text())
                    edit_meta(meta_file,"dorsal relative to ventral shift in width",x_shift)
                else:
                    x_shift = int(x_shift)                
            else:
                x_shift = self.shift_in_Width.text()

            if z_shift != "not_a_value":
                if z_shift != self.shift_in_Height.text():
                    print("z shift has been assigned with value %s"%z_shift)
                    z_shift = int(self.shift_in_Height.text())
                    edit_meta(meta_file,"dorsal relative to ventral shift in height",z_shift)
                else:
                    z_shift = int(z_shift) 
            else:
                z_shift = int(z_shift)

            if y_shift != "not_a_value":
                if y_shift != self.shift_in_Depth.text():
                    print("y shift has been assigned with value %s"%y_shift)
                    y_shift = int(self.shift_in_Depth.text())
                else:
                    y_shift = int(y_shift) 
            else:
                y_shift = int(y_shift)
            
            edit_meta(meta_file,"dorsal relative to ventral shift in width",x_shift)
            edit_meta(meta_file,"dorsal relative to ventral shift in height",z_shift)
            edit_meta(meta_file,"dorsal relative to ventral shift in depth",y_shift)
            xml_DV_fusion.generate_xml(x_shift,z_shift,y_shift,DV_folder,meta_file)
            edit_meta(meta_file,"dorsal ventral fusion",DV_folder+"/xml_merging.xml")
        else:        
            print("the matching will follow the main channel written in the xml file")

    def DV_fusion(self):
        key = self.channel + " dorsal ventral fusion"
        meta_file = self.parent.pars_mainWindow.pars_initWindow.metaFile
        DV_folder = get_text_from_meta(meta_file, key)
        os.chdir(DV_folder)
        
        if not os.path.isdir("DV_Fusion"):
            os.mkdir("DV_Fusion")
        
        os.chdir("ventral_image")        
        tifnames = glob.glob("*.tif")
        single_file_size = os.stat(tifnames[0]).st_size
        os.chdir(DV_folder)

        if self.parent.is_main_channel:
            run_terastitcher("terastitcher_for_DV.xml","DV_Fusion", "TiledXY|2Dseries",file_size = single_file_size)
        else:
            with open(meta_file,"r") as meta:
                im_info = meta.readlines()
                key = "dorsal ventral fusion" 
                [sn,xml_file] = find_key_from_meta(im_info,key)
                current_xml = shutil.copy(xml_file,DV_folder) 
            xml_edit_directory(current_xml,DV_folder)
            run_terastitcher(current_xml,"DV_Fusion", "TiledXY|2Dseries",file_size = single_file_size, is_onlymerge=True)
        
        channel_ID = self.parent.pars_mainWindow.channel_tabs.currentIndex()
        rename_stitched_2D(DV_folder+"/DV_Fusion",channel_ID)

class DVTab(QtWidgets.QWidget):
    def __init__(self,parent = None, DV = None):
        super().__init__(parent)
        self.pars_channelTab = parent
        self.DV = DV

        self.RawFileLabel = QtWidgets.QLabel(self,text ="raw file directory")
        self.RawFileLocation = QtWidgets.QLineEdit(self)

        self.current_line = self.DV + " raw file"
        self.file_location = get_text_from_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,self.current_line)
        if self.file_location != "Not assigned":
            channel_name = parent.channel
            self.file_location = self.file_location + "/"+channel_name
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
        
        self.RawFileLabel.setGeometry(10,10,290,20)
        self.reloadUnsortedfilebutton.setGeometry(300,10,110,25)
        self.RawFileLocation.setGeometry(10,45,400,18)
        self.LRSplitButton.setGeometry(10,75,400,25)
        self.LeftBox.setGeometry(10,110,280,150)
        self.RightBox.setGeometry(300,110,280,150)
        self.LRMergeBox.setGeometry(10,270,570,250)
        """
        self.tabLayout = QtWidgets.QGridLayout()
        self.tabLayout.addWidget(self.RawFileLabel,0,0,1,1)
        self.tabLayout.addWidget(self.reloadUnsortedfilebutton,0,1,1,1)
        self.tabLayout.addWidget(self.RawFileLocation,1,0,1,4)
        self.tabLayout.addWidget(self.LRSplitButton,2,0,1,4)
        self.tabLayout.addWidget(self.LeftBox,3,0,2,2)
        self.tabLayout.addWidget(self.RightBox,3,2,2,2)
        self.tabLayout.addWidget(self.LRMergeBox,5,0,2,4)
        self.setLayout(self.tabLayout)
        """
    def askdirectory(self):
        self.file_location = QtWidgets.QFileDialog.getExistingDirectory(self)
        self.RawFileLocation.setText(self.file_location)
        edit_meta(self.pars_channelTab.pars_mainWindow.pars_initWindow.metaFile,self.current_line,self.file_location)        

    def splitLR(self):
        sortLR(self.file_location)
        key_left = self.pars_channelTab.channel + " " + self.DV+" left file"
        key_right = self.pars_channelTab.channel + " " + self.DV+" right file"
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

        main_channel = get_text_from_meta(parent.pars_initWindow.metaFile,"main channel")
        if channel == main_channel:
            self.is_main_channel = True
        else:
            self.is_main_channel = False

        sides = ["ventral","dorsal"]
        for side in sides:
            self.DVtabs.addTab(DVTab(parent = self, DV = side),side)
        self.DVtabs.addTab(DVFusionTab(parent = self, channel = channel),"fusion")

        self.DVtabs.resize(600,600)

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent = None):
        super().__init__(parent)
        self.setWindowTitle(parent.metaFile)
        self.resize(600,600)
        self.channel_tabs = QtWidgets.QTabWidget(parent=self)

        self.pars_initWindow = parent
        
        with open(parent.metaFile,"r") as meta:
            im_info = meta.readlines()
            pattern = re.compile(r"[\[]channels[\]] \: [\[]\'(channel_.*)\',\s\'(channel_.*)\',\s\'(channel_.*)\'[\]]\n")
            for line in im_info:
                found_folders = pattern.findall(line)
                if found_folders:
                    found_folders = found_folders[0]
                    if len(found_folders) != 1:
                        channel_folders = []
                    for string in found_folders:
                        channel_folders.append(string)
                    break
            
        main_channel = get_text_from_meta(parent.metaFile,"main channel")

        n = 0
        for a_channel_folder in channel_folders:
            self.channel_tabs.addTab(ChannelTab(parent = self,channel = a_channel_folder), a_channel_folder)
            if a_channel_folder == main_channel:
                self.channel_tabs.setTabText(n,a_channel_folder+" (main)")
            n = n+1                
       
        self.channel_tabs.resize(600,600)

class InitWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mit: mesoSPIM interfaces Terastitcher")
        self.createWork = QtWidgets.QPushButton(text = "create a new stitching project", parent=self)
        self.createWork.setCheckable(True)
        self.createWork.clicked.connect(self.generateMeta)
        self.continueWork = QtWidgets.QPushButton(text = "continue a stitching project ",parent=self)
        self.continueWork.clicked.connect(self.popupMain)
        self.createWork.setGeometry(QtCore.QRect(10,10,200,50))
        self.continueWork.setGeometry(QtCore.QRect(10,70,200,50))
    
    def generateMeta(self):
        # This function creates the window for initial configurations
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
        self.selectChannelText = QtWidgets.QLabel("Please select the main channel for stitch")
        self.channel_folder = self.splitChannels()
        self.selectChannel = QtWidgets.QComboBox(self)
        self.selectChannel.addItems(self.channel_folder)

        self.preLayout.addWidget(self.askSideLabel, 0, 0)
        self.preLayout.addWidget(self.askSideWidget, 1, 0)
        self.preLayout.addWidget(self.askFilenameLabel, 2, 0)
        self.preLayout.addWidget(self.askFilename, 3, 0)
        self.preLayout.addWidget(self.confirmbutton, 6, 0)
        self.preLayout.addWidget(self.selectChannelText,4,0)
        self.preLayout.addWidget(self.selectChannel, 5, 0)
        self.prerequisiteWidget.setLayout(self.preLayout)
        self.prerequisiteWidget.show()
            
    def getParameters(self):

        self.side = self.askSideWidget.currentText()
        self.filename = self.askFilename.text()
        self.metaFile = self.prepare_meta(self.filename,self.channel_folder)
        self.metaFile = self.DataFolder+"/"+self.metaFile
        if self.side == "ventral":
            edit_meta(self.metaFile,"ventral raw file",self.DataFolder)
            OppositeSide = "dorsal"
        elif self.side == "dorsal":
            edit_meta(self.metaFile,"dorsal raw file",self.DataFolder)
            OppositeSide = "ventral"
        
        edit_meta(self.metaFile,"channels",self.channel_folder)
        self.main_channel = self.selectChannel.currentText()       
        edit_meta(self.metaFile,"main channel",self.main_channel)
        
        self.OppositeSideFolder = QtWidgets.QFileDialog.getExistingDirectory(self,"select the directory where %s data were stored"%OppositeSide)
        sortChannel(self.OppositeSideFolder)
        edit_meta(self.metaFile,"%s raw file"%OppositeSide,self.DataFolder)
        
        self.prerequisiteWidget.hide()
        self.mainWindow = MainWindow(self)
        self.mainWindow.show()
    
    def splitChannels(self):    
        channel_folder = sortChannel(os.getcwd())
        return channel_folder
        
    def popupMain(self):
        # This function creates the window for stitching
        metaFileName = QtWidgets.QFileDialog.getOpenFileName(self,"select a meta file (.txt) to open an existed project")
        cwd = os.getcwd()
        self.metaFile = os.path.join(cwd,metaFileName[0])
        self.mainWindow = MainWindow(self)    
        self.mainWindow.show()

    def prepare_meta(self,filename,channel_folder):
        meta_name = filename + "_meta.txt"
        with open(meta_name,"w") as meta:
            meta.write("[channels] : \n")
            meta.write("[main channel] : \n")
            meta.write("=== system parameters ===\n")
            meta.write("[pixel size of x (um)] : \n")
            meta.write("[pixel size of y (um)] : \n")
            meta.write("[z step size (um)] : \n")
            meta.write("[pixel counts in x] : \n")
            meta.write("[pixel counts in y] : \n")
            meta.write("[ventral x positions right] : \n")
            meta.write("[ventral x positions left] : \n")
            meta.write("[ventral middle of x] : \n")
            meta.write("[dorsal x positions right] : \n")
            meta.write("[dorsal x positions left] : \n")
            meta.write("[dorsal middle of x] : \n")
            meta.write("[ventral left cutting pixel] : \n")
            meta.write("[ventral right cutting pixel] : \n")
            meta.write("[ventral left overlap] : \n")
            meta.write("[ventral right overlap] : \n")
            meta.write("[ventral LR pixel difference in x] : \n")
            meta.write("[ventral LR pixel difference in y] : \n")
            meta.write("[ventral edge index] : \n")
            meta.write("[dorsal left cutting pixel] : \n")
            meta.write("[dorsal right cutting pixel] : \n")
            meta.write("[dorsal left overlap] : \n")
            meta.write("[dorsal right overlap] : \n")
            meta.write("[dorsal LR pixel difference in x] : \n")
            meta.write("[dorsal LR pixel difference in y] : \n")
            meta.write("[dorsal edge index] : \n")
            meta.write("[dorsal relative to ventral shift in width] : \n")
            meta.write("[dorsal relative to ventral shift in height] : \n")
            meta.write("[dorsal relative to ventral shift in depth] : \n")
            meta.write("=== progress ===\n")
            meta.write("=== file location ===\n")
            meta.write("[ventral raw file] : Not assigned\n")
            meta.write("[dorsal raw file] : Not assigned\n")
            for a_folder in channel_folder:               
                meta.write("[%s ventral left file] : Not assigned\n"%a_folder)
                meta.write("[%s ventral right file] : Not assigned\n"%a_folder)
                meta.write("[%s ventral left stitched] : Not assigned\n"%a_folder)
                meta.write("[%s ventral right stitched] : Not assigned\n"%a_folder)
                meta.write("[%s ventral merged image] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal left file] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal right file] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal left stitched] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal right stitched] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal merged image] : Not assigned\n"%a_folder)
                meta.write("[%s dorsal ventral fusion] : Not assigned\n"%a_folder)
            meta.write("=== xml location === \n")
            meta.write("[ventral left XY] : Not assigned\n")
            meta.write("[ventral right XY] : Not assigned\n")
            meta.write("[ventral LR merged] : Not assigned\n")
            meta.write("[dorsal left XY] : Not assigned\n")
            meta.write("[dorsal right XY] : Not assigned\n")
            meta.write("[dorsal LR merged] : Not assigned\n")
            meta.write("[dorsal ventral fusion] : Not assigned\n")

        return meta_name
    
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = InitWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
    