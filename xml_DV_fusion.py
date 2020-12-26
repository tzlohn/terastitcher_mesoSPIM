import re, sys, os, glob, time
import tkinter as tk
from tkinter import filedialog, simpledialog
import tifffile as TFF
import numpy as np
import multiprocessing
from multiprocessing import get_context

def get_value(expression,text):
    output = expression.findall(text)
    value = ""
    for num in output[0]:
        value = value + num 
    value = float(value)
    return value

def cropped_overlap(tifname,shift,im_size,isdorsal,istest = False):
    if abs(shift) > 25:
    # 25 is the default searching range for overlapping correlation in Terastitcher 
        if not isdorsal:
            if shift < 0:
                crop_range = range(0,im_size[0]-abs(shift)+25)
            else:   
                crop_range = range(shift-25,im_size[0])
        else:
            if shift < 0:
                crop_range = range(abs(shift)-25,im_size[0])
            else:
                crop_range = range(0,im_size[0]-shift+25)

        if istest:
            im = TFF.imread(all_names[778])
            im = im[crop_range,:]
            if isdorsal:
                filename = "test_dorsal.tif"
            else:
                filename = "test_ventral.tif"
            TFF.imsave(filename,im,append = False, bigtiff = True)
        else:
            """
            file_Size = os.stat(all_names[n]).st_size
            if file_Size != 53214864:
                pass
            else:
            """      
            im = TFF.imread(tifname)
            im = im[crop_range,:]
            TFF.imwrite(tifname,im,append = False, bigtiff = True)
    else:
        pass

def generate_xml(z_overlap,x_shift,DV_dir, metafile = "" ):
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
    if metafile != "":
        with open(metafile,'r') as meta_file:
            im_info = meta_file.read()
            
            pattern = re.compile(r"[\[]pixel size of x \(um\)[\]] \: (\d+)(\.)?(\d+)?")
            pixel_size_x = get_value(pattern,im_info)

            pattern = re.compile(r"[\[]pixel size of y \(um\)[\]] \: (\d+)(\.)?(\d+)?")
            pixel_size_y = get_value(pattern,im_info)
            
            pattern = re.compile(r"[\[]pixel counts in x[\]] \: (\d+)")
            x_pixels = get_value(pattern,im_info)
            x_pixels = int(x_pixels)

            pattern = re.compile(r"[\[]z step size \(um\)[\]] \: (\d+)(\.)?(\d+)?")
            z_stepsize = get_value(pattern,im_info)
    
    os.chdir(DV_dir)
    # DVH refer to current coordinates, xyz refer to the coordinate of the mechanical stage
    dim_D = pixel_size_y
    dim_V = pixel_size_x
    dim_H = z_stepsize

    xml_name = DV_dir + "//" + "terastitcher_for_DV" + ".xml"
    foldername = ['ventral_image','dorsal_image']
    istest = False

    slice_no = []
    for folder in foldername:
    #for folder in ["dorsal_image"]:
        os.chdir(folder)
        tif_name = glob.glob("*.tif")
        x_size_ori = TFF.TiffFile(tif_name[0]).pages[0].shape
        slice_no.append(len(tif_name))
        
        if folder == "ventral_image":
            isDorsal = False
        elif folder == "dorsal_image":
            isDorsal = True

        if istest == False:
            if abs(x_shift) > 25:
                core_no = multiprocessing.cpu_count()-1
                pool_input = [(tif,x_shift,x_size_ori,isDorsal) for tif in tif_name]
                #Pool = multiprocessing.Pool(processes= core_no)
                print("The %s are being cropped to remove blank parts and pre-aligned in height"%folder)
                t_start = time.time()
                with get_context("spawn").Pool(processes = core_no) as Pool: 
                    result = Pool.starmap(cropped_overlap,pool_input)
                    Pool.close()
                t_end = time.time()
                print("total duration : %d s"%(t_end-t_start))

        else:
            cropped_overlap(778,x_shift,isDorsal,True)
            ventral_image = TFF.imread(tif_name[0])
            slice_no_ventral = len(tif_name)
        
        os.chdir(DV_dir)
    
    os.chdir(foldername[0])
    tif_name = glob.glob("*.tif")
    ventral_image = TFF.imread(tif_name[0])

    #offset_V = x_shift*dim_V
    offset_V = 0
    offset_H = (ventral_image.shape[1]-z_overlap)*dim_H

    total_row = 1
    total_column = 2
    shift_H = [0, ventral_image.shape[1] - z_overlap]
    #shift_V = [0, x_shift]
    shift_V = [0, x_shift]

    with open(xml_name,'w') as xml_file:
        xml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
        xml_file.write("<!DOCTYPE TeraStitcher SYSTEM \"TeraStitcher.DTD\">\n")
        xml_file.write("<TeraStitcher volume_format=\"TiledXY|2Dseries\" input_plugin=\"tiff2D\">\n")
        xml_file.write("    <stacks_dir value=\"%s\" />\n"%DV_dir)
        xml_file.write("    <ref_sys ref1=\"%d\" ref2=\"%d\" ref3=\"%d\" />\n"%(ref1,ref2,ref3))
        xml_file.write("    <voxel_dims V=\"%.2f\" H=\"%.2f\" D=\"%.2f\" />\n"%(dim_V,dim_H,dim_D))
        xml_file.write("    <origin V=\"%.3f\" H=\"%.3f\" D=\"%.3f\" />\n"%(ori_V,ori_H,ori_D))
        xml_file.write("    <mechanical_displacements V=\"%.2f\" H=\"%.2f\" />\n"%(offset_V,offset_H))
        xml_file.write("    <dimensions stack_rows=\"%d\" stack_columns=\"%d\" stack_slices=\"%d\" />\n"%(total_row,total_column,max(slice_no)))
        xml_file.write("    <STACKS>\n")
        
        for n in range(len(foldername)):
            xml_file.write("        <Stack N_CHANS=\"1\"")
            xml_file.write(" N_BYTESxCHAN=\"%d\""%(bit/8))
                
            xml_file.write(" ROW=\"%d\""%(n))
            xml_file.write(" COL=\"%d\""%(n))   
            xml_file.write(" ABS_H=\"%d\""%(shift_H[n]))
            xml_file.write(" ABS_V=\"%d\""%(shift_V[n]))
                
            xml_file.write(" ABS_D=\"0\"")
            xml_file.write(" STITCHABLE=\"yes\"")
            xml_file.write(" DIR_NAME=\"%s\""%(foldername[n]))
            xml_file.write(" Z_RANGES=\"[0,%d)\""%(slice_no[n]))
            xml_file.write(" IMG_REGEX=\"%s\">\n"%("yz_\d+.tif"))
                
            xml_file.write("            <NORTH_displacements/>\n")
            xml_file.write("            <EAST_displacements/>\n")
            xml_file.write("            <SOUTH_displacements/>\n")
            xml_file.write("            <WEST_displacements/>\n")
            xml_file.write("        </Stack>\n")
        xml_file.write("    </STACKS>\n")
        xml_file.write("</TeraStitcher>\n")
"""
if __name__ == "__main__":    
    root = tk.Tk()
    root.withdraw()

    DV_dir = filedialog.askdirectory(title = "select the folder containing folders for images from both sides")

    dim_D = simpledialog.askfloat(prompt = "the pixel size in y:", title = "")
    dim_V = simpledialog.askfloat(prompt = "the pixel size in x:", title = "")
    dim_H = simpledialog.askfloat(prompt = "the step size in z:", title = "")

    z_overlap = simpledialog.askinteger(prompt = "no. of overlapped layers between dorsal and ventral sides:", title = "")
    x_shift = simpledialog.askinteger(prompt = "relative (to ventral) pixel offset along the y axis of the image :", title = "")

    generate_xml(z_overlap,x_shift,DV_dir)
"""
