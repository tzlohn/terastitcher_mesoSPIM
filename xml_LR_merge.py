import tkinter as tk
from tkinter import filedialog
import numpy as np
import tifffile as TFF
import os,time,shutil,re
import multiprocessing

def get_value(expression,text):
    output = expression.findall(text)
    value = ""
    for num in output[0]:
        value = value + num 
    value = float(value)
    return value

def find_all_0_rows(img):
    rows_of_zero = np.sum(img[0,:,:],axis = 1)
    index_of_0 = np.where(rows_of_zero == 0)[0]
    edge = [0,0]
    diff = 1
    if index_of_0.size == 0:
        pass
    else:
        if index_of_0[-1] != img.shape[1]-1:
            edge[1] = img.shape[1]-1
            n = -1
            if index_of_0[0] != 0:
                edge[0] = 0
            else:
                while diff == 1 and n < len(index_of_0)-2:
                    n = n+1
                    diff = index_of_0[n+1] - index_of_0[n]
                edge[0] = index_of_0[n]+1
        else:
            n = len(index_of_0)
            while diff == 1:
                n = n-1
                diff = index_of_0[n] - index_of_0[n-1]         
            edge[1] = index_of_0[n]-1
            
            if index_of_0[0] != 0:
                edge[0] = 0
            else:
                while diff == 1 and n < len(index_of_0)-2:
                    n = n+1
                    diff = index_of_0[n+1] - index_of_0[n]
                edge[0] = index_of_0[n]+1    
        
    return edge

def finding_index_for_zero(im_file, page_num, side):
    
    last_layers = TFF.imread(im_file, key = range(page_num-10,page_num,1))
    column_num = last_layers.shape[2]
    row_num = last_layers.shape[1]

    offset_threshold = find_all_0_rows(last_layers)
    
    if side == "left":
        delta = 1
        n = -1
    elif side == "right":
        delta = -1
        n = column_num-1

    size_of_0 = 1
    ini_set = n

    while size_of_0 != 0:
        n = n + delta
        column = last_layers[0,offset_threshold[0]:offset_threshold[1],n]
        if n == ini_set + delta:
            columns = column
        else:
            columns = columns + column
        index_of_0 = np.where(columns == 0)[0]
        size_of_0 = index_of_0.shape[0]

    return n

def get_dim_match_image(im, x_diff,y_diff,side):
    dim_shape = im.shape
    if side == "Right":
        if x_diff > 0:
            filling_zero_matrix  = np.zeros(shape = (dim_shape[0],x_diff), dtype = "uint16")
            im = np.concatenate([filling_zero_matrix,im], axis = 1)
        if y_diff > 0:
            filling_zero_matrix  = np.zeros(shape = (y_diff,im.shape[1]), dtype = "uint16")
            im = np.concatenate([filling_zero_matrix,im], axis = 0)            
    elif side == "Left":
        if x_diff < 0:
            filling_zero_matrix  = np.zeros(shape = (dim_shape[0],abs(x_diff)), dtype = "uint16")
            im = np.concatenate([im,filling_zero_matrix], axis = 1)
        if y_diff < 0:
            filling_zero_matrix  = np.zeros(shape = (abs(y_diff),im.shape[1]), dtype = "uint16")
            im = np.concatenate([im,filling_zero_matrix], axis = 0)
    return im.transpose(1,0)

def remove_comma_from_string(string):
    return string[0:len(string)-1]

def find_0_pos(all_positions,image_size_x,side):
    # this function tries to find out the part where the image contains 0
    pos_with_0 = []
    for pos in all_positions:
        if abs(pos) <= 0.5* image_size_x:
            pos_with_0.append(pos)
    # There might be several tile containing zero positions, so only return the extrem.
    if side == "Left":
        return max(pos_with_0)
    elif side == "Right":
        return min(pos_with_0)

def save2_2D(n,imfile,overlap_offset,cutting_pixel,x_diff,y_diff,side,dest_folder):    
    img = TFF.TiffFile(imfile)
    im = TFF.imread(imfile, key = n)

    if side == "Right":
        im = im[:,0:cutting_pixel - overlap_offset]

    elif side == "Left":    
        #im = im[:,cutting_pixel:size_left[1] - overlap_offset]
        im = im[:,cutting_pixel + overlap_offset :-1]

    an_image = get_dim_match_image(im,x_diff,y_diff,side)

    page_num_str = str(len(img.pages))
    n_str = str(n)
    digit_diff = len(page_num_str) - len(n_str)  
    n_str = "0"*digit_diff + n_str
    name = "image_" + n_str + ".tif"

    TFF.imwrite(name, an_image, bigtiff = True)
    shutil.move(name,dest_folder)

    return an_image.shape
# part 1: modify images according to meta files
# 1) rotates both images 90 degree
# 2) remove overlapped pixels to make both dimensions identical
def multiproc(Pool_input_right,Pool_input_left):
    core_no = multiprocessing.cpu_count()-1
    Pool = multiprocessing.Pool(processes= core_no)
    im_shape = Pool.starmap(save2_2D,Pool_input_right)
    im_shape = Pool.starmap(save2_2D,Pool_input_left)
    Pool.close()
    return im_shape

def matchLR_to_xml(metafile,working_folder,left_file,right_file,is_main_channel,DV, pos_zero = 0):
    # the option pos_zero can be assigned to a user defined 0 position

    # get required parameters from meta file
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
        
        x_pos_name = DV +" x positions left"
        pattern = re.compile(r"[\[]%s[\]] \: [\[](.*)[\]]"%x_pos_name)
        all_left_positions = pattern.findall(im_info)
        all_left_positions = all_left_positions[0].split()
        for ind,string in enumerate(all_left_positions):
            all_left_positions[ind] = float(remove_comma_from_string(string))-pos_zero

        x_pos_name = DV +" x positions right"
        pattern = re.compile(r"[\[]%s[\]] \: [\[](.*)[\]]"%x_pos_name)
        all_right_positions = pattern.findall(im_info)
        all_right_positions = all_right_positions[0].split()
        for ind,string in enumerate(all_right_positions):
            all_right_positions[ind] = float(remove_comma_from_string(string))-pos_zero

    with TFF.TiffFile(right_file) as right_tif:
        size_right = right_tif.pages[0].shape
        x_in_right = size_right[1]
        page_num_right = int(round(len(right_tif.pages)))

    with TFF.TiffFile(left_file) as left_tif:
        size_left = left_tif.pages[0].shape
        x_in_left = size_left[1]
        page_num_left = int(round(len(left_tif.pages)))

    total_L_portion = (all_left_positions[0] - all_left_positions[-1])/(x_pixels*pixel_size_x)+1
    total_R_portion = (all_right_positions[0] - all_right_positions[-1])/(x_pixels*pixel_size_x)+1
    offset_portion = (all_left_positions[0] - all_left_positions[1])/(x_pixels*pixel_size_x)

    os.chdir(working_folder)
    dest_folder = ["right_rot","left_rot"]
    if not os.path.exists(dest_folder[0]):
        os.mkdir(dest_folder[0])
    if not os.path.exists(dest_folder[1]):
        os.mkdir(dest_folder[1])

    ## removing 80% of overlap
    image_size = pixel_size_x * x_pixels
    pos_L = find_0_pos(all_left_positions,image_size,"Left")
    pos_L_idx = all_left_positions.index(pos_L)
    redundant_tile_L = pos_L_idx
    pos_R = find_0_pos(all_right_positions,image_size,"Right")
    pos_R_idx = all_right_positions.index(pos_R)
    redundant_tile_R = len(all_right_positions)-pos_R_idx-1

    ratio_of_Right = abs(pos_R + 0.5*image_size)/image_size 
    ratio_of_Left = abs(pos_L - 0.5*image_size)/image_size
    
    if ratio_of_Right >0.9 and pos_L == pos_R:
        # if one side has the ratio larger than 95%, the the other side will be totally discarded.
        overlap_offset_L = 0
        overlap_offset_R = x_pixels
    elif ratio_of_Left >0.9 and pos_L == pos_R:
        overlap_offset_R = 0
        overlap_offset_L = x_pixels
    else:
        # 20% overlap
        """
        overlap_offset_L = x_pixels-round((ratio_of_Left+0.1)*x_pixels)
        overlap_offset_R = x_pixels-round((ratio_of_Right+0.1)*x_pixels)
        """        
        overlap_offset_L = 1-ratio_of_Left+redundant_tile_L*offset_portion
        overlap_offset_R = 1-ratio_of_Right+redundant_tile_R*offset_portion
        overlap_offset_L = round((overlap_offset_L)/total_L_portion*x_in_left - 0.1*x_pixels)
        overlap_offset_R = round((overlap_offset_R)/total_R_portion*x_in_right - 0.1*x_pixels)
    
    print(("overlap_offset_L:%d,overlap_offset_R:%d,")%(overlap_offset_L,overlap_offset_R))
        
    # finding upper and lower 0 lines
    if is_main_channel == True:
        left_cutting_pixel = finding_index_for_zero(left_file, page_num_left, "left") # should be a number closer to 0
        right_cutting_pixel = finding_index_for_zero(right_file, page_num_right, "right") # should be a number closer to size_right
        y_diff = size_left[0]-size_right[0]
        x_diff = (size_left[1]-1 -left_cutting_pixel- overlap_offset_L)-(right_cutting_pixel-overlap_offset_R)
    else:
        with open(metafile,"r") as meta:
            im_info = meta.read()
            string = DV + " left cutting pixel"
            pattern = re.compile(r"[\[]%s[\]] \: (\d+)(\.)?(\d+)?"%string)
            left_cutting_pixel = int(get_value(pattern,im_info))
            string = DV + " right cutting pixel"
            pattern = re.compile(r"[\[]%s[\]] \: (\d+)(\.)?(\d+)?"%string)
            right_cutting_pixel = int(get_value(pattern,im_info))
            string = DV + " left overlap"
            pattern = re.compile(r"[\[]%s[\]] \: (\d+)(\.)?(\d+)?"%string)
            overlap_offset_L = int(get_value(pattern,im_info))
            string = DV + " right overlap"
            pattern = re.compile(r"[\[]%s[\]] \: (\d+)(\.)?(\d+)?"%string)
            overlap_offset_R = int(get_value(pattern,im_info))
            string = DV + " LR pixel difference in x"
            pattern = re.compile(r"[\[]%s[\]] \: (-?\d+)(\.)?(\d+)?"%string)
            x_diff = int(get_value(pattern,im_info))
            string = DV + " LR pixel difference in y"
            pattern = re.compile(r"[\[]%s[\]] \: (-?\d+)(\.)?(\d+)?"%string)
            y_diff = int(get_value(pattern,im_info))
    #x_diff = (left_cutting_pixel-overlap_offset_L)-(size_right[1]-overlap_offset_R-right_cutting_pixel)
    print(("left_cutting_pixel:%d,right_cutting_pixel:%d,")%(left_cutting_pixel,right_cutting_pixel))
    print(("x_diff:%d,y_diff:%d,")%(x_diff,y_diff))
    
    Pool_input_right = [(n,right_file,overlap_offset_R,right_cutting_pixel,x_diff,y_diff,"Right",dest_folder[0]) for n in range(page_num_right)]
    Pool_input_left = [(n,left_file,overlap_offset_L,left_cutting_pixel,x_diff,y_diff,"Left",dest_folder[1]) for n in range(page_num_left)]

    im_shape = multiproc(Pool_input_right,Pool_input_left)

    if is_main_channel == True:    
        # part 2: generate the xml file
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
        ###########
        dim_V = pixel_size_y
        dim_H = pixel_size_x
        dim_D = z_stepsize

        xml_name = "terastitcher_for_LR.xml"

        slice_no = [len(right_tif.pages),len(left_tif.pages)]
        
        shift_no = [1, (im_shape[0][0]-0.2*x_pixels)*pixel_size_x]
        offset_H = 0
        offset_V = shift_no[1]

        with open(xml_name,'w') as xml_file:
            xml_file.write("<?xml version=\"1.0\" encoding=\"UTF-8\" ?>\n")
            xml_file.write("<!DOCTYPE TeraStitcher SYSTEM \"TeraStitcher.DTD\">\n")
            xml_file.write("<TeraStitcher volume_format=\"TiledXY|2Dseries\" input_plugin=\"tiff2D\">\n")
            xml_file.write("    <stacks_dir value=\"%s\" />\n"%(working_folder))
            xml_file.write("    <ref_sys ref1=\"%d\" ref2=\"%d\" ref3=\"%d\" />\n"%(ref1,ref2,ref3))
            xml_file.write("    <voxel_dims V=\"%.2f\" H=\"%.2f\" D=\"%.2f\" />\n"%(dim_V,dim_H,dim_D))
            xml_file.write("    <origin V=\"%.3f\" H=\"%.3f\" D=\"%.3f\" />\n"%(ori_V,ori_H,ori_D))
            xml_file.write("    <mechanical_displacements V=\"%.2f\" H=\"%.2f\" />\n"%(offset_V,offset_H))
            xml_file.write("    <dimensions stack_rows=\"%d\" stack_columns=\"%d\" stack_slices=\"%d\" />\n"%(2,1,max(slice_no)))
            xml_file.write("    <STACKS>\n")
            
            for n in range(len(dest_folder)):
                xml_file.write("        <Stack N_CHANS=\"1\"")
                xml_file.write(" N_BYTESxCHAN=\"%d\""%(bit/8))
                    
                xml_file.write(" ROW=\"%d\""%(n))
                xml_file.write(" COL=\"%d\""%(0))   
                xml_file.write(" ABS_H=\"%.1f\""%(1))
                xml_file.write(" ABS_V=\"%.1f\""%(shift_no[n]))
                    
                xml_file.write(" ABS_D=\"0\"")
                xml_file.write(" STITCHABLE=\"yes\"")
                xml_file.write(" DIR_NAME=\"%s\""%(dest_folder[n]))
                xml_file.write(" Z_RANGES=\"[0,%d)\""%(slice_no[n]))
                xml_file.write(" IMG_REGEX=\"%s\">\n"%("image_\d+.tif"))
                    
                xml_file.write("            <NORTH_displacements/>\n")
                xml_file.write("            <EAST_displacements/>\n")
                xml_file.write("            <SOUTH_displacements/>\n")
                xml_file.write("            <WEST_displacements/>\n")
                xml_file.write("        </Stack>\n")
            xml_file.write("    </STACKS>\n")
            xml_file.write("</TeraStitcher>\n")
        
        return [left_cutting_pixel,right_cutting_pixel,overlap_offset_L,overlap_offset_R,x_diff,y_diff]
    else:
        return False

if __name__ == "__main__":
    root =  tk.Tk()
    root.withdraw()

    working_folder = filedialog.askdirectory(title = "selecting the working folder for storing stitched data")
    os.chdir(working_folder)

    meta_file = filedialog.askopenfilename(title = "select the meta file")
    left_file = filedialog.askopenfilename(title = "select the left image")
    right_file = filedialog.askopenfilename(title = "select the right image")
    matchLR_to_xml(meta_file,working_folder,left_file,right_file,True,"ventral")
