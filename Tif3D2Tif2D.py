import numpy as np 
import tifffile as tff 
import os

def c3DTo2D(images, dest_folder):
    currentfolder = os.getcwd()
    os.mkdir(dest_folder)
    os.chdir(dest_folder)    
    layerno = images.shape[0]
    for n in range(0,layerno):
        name = "image_" + str(n) + ".tif"
        tff.imwrite(name,images[n,:,:])
    os.chdir(currentfolder)

