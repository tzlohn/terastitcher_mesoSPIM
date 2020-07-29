import re, sys, os, glob, time
import tkinter as tk
from tkinter import filedialog, simpledialog
import tifffile as TFF
import numpy as np

# magic number zone #
'''
reference refering is like transpose. ref1 indicates the V in terastitcher
ref2 indicates H, ref3 indicates D. 1,2,3 is the 3 dimension indicators in your images.
The follwing assigment tells the code to map the coordinates of your system to terastitcher
the minus sign indicates that the tile will be aligned/stitched in the reverse order of the index
''' 
ref1 = 1
ref2 = 2
ref3 = 3

ori_V = 0 # unit: mm
ori_H = 0
ori_D = 0

bit = 16
######################

def get_value(expression,text):
    output = expression.findall(text)
    value = ""
    for num in output[0]:
        value = value + num 
    value = float(value)
    return value

root = tk.Tk()
root.withdraw()

folderpath = filedialog.askdirectory(title = "select the folder containing folders for images from both sides")
os.chdir(folderpath)

dim_V = simpledialog.askfloat(prompt = "the pixel size in y:", title = "")
dim_D = simpledialog.askfloat(prompt = "the pixel size in x:", title = "")
dim_H = simpledialog.askfloat(prompt = "the step size in z:", title = "")
z_overlap = simpledialog.askinteger(prompt = "no. of overlapped layers between dorsal and ventral sides:", title = "")

xml_name = folderpath + "//" + "terastitcher" + ".xml"

offset_V = 0
for folder in ["ventral_image","dorsal_image"]:
    os.chdir(folder)
    tif_name = glob.glob("*.tif")
    if folder  == "ventral_image":
        ventral_image = TFF.imread(tif_name[0])
        slice_no_ventral = len(tif_name)
    elif folder == "dorsal_image":
        dorsal_image = TFF.imread(tif_name[0])
        slice_no_dorsal = len(tif_name)
    os.chdir(folderpath)
offset_H = (ventral_image.shape[1]-z_overlap)*dim_H

total_row = 1
total_column = 2
slice_no = [slice_no_ventral,slice_no_dorsal]
print(slice_no)
shift_no = [1, ventral_image.shape[1]-z_overlap]
print(shift_no)

foldername = ['ventral_image','dorsal_image']


with open(xml_name,'w') as xml_file:
    xml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
    xml_file.write("<!DOCTYPE TeraStitcher SYSTEM \"TeraStitcher.DTD\">\n")
    xml_file.write("<TeraStitcher volume_format=\"TiledXY|2Dseries\" input_plugin=\"tiff2D\">\n")
    xml_file.write("    <stacks_dir value=\"%s\" />\n"%folderpath)
    xml_file.write("    <ref_sys ref1=\"%d\" ref2=\"%d\" ref3=\"%d\" />\n"%(ref1,ref2,ref3))
    xml_file.write("    <voxel_dims V=\"%.2f\" H=\"%.2f\" D=\"%.2f\" />\n"%(dim_V,dim_H,dim_D))
    xml_file.write("    <origin V=\"%.3f\" H=\"%.3f\" D=\"%.3f\" />\n"%(ori_V,ori_H,ori_D))
    xml_file.write("    <mechanical_displacements V=\"%.2f\" H=\"%.2f\" />\n"%(offset_V,offset_H))
    xml_file.write("    <dimensions stack_rows=\"%d\" stack_columns=\"%d\" stack_slices=\"%d\" />\n"%(total_row,total_column,max(slice_no)))
    xml_file.write("    <STACKS>\n")
    
    for n in range(len(foldername)):
        xml_file.write("        <Stack N_CHANS=\"1\"")
        xml_file.write(" N_BYTESxCHAN=\"%d\""%(bit/8))
            
        xml_file.write(" ROW=\"%d\""%(0))
        xml_file.write(" COL=\"%d\""%(n))   
        xml_file.write(" ABS_H=\"%.1f\""%(shift_no[n]))
        xml_file.write(" ABS_V=\"%.1f\""%(1))
            
        xml_file.write(" ABS_D=\"0\"")
        xml_file.write(" STITCHABLE=\"yes\"")
        xml_file.write(" DIR_NAME=\"%s\""%(foldername[n]))
        xml_file.write(" Z_RANGES=\"[0,%d)\""%(slice_no[n]))
        xml_file.write(" IMG_REGEX=\"%s\">\n"%("image_\d+.tif"))
            
        xml_file.write("            <NORTH_displacements/>\n")
        xml_file.write("            <EAST_displacements/>\n")
        xml_file.write("            <SOUTH_displacements/>\n")
        xml_file.write("            <WEST_displacements/>\n")
        xml_file.write("        </Stack>\n")
    xml_file.write("    </STACKS>\n")
    xml_file.write("</TeraStitcher>\n")

