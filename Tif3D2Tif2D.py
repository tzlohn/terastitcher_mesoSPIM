import numpy as np 
import tifffile as tff 
import os,shutil

def c3DTo2D(filename, dest_folder):
    currentfolder = os.getcwd()
    os.mkdir(dest_folder)
    shutil.move(filename,currentfolder+"/"+dest_folder+"/"+ filename)
    os.chdir(dest_folder)
    tif  = tff.TiffFile(filename)
    layerno = len(tif.pages)
    for n in range(0,layerno):
        name = "image_" + str(n) + ".tif"
        img = tff.imread(filename,key = n)
        tff.imwrite(name,img)
    os.chdir(currentfolder)

