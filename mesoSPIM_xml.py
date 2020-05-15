import re, sys, os, glob
import tkinter as tk
from tkinter import filedialog

# magic number zone #
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

folderpath = filedialog.askdirectory()
os.chdir(folderpath)

xml_name = folderpath + "\\" + "terastitcher" + ".xml"

file_list = glob.glob('*tif_meta.txt')
pattern_y = re.compile(r"X-?\d+_Y(-?\d+)")
pattern_x = re.compile(r"X(-?\d+)_Y-?\d+")

# Counting number of tiles, getting the offset between them
y_pos_all = []
x_pos_all = []
for a_file_name in file_list:
    y_pos = float(pattern_y.findall(a_file_name)[0])
    if y_pos not in y_pos_all:
        y_pos_all.append(y_pos)
    x_pos = float(pattern_x.findall(a_file_name)[0])
    if x_pos not in x_pos_all:
        x_pos_all.append(x_pos)
y_pos_all.sort(reverse= True)
x_pos_all.sort(reverse= True)

total_row = len(y_pos_all)
if total_row > 1:
    offset_V = y_pos_all[0]-y_pos_all[1]
else:
    offset_V = 0

total_column = len(x_pos_all)
if total_column > 1:
    offset_H = x_pos_all[0]-x_pos_all[1]
else:
    offset_H = 0


with open(file_list[0],'r') as a_metafile:
    im_info = a_metafile.read()
    pattern = re.compile(r"[\[]Pixelsize in um[\]] (\d+)(\.)?(\d+)?")
    dim_V = get_value(pattern,im_info)
    dim_H = dim_V
    
    pattern = re.compile(r"[\[]z_stepsize[\]] (\d+)(\.)?(\d+)?")
    dim_D = get_value(pattern,im_info)

    pattern = re.compile(r"[\[]z_planes[\]] (\d+)")
    output = pattern.findall(im_info)
    #slice_no = int(output[0])
    slice_no = 116
    
with open(xml_name,'w') as xml_file:
    xml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
    xml_file.write("<!DOCTYPE TeraStitcher SYSTEM \"TeraStitcher.DTD\">\n")
    xml_file.write("<TeraStitcher volume_format=\"TiledXY|3Dseries\" input_plugin=\"tiff3D\">\n")
    xml_file.write("    <stacks_dir value=\"%s\" />\n"%folderpath)
    xml_file.write("    <ref_sys ref1=\"%d\" ref2=\"%d\" ref3=\"%d\" />\n"%(ref1,ref2,ref3))
    xml_file.write("    <voxel_dims V=\"%.2f\" H=\"%.2f\" D=\"%.2f\" />\n"%(dim_V,dim_H,dim_D))
    xml_file.write("    <origin V=\"%.3f\" H=\"%.3f\" D=\"%.3f\" />\n"%(ori_V,ori_H,ori_D))
    xml_file.write("    <mechanical_displacements V=\"%.2f\" H=\"%.2f\" />\n"%(offset_V,offset_H))
    xml_file.write("    <dimensions stack_rows=\"%d\" stack_columns=\"%d\" stack_slices=\"%d\" />\n"%(total_row,total_column,slice_no))
    xml_file.write("    <STACKS>\n")
    for file_name in file_list:
        with open(file_name,'r') as this_im:
            im_info = this_im.read()
            xml_file.write("        <Stack N_BLOCKS=\"1\"")
            xml_file.write(" BLOCK_SIZES=\"%.2f\""%(slice_no*dim_D))
            xml_file.write(" BLOCKS_ABS_D=\"0\"")
            xml_file.write(" N_CHANS=\"1\"")
            xml_file.write(" N_BYTESxCHAN=\"%d\""%(bit/8))
            
            pattern = re.compile(r"[\[]y_pos[\]] (-)?(\d+)(\.)?(\d+)?")
            y_position = int(get_value(pattern,im_info))
            y_index = y_pos_all.index(y_position)    
            
            pattern = re.compile(r"[\[]x_pos[\]] (-)?(\d+)(\.)?(\d+)?")
            x_position = int(get_value(pattern,im_info))
            x_index = x_pos_all.index(x_position)

            xml_file.write(" ROW=\"%d\""%(y_index))
            xml_file.write(" COL=\"%d\""%(x_index))   
            xml_file.write(" ABS_H=\"%.1f\""%(x_position))
            xml_file.write(" ABS_V=\"%.1f\""%(y_position))
            
            xml_file.write(" ABS_D=\"0\"")
            xml_file.write(" STITCHABLE=\"no\"")
            xml_file.write(" DIR_NAME=\"\"")
            xml_file.write(" Z_RANGES=\"[0,%d)\""%(slice_no))
            
            pattern = re.compile(r"(.*)_meta.txt")
            image_name = pattern.findall(file_name)[0]
            print(image_name)
            xml_file.write(" IMG_REGEX=\"%s\">\n"%(image_name))
            
            xml_file.write("            <NORTH_displacements/>\n")
            xml_file.write("            <EAST_displacements/>\n")
            xml_file.write("            <SOUTH_displacements/>\n")
            xml_file.write("            <WEST_displacements/>\n")
            xml_file.write("        </Stack>\n")
    xml_file.write("    </STACKS>\n")
    xml_file.write("</TeraStitcher>\n")

