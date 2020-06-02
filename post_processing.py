'''
The postprocessing code is part of the mesoSPIM interface to Terastitcher.
After the terastitcher process the dorsal-ventral fusion, post_processing.py 
will transpose the yz stacks back to xy stacks, remove filling zero layers,
and save it into a series of 2D tiffs
To do: offer an option to save to a 3D tiff
'''
import tifffile as TFF 
import tkinter as tk 
import numpy as np
import os
from tkinter import filedialog
import Tif3D2Tif2D as t32D

root = tk.Tk()
root.withdraw()

currentImage = filedialog.askopenfilename()
currentfolder = filedialog.askdirectory()
os.chdir(currentfolder)

print("step 0/3: the image is under loading")
img = TFF.imread(currentImage)
img = np.asarray(img)
print("step 1/3: the image is transposing")
img = img.transpose([2,1,0])

# remove the zero layers for terastitcher
print("step 2/3: finding empty filling layers and reomve them")
layer_mean = np.mean(img[0,:,:])
if layer_mean is 0:
    dz = +1
    z0 = 0
    condition = 0
else:
    dz = -1
    z0 = img.shape[0]
    condition = 1

layer_mean = 0
while layer_mean is 0:
    z0 = z0+dz
    layer_mean = np.mean(img[z0,:,:])

if condition == 0:
    img = img[z0:-1,:,:]
elif condition == 1:
    img = img[0:z0,:,:]

#save the transpose file with lzw compression
print("step 3/3: saving the processed image to a lzw tif")
'''
with TFF.TiffWriter("xySection.tif", bigtiff = True, imagej = True, append = True) as Tif3D:
    for n in range(img.shape[0]):
        Tif3D.save(img[n,:,:], compress = 5)
'''
t32D.c3DTo2D(img,"new_stitcheing")


    