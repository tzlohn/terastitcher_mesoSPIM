import re, sys, os, glob
import tkinter as tk
from tkinter import filedialog

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

folderpath = filedialog.askdirectory()

# create a new folder for future Left right fusion in the upper directory/folder
pattern = re.compile(r"(.*./)\w+$")
root_folder = pattern.findall(folderpath)
root_folder = root_folder[0]
os.chdir(root_folder)
if os.path.exists("LR_fusion"):
    pass
else:
    os.mkdir("LR_fusion")
os.chdir(folderpath)

# find out the illumination side
pattern = re.compile(r"(.*./)(Left|Right)(./.*./)?")
illumination_side = pattern.findall(folderpath)
illumination_side = illumination_side[0][1] 

xml_name = folderpath + "\\" + "terastitcher_for_XY" + ".xml"
meta_name = "meta_for_LR_fusion" + ".txt"

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
total_column = len(x_pos_all)

# Terasticher requires users to put the file in a order of the aligning/stitching direction
new_file_index = []
for a_file_name in file_list:
    y_pos = float(pattern_y.findall(a_file_name)[0])
    x_pos = float(pattern_x.findall(a_file_name)[0])
    #index = y_pos_all.index(y_pos) + x_pos_all.index(x_pos)*total_row
    index = x_pos_all.index(x_pos) + y_pos_all.index(y_pos)*total_column
    new_file_index.append(index)
sorted_file_list = [file_list for _, file_list in sorted(zip(new_file_index, file_list))]

if total_row > 1:
    offset_V = y_pos_all[0]-y_pos_all[1]
else:
    offset_V = 0

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
    slice_no = int(output[0])

    pattern = re.compile(r"[\[]x_pixels[\]] (\d+)")
    x_pixel_count = get_value(pattern,im_info)

    pattern = re.compile(r"[\[]y_pixels[\]] (\d+)")
    y_pixel_count = get_value(pattern,im_info)     

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
    for file_name in sorted_file_list:
        with open(file_name,'r') as this_im:
            im_info = this_im.read()
            xml_file.write("        <Stack N_BLOCKS=\"1\"")
            xml_file.write(" BLOCK_SIZES=\"%.2f\""%(slice_no*dim_D))
            xml_file.write(" BLOCKS_ABS_D=\"0\"")
            xml_file.write(" N_CHANS=\"1\"")
            xml_file.write(" N_BYTESxCHAN=\"%d\""%(bit/8))
            
            pattern = re.compile(r"[\[]y_pos[\]] (-)?(\d+)(\.)?(\d+)?")
            y_position = int(round(get_value(pattern,im_info)))
            y_index = y_pos_all.index(y_position)

            
            pattern = re.compile(r"[\[]x_pos[\]] (-)?(\d+)(\.)?(\d+)?")
            x_position = int(round(get_value(pattern,im_info)))
            x_index = x_pos_all.index(x_position)

            xml_file.write(" ROW=\"%d\""%(y_index))
            xml_file.write(" COL=\"%d\""%(x_index))   
            xml_file.write(" ABS_H=\"%.1f\""%(round(x_position/dim_H)))
            xml_file.write(" ABS_V=\"%.1f\""%(round(y_position/dim_V)))
            
            xml_file.write(" ABS_D=\"0\"")
            xml_file.write(" STITCHABLE=\"yes\"")
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

fusion_folder = root_folder + "/LR_fusion/"
os.chdir(fusion_folder)

if os.path.exists(meta_name):
    with open(meta_name,'a') as meta_file:
        meta_file.write("[x positions_%s] : %r\n" % (illumination_side,x_pos_all))
else:    
    with open(meta_name,'w') as meta_file:
        meta_file.write("[pixel size of x (µm)] : %.3f\n"%dim_H)
        meta_file.write("[pixel size of y (µm)] : %.3f\n"%dim_V)
        meta_file.write("[z step size (µm)] : %.3f\n"%dim_D)
        meta_file.write("[pixel counts in x] : %d\n"%x_pixel_count)
        meta_file.write("[pixel counts in y] : %d\n"%y_pixel_count)
        meta_file.write("[x positions_%s] : %r\n" % (illumination_side,x_pos_all))
