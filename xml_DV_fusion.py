import re, os, glob, time,sys
#import tkinter as tk
#from tkinter import filedialog, simpledialog
import tifffile as TFF
import multiprocessing
from multiprocessing import get_context

def get_value(expression,text):
    output = expression.findall(text)
    value = ""
    for num in output[0]:
        value = value + num 
    value = float(value)
    return value

def report_progress(filesize):
    all_file = glob.glob("*.tif")
    n = 0
    for a_file in all_file:
        if os.stat(a_file).st_size == filesize:
            n = n+1
    p = int(n*100/len(all_file))
    sys.stdout.write("\r{0} ({1}/{2})".format(">"*p+"="*(100-p),n,len(all_file)))
    sys.stdout.flush()

def check_file_size(folders,root_dir):
    
    filesize = []
    for a_folder in folders:
        os.chdir(a_folder)
        all_file = glob.glob("*.tif")
        for a_file in all_file:
            if not os.stat(a_file).st_size in filesize:
                filesize.append(os.stat(a_file).st_size)
        os.chdir(root_dir)
    
    return filesize

def cropped_overlap(tifname,shift,im_size,image_size,idx,isdorsal):
    # 25 is the default searching range for overlapping correlation in Terastitcher
    current_size =  os.stat(tifname).st_size
    if  current_size == max(image_size):
        if not isdorsal:
            if shift < 0:
                ##crop_range = range(0,im_size[0]-abs(shift)+25)
                crop_range = range(0,im_size[1]-abs(shift)+25)
            else:   
                ##crop_range = range(shift-25,im_size[0])
                crop_range = range(shift-25,im_size[1])
        else:
            if shift < 0:
                ##crop_range = range(abs(shift)-25,im_size[0])
                crop_range = range(abs(shift)-25,im_size[1])
            else:
                ##crop_range = range(0,im_size[0]-shift+25)
                crop_range = range(0,im_size[1]-shift+25)

        im = TFF.imread(tifname)
        im = im[:,crop_range]
        ##im = im[crop_range,:]
        TFF.imwrite(tifname,im,append = False, bigtiff = True)
        im_size = os.stat(tifname).st_size
        if idx%100 == 0:
            report_progress(im_size)

def generate_xml(x_shift,z_shift,DV_dir, metafile = "", isMain = True, dim_H = 6.5, dim_D = 6.5, dim_V = 6):
   
    os.chdir(DV_dir)

    xml_name = DV_dir + "//" + "terastitcher_for_DV" + ".xml"
    foldername = ['ventral_image','dorsal_image']

    isdone = True
    if isMain:
        if metafile != "":
            with open(metafile,'r') as meta_file:
                im_info = meta_file.read()    
                pattern = re.compile(r"[\[]dorsal relative to ventral shift in width[\]] \: (\d+)")
                output = pattern.findall(im_info)       
                if not output:
                    isdone = False
    
    if not isdone:            
        """check whether the process is done by their file sizes"""
        image_size_list = check_file_size(foldername,DV_dir)
        if len(image_size_list) > 2:
            print("some images have problem, please check their sizes")
            return False

        if len(image_size_list) == 2:
            for folder in foldername:
                os.chdir(folder)
                tif_name = glob.glob("*.tif")
                n=0
                while os.stat(tif_name[n]).st_size == min(image_size_list):
                    n=n+1
                    if n >= len(tif_name):
                        os.chdir(DV_dir)
                        os.chdir(foldername[1])
                        tif_name = glob.glob("*.tif")
                        n = 0
                break
        
            with TFF.TiffFile(tif_name[n]) as tif0:
                x_size_ori = tif0.pages[0].shape    
        
        os.chdir(DV_dir)

        slice_no = []
        for folder in foldername:
            os.chdir(folder)
            tif_name = glob.glob("*.tif")
            
            if len(image_size_list) == 1:
                with TFF.TiffFile(tif_name[0]) as tif0:
                    x_size_ori = tif0.pages[0].shape 
                    
            slice_no.append(len(tif_name))
            
            if folder == "ventral_image":
                isDorsal = False
            elif folder == "dorsal_image":
                isDorsal = True

            if abs(x_shift) > 25:
                core_no = multiprocessing.cpu_count()-1
                pool_input = [(tif,x_shift,x_size_ori,image_size_list,idx,isDorsal) for idx,tif in enumerate(tif_name)]
                print("The %s are being cropped to remove blank parts and pre-aligned in height"%folder)
                t_start = time.time()
                with get_context("spawn").Pool(processes = core_no) as Pool: 
                    result = Pool.starmap(cropped_overlap,pool_input)
                    Pool.close()

                sys.stdout.write("\r{0} ({1}/{2})".format(">"*100,len(tif_name),len(tif_name)))
                t_end = time.time()
                print("\ntotal duration : %d s"%(t_end-t_start))
            os.chdir(DV_dir)
        
    
    if isMain:
        '''
        reference refering is like transpose. ref1 indicates the V in terastitcher
        ref2 indicates H, ref3 indicates D. 1,2,3 is the 3 dimension indicators in your images.
        The follwing assigment tells the code to map the coordinates of your system to terastitcher
        the minus sign indicates that the tile will be aligned/stitched in the reverse order of the index
        ''' 
        # magic number zone # 
        ref1 = 1
        ref2 = 2
        ref3 = 3

        ori_V = 0 # unit: mm
        ori_H = 0
        ori_D = 0

        bit = 16
        ######################
            # DVH refer to current coordinates, xyz refer to the coordinate of the mechanical stage
        if metafile != "":
            with open(metafile,'r') as meta_file:
                im_info = meta_file.read()
                
                pattern = re.compile(r"[\[]pixel size of x \(um\)[\]] \: (\d+)(\.)?(\d+)?")
                ##dim_V = get_value(pattern,im_info)
                dim_H = get_value(pattern,im_info)

                pattern = re.compile(r"[\[]pixel size of y \(um\)[\]] \: (\d+)(\.)?(\d+)?")
                dim_D = get_value(pattern,im_info)
                
                pattern = re.compile(r"[\[]pixel counts in x[\]] \: (\d+)")
                x_pixels = get_value(pattern,im_info)
                x_pixels = int(x_pixels)

                pattern = re.compile(r"[\[]z step size \(um\)[\]] \: (\d+)(\.)?(\d+)?")
                ##dim_H = get_value(pattern,im_info)
                dim_V = get_value(pattern,im_info)
        ##offset_V = 0
        ##offset_H = (ventral_image.shape[1]-z_overlap)*dim_H
        offset_V = z_shift*dim_V
        offset_H = 0

        ##total_row = 1
        ##total_column = 2
        ##shift_H = [0, ventral_image.shape[1] - z_overlap]
        ##shift_V = [0, 0]

        total_row = 2
        total_column = 1
        shift_V = [0, z_shift]
        shift_H = [0, 0]    

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
                xml_file.write(" COL=\"%d\""%(0))   
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
    dim_H = simpledialog.askfloat(prompt = "the pixel size in x:", title = "")
    dim_V = simpledialog.askfloat(prompt = "the step size in z:", title = "")

    z_overlap = simpledialog.askinteger(prompt = "no. of overlapped layers between dorsal and ventral sides:", title = "")
    x_shift = simpledialog.askinteger(prompt = "relative (to ventral) pixel offset along the y axis of the image :", title = "")

    generate_xml(z_overlap,x_shift,DV_dir,dim_H = dim_H, dim_D = dim_D, dimV = dim_V)
"""
