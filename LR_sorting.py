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
from multiprocessing import get_context
import os,re,glob,shutil,time
from psutil import virtual_memory

def save2tif(a_raw_file,working_folder):
    # magic number zone #
    background_intensity = 120

    pattern = re.compile(r'(.*)(_left|_right|_Left|_Right).*.raw')
    filename_piece = pattern.findall(a_raw_file)
    print(a_raw_file)
    if not filename_piece:
        return False
    else:    
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
        
        dim_size = tuple(dim_size)

        # save to tiff
        if is_scanned == "False":
            im = np.ones(shape = dim_size, dtype = "uint16")
            im = im*background_intensity
        else:
            im = np.memmap(a_raw_file, dtype = 'uint16', mode = 'r', shape = dim_size)
        n = 0
        new_name = ""
        while n < len(filename_piece[0]):
            new_name = new_name + filename_piece[0][n]
            n = n+1
        new_tif_name = new_name + ".tif"
        
        TFF.imwrite(new_tif_name, data = im, bigtiff = True)

        # save the meta for tiff
        new_meta_name = new_name+".tif_meta.txt"
        copyfile(its_meta_file,new_meta_name)

        if filename_piece[0][1] == "_Left":
            shutil.move(new_tif_name, working_folder+"/Left")    
            shutil.move(new_meta_name, working_folder+"/Left")
        elif filename_piece[0][1] == "_Right":    
            shutil.move(new_tif_name, working_folder+"/Right")
            shutil.move(new_meta_name, working_folder+"/Right")


def sortLR(working_folder):

    os.chdir(working_folder)
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
# potential bug: if file exists, then this bug will create crashed when finding the name.

    if not os.path.exists("Left"):
        os.mkdir("Left")
    if not os.path.exists("Right"):
        os.mkdir("Right")

    all_raw_files = glob.glob("*.raw")
    a_file_size = os.stat(all_raw_files[0]).st_size
    core_no = int(virtual_memory().free/a_file_size)
    pool_input = [(a_raw_file,working_folder) for a_raw_file in all_raw_files]
    with get_context("spawn").Pool(processes=core_no) as pool:
        result = pool.starmap(save2tif,pool_input)
        pool.close()

"""
    t_start = time.time()
    for a_raw_file in all_raw_files:
        pattern = re.compile(r'(.*)(_left|_right|_Left|_Right).*.raw')
        filename_piece = pattern.findall(a_raw_file)
        print(a_raw_file)
        if not filename_piece:
            continue
        else:    
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
            
            dim_size = tuple(dim_size)

            # save to tiff
            if is_scanned == "False":
                im = np.ones(shape = dim_size, dtype = "uint16")
                im = im*background_intensity
            else:
                im = np.memmap(a_raw_file, dtype = 'uint16', mode = 'r', shape = dim_size)
            n = 0
            new_name = ""
            while n < len(filename_piece[0]):
                new_name = new_name + filename_piece[0][n]
                n = n+1
            new_tif_name = new_name + ".tif"
            
            TFF.imwrite(new_tif_name, data = im, bigtiff = True)

            # save the meta for tiff
            new_meta_name = new_name+".tif_meta.txt"
            copyfile(its_meta_file,new_meta_name)
        
            if filename_piece[0][1] == "_Left":
                shutil.move(new_tif_name, working_folder+"/Left")    
                shutil.move(new_meta_name, working_folder+"/Left")
            elif filename_piece[0][1] == "_Right":    
                shutil.move(new_tif_name, working_folder+"/Right")
                shutil.move(new_meta_name, working_folder+"/Right")
            
            t_end = time.time()

            estimate_time = ((t_end-t_start)/(all_raw_files.index(a_raw_file)+1))*len(all_raw_files)
            print("time taken: %.2f, time remaining: %.2f seconds (%.2f/100)"%(t_end-t_start, estimate_time-(t_end-t_start), ((t_end-t_start)/estimate_time)*100))
            """