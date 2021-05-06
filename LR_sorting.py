"""
This function finds out whether an image is from left or right illuminatoins by its file name. 
When an image is identified, it will be moved to the corresponding folder.
"""
import numpy as np
import tifffile as TFF
import tkinter as tk
from tkinter import filedialog
from shutil import copyfile
import multiprocessing as mp
from multiprocessing import Process, Queue, Pipe
from multiprocessing import get_context
import os,re,glob,shutil,sys,time
from psutil import virtual_memory
from PyQt5 import QtWidgets

def progress_bar(datatype):
    if datatype == "mesoSPIM raw":
        all_raw_file = glob.glob("*.%s"%"raw")
        total_length = len(all_raw_file)
    elif datatype == "tif":
        all_raw_file = glob.glob("*.%s"%"tif")
        remaining_length = len(all_raw_file)
   
    left_list = os.listdir("Left")
    right_list = os.listdir("Right")
    if not left_list:
        left_len = 0
    else:
        left_len = len(left_list)
    if not right_list:
        right_len = 0
    else:
        right_len = len(right_list)
    n = int(left_len/2)+int(right_len/2)
    if datatype == "tif":
        total_length = remaining_length + n
    p = int(n*100/total_length)
    if p > 100:
        p = 100
    sys.stdout.write("\r{0}| ({1}/{2})".format(">"*p+"="*(100-p),n,total_length))
    sys.stdout.flush()

def save2tif(raw_list,working_folder,datatype):

    # magic number zone #
    background_intensity = 120

    a_raw_file = raw_list.pop(0)
    if raw_list:
        next_process = Process(target = save2tif, args=(raw_list,working_folder,datatype))
     
    progress_bar(datatype)
      
    its_meta_file = a_raw_file + "_meta.txt"
    # get pixel number, pixel size and dimensions for memmap to load the image
    dim_names = ['z_planes','y_pixels','x_pixels']
    dim_size = [0, 0, 0]        
    n = 0
    with open(its_meta_file) as metaFile:
        image_info = metaFile.read()
        for dim_name in dim_names:
            pattern = re.compile(r"[\[]%s[\]] (\d+)"%dim_name)
            value = pattern.findall(image_info)
            dim_size[n] = int(value[0])
            n=n+1
    
        pattern = re.compile(r"[\[]is\sscanned[\]] (\w+)")
        is_scanned = pattern.findall(image_info)
        is_scanned = is_scanned[0]

        # identify the shutter/illumination side
        pattern = re.compile(r"[\[]Shutter[\]] (\w+)\n")
        illumination_side = pattern.findall(image_info)
        illumination_side = illumination_side[0]    
    
    dim_size = tuple(dim_size)

    if datatype == "mesoSPIM raw":
        new_name = a_raw_file[0:len(a_raw_file)-4]
        new_tif_name = new_name + ".tif"
    else:
        new_tif_name = a_raw_file

    if not os.path.exists(working_folder+"/"+illumination_side+"/"+new_tif_name):
        # save to tiff
        if is_scanned == "False":
            im = np.ones(shape = dim_size, dtype = "uint16")
            im = im*background_intensity
        else:
            if datatype == "mesoSPIM raw":
                im = np.memmap(a_raw_file, dtype = 'uint16', mode = 'r', shape = dim_size)
            else:
                pass
        
        if datatype == "mesoSPIM raw":
            TFF.imwrite(new_tif_name, data = im, bigtiff = True)
            # save the meta for tiff
            new_meta_name = new_name+".tif_meta.txt"
            copyfile(its_meta_file,new_meta_name)
        else:
            if is_scanned == False:
                TFF.imwrite(new_tif_name,data = im, bigtiff = True)
            new_meta_name = its_meta_file
        
        if raw_list:
            next_process.start()

        if illumination_side == "Left":
            #shutil.move(new_tif_name, working_folder+"/Left")
            os.rename(new_tif_name, working_folder+"/Left/"+new_tif_name)    
            shutil.move(new_meta_name, working_folder+"/Left")
        elif illumination_side == "Right":    
            #shutil.move(new_tif_name, working_folder+"/Right")
            os.rename(new_tif_name, working_folder+"/Right/"+new_tif_name)
            shutil.move(new_meta_name, working_folder+"/Right")
        
        progress_bar(datatype)

    else:
        if raw_list:
            next_process.start()
    
    if raw_list:
        next_process.join()

def sortLR(working_folder, datatype = "mesoSPIM raw"):
    print("Left-Right sorting starts...")
    os.chdir(working_folder)
    
    if not os.path.exists("Left"):
        os.mkdir("Left")
    if not os.path.exists("Right"):
        os.mkdir("Right")
    
    if datatype == "mesoSPIM raw":
        all_raw_files = glob.glob("*.raw")
    elif datatype == "tif":
        all_raw_files = glob.glob("*.tif")
    try:    
        a_file_size = os.stat(all_raw_files[0]).st_size
    except:
        msgWindow = QtWidgets.QMessageBox()
        msgWindow.setIcon(QtWidgets.QMessageBox.Warning)
        msgWindow.setWindowTitle("Can't find images with %s format"%datatype)
        msgWindow.setText("Can't find images with %s format,\n please check whether the image format is correct"%datatype)
        return 0
    core_no = int(virtual_memory().free/a_file_size)    

    round_no = (len(all_raw_files)//core_no)+1
    for a_round in range(round_no):
        if core_no*(a_round+1) < len(all_raw_files):
            working_raw_list = all_raw_files[core_no*a_round:core_no*(a_round+1)]
        else:
            working_raw_list = all_raw_files[core_no*a_round:len(all_raw_files)]
        save2tif(working_raw_list,working_folder,datatype)
    print("Left-right file sorting is finished.")

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    working_dir = filedialog.askdirectory()
    sortLR(working_dir)
