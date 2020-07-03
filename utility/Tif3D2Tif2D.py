'''
This code save a 3d tif files into a series of 2D tif files in a designated folder
'''

import numpy as np 
import tifffile as tff 
import os

def c3DTo2D(images, dest_folder):
    '''
    images: should be a 3D tif file
    dest_folder: the folder used to save the output 2D tifs. This folder should not exist before running the code.
    the code will generate the folder itself
    '''
    currentfolder = os.getcwd()
    os.mkdir(dest_folder)
    os.chdir(dest_folder)    
    layerno = images.shape[0]
    for n in range(0,layerno):
        name = "image_" + str(n) + ".tif"
        tff.imwrite(name,images[:,:,n])
    os.chdir(currentfolder)

