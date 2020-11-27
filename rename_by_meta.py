from mit import find_key_from_meta
import tkinter as tk
from tkinter import filedialog
import glob,os,re

root = tk.Tk()
root.withdraw()

folder = filedialog.askdirectory()
os.chdir(folder)
all_meta_file = glob.glob("*_meta.txt")
all_raw_file = glob.glob("*.raw")

for a_meta in all_meta_file:
    meta = open(a_meta,'r')
    all_lines = meta.readlines()
    meta.close()

    [n,x_pos] = find_key_from_meta(all_lines,"x_pos")
    x_pos = str(round(float(x_pos)))
    [n,y_pos] = find_key_from_meta(all_lines,"y_pos")
    y_pos = str(round(float(y_pos)))
    [n,laser] = find_key_from_meta(all_lines,"Laser")
    laser = laser[0:len(laser)-3]
    [n,filters] = find_key_from_meta(all_lines,"Filter")
    [n,mag] = find_key_from_meta(all_lines,"Zoom")
    [n,side] = find_key_from_meta(all_lines,"Shutter")

    name = "X"+x_pos+"_Y"+y_pos+"_"+laser+"_nm_"+filters+"_"+mag+"_"+side+".raw"

    name_prefix = a_meta[0:len(a_meta)-9]
    n = 0
    while name_prefix != all_raw_file[n] and n < len(all_raw_file) :
        n = n+1
    if n >= len(all_raw_file):
        print("the image file %s can't be found"%name_prefix)
    else:
        image_name = all_raw_file[n]
        os.rename(a_meta,name+"_meta.txt")
        os.rename(image_name,name)      


