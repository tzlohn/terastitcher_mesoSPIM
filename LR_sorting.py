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

def progress_bar():
    all_raw_file = glob.glob("*.raw")
    total_length = len(all_raw_file)
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
    p = int(n*100/total_length)
    if p > 100:
        p = 100
    sys.stdout.write("\r{0}| ({1}/{2})".format(">"*p+"="*(100-p),n,total_length))
    sys.stdout.flush()

def save2tif(raw_list,working_folder):

    # magic number zone #
    background_intensity = 120

    a_raw_file = raw_list.pop(0)
    if raw_list:
        next_process = Process(target = save2tif, args=(raw_list,working_folder))

    progress_bar()   
    
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

    new_name = a_raw_file[0:len(a_raw_file)-4]
    new_tif_name = new_name + ".tif"

    if not os.path.exists(working_folder+"/"+illumination_side+"/"+new_tif_name):
        # save to tiff
        if is_scanned == "False":
            im = np.ones(shape = dim_size, dtype = "uint16")
            im = im*background_intensity
        else:
            im = np.memmap(a_raw_file, dtype = 'uint16', mode = 'r', shape = dim_size)
        

        #TFF.imwrite(new_tif_name, data = im, bigtiff = True)
        memmap_img = TFF.memmap(new_tif_name, shape = dim_size, dtype = 'uint16')
        if raw_list:
            next_process.start()
        np.copyto(memmap_img,im)
        memmap_img.flush()
        del memmap_img

        # save the meta for tiff
        new_meta_name = new_name+".tif_meta.txt"
        copyfile(its_meta_file,new_meta_name)

        if illumination_side == "Left":
            shutil.move(new_tif_name, working_folder+"/Left")
            #os.rename(new_tif_name, working_folder+"/Left/"+new_tif_name)    
            shutil.move(new_meta_name, working_folder+"/Left")
        elif illumination_side == "Right":    
            shutil.move(new_tif_name, working_folder+"/Right")
            #os.rename(new_tif_name, working_folder+"/Right/"+new_tif_name)
            shutil.move(new_meta_name, working_folder+"/Right")
        
        progress_bar()
        if raw_list:
            next_process.join()

def sortLR(working_folder):
    print("Left-Right sorting starts...")
    os.chdir(working_folder)
    
    if not os.path.exists("Left"):
        os.mkdir("Left")
    if not os.path.exists("Right"):
        os.mkdir("Right")
    
    all_raw_files = glob.glob("*.raw")
    a_file_size = os.stat(all_raw_files[0]).st_size
    core_no = int(virtual_memory().free/a_file_size)    

    round_no = (len(all_raw_files)//core_no)+1
    for a_round in range(round_no):
        if core_no*(a_round+1) < len(all_raw_files):
            working_raw_list = all_raw_files[core_no*a_round:core_no*(a_round+1)]
        else:
            working_raw_list = all_raw_files[core_no*a_round:len(all_raw_files)]
        save2tif(working_raw_list,working_folder)
    progress_bar()

    """
    pool_input = [(a_raw_file,working_folder) for a_raw_file in all_raw_files]
    with get_context("spawn").Pool(processes=core_no) as pool:
        try:
            result = pool.starmap(save2tif,pool_input)
            pool.close()
        except:
            pool.close()
            pool.join()
            all_tif = glob.glob("*.tif")
            for a_tif in all_tif:
                os.remove(a_tif)
            all_meta_tif = glob.glob("*.tif_meta.txt")
            for a_meta_tif in all_meta_tif:
                os.remove(a_meta_tif)
        pool.join()

    progress_bar()
    """
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    working_dir = filedialog.askdirectory()
    sortLR(working_dir)
