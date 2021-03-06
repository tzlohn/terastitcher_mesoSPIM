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

def identify_channel(a_raw,channels):

    its_meta_name = a_raw + "_meta.txt"
    with open(its_meta_name,"r") as its_meta:
        all_lines = its_meta.readlines()
    for a_line in all_lines:
            pattern_1 = re.compile(r"[\[]Laser[\]] (.*) nm\n")
            pattern_2 = re.compile(r"[\[]Filter[\]] (.*)\n")
            found_1 = pattern_1.findall(a_line)
            found_2 = pattern_2.findall(a_line)
            if found_1:
                laser = found_1[0]     
            if found_2:
                filters = found_2[0]
                break
    channel = "channel_" + laser + "_" + filters
    if not channel in channels:
        channels.append(channel)
    
    return [channel,channels]

def remove_serial_nr(aFile):
    
    pattern = re.compile(r'(.raw_meta.txt|.raw)')
    exts = pattern.findall(aFile)    
    if not exts:
    # if there are files which in not ended by .raw or .raw_meta.txt, such as tif, then the loop
    # will be continued.
        return
    ext = exts[-1]
    pattern = re.compile(r'(.*)(_0\d+)%s'%ext)
    new_name = pattern.findall(aFile)
    if new_name == []:
        pattern = re.compile(r'(.*)%s'%ext)
        new_name = pattern.findall(aFile)      
        new_name = new_name[0] + ext
    else:
        new_name = new_name[0][0] + ext    

    return new_name
    """
    if not os.path.exists(new_name):
        os.rename(aFile,new_name)
    """

def sortChannel(working_folder):
    #print("warning: if you have different channels used the same wavelength to excite, then this function can't work properly. Please contact Tzu-Lun in this case")

    all_raw = glob.glob("*.raw")
    if len(all_raw) == 0:
        all_raw = glob.glob("*.tif")
            
    channel_folder = []

    for a_raw in all_raw:
        [current_channel,channel_folder] = identify_channel(a_raw,channel_folder)    
        if not os.path.exists(current_channel):
           os.mkdir(current_channel)
        
        its_meta = a_raw + "_meta.txt"
        """
        new_raw_name = remove_serial_nr(a_raw)
        its_meta = a_raw + "_meta.txt"
        new_meta_name = remove_serial_nr(its_meta)
        """
        os.rename(a_raw, working_folder+"/"+current_channel+"/"+a_raw)
        os.rename(its_meta, working_folder+"/"+current_channel+"/"+its_meta)
         

    return channel_folder

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    working_folder = filedialog.askdirectory()
    os.chdir(working_folder)
    sortChannel(working_folder)