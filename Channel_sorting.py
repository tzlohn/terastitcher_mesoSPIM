"""
This function finds out the wavelength used to illuminatoins for an image by its file name. 
When an image is identified, it will be moved to the corresponding folder.
In the future, 2 channels which excites by on wavelength might be added
"""
import numpy as np
import tifffile as TFF
import tkinter as tk
from tkinter import filedialog, simpledialog
from shutil import copyfile
import os,re,glob,shutil,time

def sortChannel(working_folder):
    print("warning: if you have different channels used the same wavelength to excite, then this function can't work properly. Please contact Tzu-Lun in this case")

    all_files = glob.glob("*")

    # rename all files, remove the serial number in the end
    for aFile in all_files:
        pattern = re.compile(r'(.raw_meta.txt|.raw)')
        exts = pattern.findall(aFile)    
        if not exts:
        # if there are files which in not ended by .raw or .raw_meta.txt, such as tif, then the loop
        # will be continued.
            continue
        ext = exts[-1]
        pattern = re.compile(r'(.*)(_0\d+)%s'%ext)
        new_name = pattern.findall(aFile)
        if new_name == []:
            pattern = re.compile(r'(.*)%s'%ext)
            new_name = pattern.findall(aFile)      
            new_name = new_name[0] + ext
        else:
            new_name = new_name[0][0] + ext    

        if not os.path.exists(new_name):
            os.rename(aFile,new_name)

    all_raw_files = glob.glob("*")

    channels= []
    channels_folder = []

    for a_raw_file in all_raw_files:
        pattern = re.compile(r'.*(.raw|.tif)')
        filename_piece = pattern.findall(a_raw_file)
        if not filename_piece:
            continue  
        print(a_raw_file)
        its_meta_file = a_raw_file + "_meta.txt"
        if not os.path.exists(its_meta_file):
            continue

        pattern = re.compile(r'(.*)_(\d+)_nm_(.*)(.raw|.tif)')
        filename_piece = pattern.findall(a_raw_file)

        if not filename_piece[0][1] in channels:
            print(filename_piece[0][1])
            channels.append(filename_piece[0][1])
            channels_folder.append("channel_"+filename_piece[0][1])
            os.mkdir("channel_"+filename_piece[0][1])

        n = 0
        found_wavelength = ""
        while len(found_wavelength) is 0: 
            pattern = re.compile(r'(.*)_(%s)_nm_(.*)(.raw|.tif)'%(channels[n]))
            filename_piece = pattern.findall(a_raw_file)        
            if not filename_piece:
                n = n+1
                continue
            else:
                found_wavelength = filename_piece[0][1] 

        shutil.move(a_raw_file, working_folder+"/"+channels_folder[n])    
        shutil.move(its_meta_file, working_folder+"/"+channels_folder[n])

    return channels_folder

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    working_folder = filedialog.askdirectory()
    os.chdir(working_folder)
    sortChannel(working_folder)