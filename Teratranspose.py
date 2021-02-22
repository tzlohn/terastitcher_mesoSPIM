import tifffile as TFF
import numpy as np
import time,os,glob,re,random,sys
#from tkinter import filedialog
#import tkinter as tk
import multiprocessing
from multiprocessing import get_context
from psutil import virtual_memory

def find_key_from_meta(all_line_string,key):
    #print(key)
    a_line = "nothing should be the same"
    n = -1
    while a_line == "nothing should be the same" and n < len(all_line_string):
        n = n+1
        current_str = all_line_string[n]
        pattern = re.compile(r"[\[](%s)[\]]( \:)? (.*)?\n"%key)
        a_line_all = pattern.findall(current_str)
        if not a_line_all:
            a_line = "nothing should be the same"
        else: 
            a_line = a_line_all[0][0]
            value = a_line_all[0][-1]
    
    if not value:
        return [n,"not_a_value"] 
    else:    
        return [n,value]
        
def edit_meta(metaFile,key,value):
    new_line = "["+ key.replace("\\","") + "]" + " : " + str(value) +"\n"
    meta = open(metaFile,"r")
    all_lines = meta.readlines()
    meta.close()
    [line_sn,value] = find_key_from_meta(all_lines,key)
    all_lines[line_sn] = new_line

    if line_sn < len(all_lines):
        with open(metaFile,"w") as meta:
            meta.writelines(all_lines)

def find_image_edge(img_file):
    img_info = TFF.TiffFile(img_file)
    z_layers = len(img_info.pages)
    if z_layers > 30:
        loading_range = range(round(z_layers/2)-10,round(z_layers/2)+10)
    else:
        loading_range = round(z_layers/2)
    img = TFF.imread(img_file, key = loading_range)
    # projection
    img = np.sum(img, axis = 0) 
    # find columns with only zero
    sum_over_row = img.sum(axis = 0)
    index_of_0 = np.where(sum_over_row == 0)[0]
    diff_index0 = np.diff(index_of_0)
    edge_index = np.where(diff_index0 > 1)[0]
    if index_of_0.size == 0:
        edge_left = 0
        edge_right = img.shape[1]-1
    else:
        if edge_index.size == 0:
            if index_of_0[-1] == img.shape[1]-1:
                edge_left = 0
                edge_right = index_of_0[0]-1
            elif index_of_0[0] == 0:
                edge_left = index_of_0[-1]+1
                edge_right = img.shape[1]-1
        elif edge_index.size == 1:
            edge = edge_index[0]
            edge_left = index_of_0(edge)+1 
            edge_right = index_of_0(edge+1)-1 

    # finding row with only zero        
    sum_over_column = img.sum(axis = 1)
    index_of_0 = np.where(sum_over_column == 0)[0]
    diff_index0 = np.diff(index_of_0)
    edge_index = np.where(diff_index0 > 1)[0]
    if index_of_0.size == 0:
        edge_up = 0
        edge_down = img.shape[0]-1
    else:
        if edge_index.size == 0:
            if index_of_0[-1] == img.shape[0]-1:
                edge_up = 0
                edge_down = index_of_0[0]-1
            elif index_of_0[0] == 0:
                edge_up = index_of_0[-1]+1
                edge_down = img.shape[0]-1
        elif edge_index.size == 1:
            edge = edge_index[0]
            edge_up = index_of_0(edge)+1 
            edge_down = index_of_0(edge+1)-1    
    return [edge_up,edge_down,edge_left,edge_right]

def removeErrorFiles(file_list,core_no):
    """
    Memory error from pickling might happens during processing of a file, this file needs to be removed,
    because it doesn't contain complete information and might crash next steps which need it.
    file_list : the list of file which needs to be examined. The newest batch file from the file_list will be found and deleted.
    core_no: the number of cores used to run multiprocessing
    """
    modified_time = []
    for a_file in file_list:
        modified_time.append(os.path.getmtime(a_file))
        sorted_modified_file = [file for _,file in sorted(zip(modified_time,file_list))]

    for n in range(len(file_list)-core_no, len(file_list)):
        os.remove(sorted_modified_file[n])
        print("remove %s"%sorted_modified_file[n])

def progress_bar(total_length,key):
    file_list = glob.glob(key)
    n = len(file_list)
    p = int(n*100/total_length)
    if p > 100:
        p = 100
    sys.stdout.write("\r{0}| ({1}/{2})".format(">"*p+"="*(100-p),n,total_length))
    sys.stdout.flush()

def segmented_transpose(n,filename,LoadedPagesNo,edge_index,new_shape,isdorsal):
    # new_shape is a transposed shape
    # n is the serial number of the first page to be loaded.
    with TFF.TiffFile(filename) as tif:
        ori_z_layers = len(tif.pages)

    diff = new_shape[2] - ori_z_layers

    if diff > 0 and not isdorsal:        
        str_n = str(n+diff)
    else:
        str_n = str(n)
    digit_diff = len(str(new_shape[1])) - len(str_n)
    str_n = "0"*digit_diff + str_n
    temp_img_name = "temp_" + str_n + ".tif"

    if not os.path.exists(temp_img_name):    
        if n + LoadedPagesNo < ori_z_layers :
            # when this if statement is sufficed, images can be loaded fully without worrying out of index 
            try:
                an_image = TFF.imread(filename, key = range(n,n+LoadedPagesNo))
            except:
                for p in range(LoadedPagesNo):
                    a_slice = TFF.imread(filename, key = n+p)
                    if isinstance(a_slice,np.ndarray):
                        if p == 0:
                            an_image= np.zeros(shape=(LoadedPagesNo,a_slice.shape[0],a_slice.shape[1]),dtype = a_slice.dtype)
                        an_image[p,:,:] = a_slice
                    else:
                        if p == 0:
                            q = 1
                            while not isinstance(a_slice,np.ndarray):
                                a_slice = TFF.imread(filename, key = n+p+q)
                                q=q+1
                            an_image= np.zeros(shape=(LoadedPagesNo,a_slice.shape[0],a_slice.shape[1]),dtype = a_slice.dtype)
                            an_image[p,:,:] = a_slice
                        else:
                            an_image[p,:,:] = an_image[p-1,:,:]    
        else:
            an_image = TFF.imread(filename, key = range(n,ori_z_layers))
        
        if len(an_image.shape) == 2:
            an_image = an_image[edge_index[0]:edge_index[1],edge_index[2]:edge_index[3]]
            an_image = an_image[np.newaxis,...]
        else:    
            an_image = an_image[:,edge_index[0]:edge_index[1],edge_index[2]:edge_index[3]]

        if isdorsal:
            an_image = np.flip(an_image,axis = 1)

        # create a zero matrix for filling to match the size of both images
        if an_image.shape[1] < new_shape[1]:
            filling_shape = (an_image.shape[0], new_shape[1]-an_image.shape[1], an_image.shape[2])
            filling_image = np.zeros(filling_shape,dtype = 'uint16')
            an_image = np.concatenate([an_image,filling_image], axis = 1)     
        an_image = an_image.transpose(2,1,0)

        TFF.imwrite(temp_img_name, an_image, bigtiff = True)
        progress_bar(int(new_shape[2]/LoadedPagesNo),"temp*.tif")
    else:
        pass

def image_recombination(n,temptifs_name,x_layer_no,x_size,isdorsal):      

    if isdorsal:
        name_prefix = "dorsal_"
    else:
        name_prefix = "ventral_"

    if n + x_layer_no < x_size:
        loading_range = range(n , n+x_layer_no)
    else:
        loading_range = range(n , x_size-1)
    img = [None]*len(temptifs_name)
    
    isdoing = False
    for m in loading_range:
        str_m = str(m)
        digit_diff = len(str(x_size)) - len(str_m)
        str_m = "0"*digit_diff + str_m
        img_name = name_prefix + str_m + ".tif"
        if not os.path.exists(img_name):          
            isdoing = True
            break
    
    if isdoing:
        counting_order = [x for x in range(len(temptifs_name))]
        #randomize the loading of temp image files can prevent all process try to access the same temp image file.
        random.shuffle(counting_order)
        
        for idx in counting_order:
            tempname = temptifs_name[idx]
            tmpinfo = TFF.TiffFile(tempname)
            if len(tmpinfo.pages) == 1:
                """A very interesting bug: when interrogate it by Tifffile or Fiji, it detects a 2D image, 
                but after reading as numpy, it recovers to be 3D"""
                tmp = TFF.imread(tempname)
                tmp = tmp[loading_range,:,:]
            else:                  
                tmp = TFF.imread(tempname, key = loading_range)
            img[idx] = tmp

        img = np.concatenate(img, axis = 2)

        if isdorsal:
            img = np.flip(img, axis = 2)
            name_prefix = "dorsal_"
        else:
            name_prefix = "ventral_"
        
        for m in loading_range:
            str_m = str(m)
            digit_diff = len(str(x_size)) - len(str_m)
            str_m = "0"*digit_diff + str_m
            img_name = name_prefix + str_m + ".tif"
            if not os.path.exists(img_name):     
                TFF.imwrite(img_name, img[m-n].transpose(), bigtiff = True)

        progress_bar(x_size-1,name_prefix+"*.tif")

def generate_zero_image_for_z(n, new_shape, filename, LoadedPagesNo,isdorsal=False):
    
    string_n = "0"*(len(str(new_shape[2])) - len(str(n)))+str(n)
    temp_img_name = "temp_" + string_n + ".tif"
    if not os.path.exists(temp_img_name):
        TFFim = TFF.TiffFile(filename)
        diff = new_shape[2] - len(TFFim.pages) 
        if not isdorsal:
            Filling_SN = range(0,diff,LoadedPagesNo)
        else:
            Filling_SN = range(len(TFFim.pages),diff+len(TFFim.pages),LoadedPagesNo)
        filling_shape_z = (new_shape[0]-1, new_shape[1], LoadedPagesNo)
        filling_image = np.zeros(filling_shape_z,dtype = 'uint16')

        if n == Filling_SN[-1]:
            if not isdorsal:
                filling_shape_z = (new_shape[0]-1, new_shape[1], diff-n)
            else:
                filling_shape_z = (new_shape[0]-1, new_shape[1], new_shape[2]-n)
            filling_image = np.zeros(filling_shape_z,dtype = 'uint16')
        
        TFF.imwrite(temp_img_name, filling_image, bigtiff = True)

        progress_bar(len(Filling_SN),"temp*.tif")
    else:
        pass

def findLostFile(stepsize,tifpages,diff,isdorsal):
    tifname = glob.glob("*.tif")

    SNlist = []
    for atif in tifname:
        pattern = re.compile(r"temp_(\d+)")
        SN = pattern.findall(atif)
        SN = SN[0]
        SNlist.append(int(SN))

    p=0
    if diff <= 0 or isdorsal:
        indlist = range(0,tifpages,stepsize)
    else:
        indlist = range(diff,tifpages+diff,stepsize)
    
    returnlist = []
    for ind in indlist:
        if SNlist[p] - ind > 0:
            returnlist.append(ind)        
        else:
            p = p+1
    return returnlist

def trapoSave(filename,new_shape,edge_index,isdorsal=False):

    # the following line prevent stuck in multiprocessing, which should work with get_context
    #set_start_method("spawn")
    
    total_core_no = multiprocessing.cpu_count() 
    core_no = int(np.sqrt(total_core_no)*np.floor(np.sqrt(total_core_no)))
    mem = virtual_memory()
    ram_use = mem.free*0.7/core_no

    if ram_use > 9*(1024**3):
        ram_use = 9*(1024**3)
 
    new_shape = tuple(new_shape)

    tif = TFF.TiffFile(filename)    
    if tif.pages[0].dtype ==  "uint16":
        byte = 2
    elif tif.pages[0].dtype == "uint8":
        byte = 1
    else:
        print("dtype is neither uint16 or uint8")

    BytesOnePage = byte * new_shape[0]*new_shape[1]
    # calculate the adequate number of pages to load
    LoadedPagesNo = int(ram_use//BytesOnePage)
    
    t_start = time.time()
    
    # create filling matrices for matching the shape of both images (ventral/dorsal)
    diff = new_shape[2] - len(tif.pages)
    
    if isdorsal:
        yz_name = "dorsal*.tif"
    else:
        yz_name = "ventral*.tif"
    final_list = glob.glob("yz*.tif")

    if diff> 0:
        yzlist = glob.glob(yz_name)

        if not yzlist and not final_list:
            templist = glob.glob("temp*.tif")
            if templist:
                with TFF.TiffFile(templist[0]) as temptif:
                    LoadedPagesNo = temptif.pages[0].shape[1]
                    temptif.close()
            #print(len(range(0,diff,LoadedPagesNo)))
            if len(templist) < len(range(0,diff,LoadedPagesNo)):
                if not isdorsal:
                    Pool_input = [(layers, new_shape, filename, LoadedPagesNo,isdorsal) for layers in range(0,diff,LoadedPagesNo)]
                else:
                    Pool_input = [(layers, new_shape, filename, LoadedPagesNo,isdorsal) for layers in range(len(tif.pages),diff+len(tif.pages),LoadedPagesNo)]
                print("Creating blank images to fill the differences between ventral and dorsal")
                with get_context("spawn").Pool(processes = core_no) as Pool:
                    result = Pool.starmap(generate_zero_image_for_z,Pool_input)
                    Pool.close()
                    Pool.join()
    
    yzlist = glob.glob(yz_name)
    # if images are under combination (can be interogated by finding the existance of any yz*.tif), the transpose step should be skipped 
    if not yzlist and not final_list:
        # get chunks and transpose the axis to z,y,x
        print("\nStep 1: segmented and transpose,\nmight take up to 3 hours for a color in 2X whole-body images")
        templist = glob.glob("temp*.tif")
        if templist:
            with TFF.TiffFile(templist[0]) as tiftemp:
                LoadedPagesNo = tiftemp.pages[0].shape[1]
                tiftemp.close()
        print("%d pages were loaded per image for transpose"%LoadedPagesNo) 
        Pool_input = [(layers,filename,LoadedPagesNo,edge_index,new_shape,isdorsal) for layers in range(0,len(tif.pages),LoadedPagesNo)]
        
        while not templist or len(templist) < new_shape[2]//LoadedPagesNo:
            with get_context("spawn").Pool(processes = core_no) as Pool:
                try:
                    result = Pool.starmap(segmented_transpose,Pool_input)
                    Pool.close()       
                except:
                    Pool.close()
                    Pool.join()
                    print("\nPickling problems causes memory error in multiprocessing")
                    print(time.asctime())
                    tempfilelist = glob.glob("temp*.tif")
                    removeErrorFiles(tempfilelist,core_no)
            templist = glob.glob("temp*.tif")
            Pool.join()
       
        """
        #multiprocessing will sometimes skip some items in list, the following code find the lost items and get them.
        lost_list = findLostFile(LoadedPagesNo,len(tif.pages),diff,isdorsal)
        #Pool.close()
        while(lost_list):
            print("some skipped layers were found")            
            Pool_input = [(layers,filename,LoadedPagesNo,edge_index,new_shape,isdorsal) for layers in lost_list]
            with get_context("spawn").Pool(processes = core_no) as Pool:
                result = Pool.starmap(segmented_transpose,Pool_input)
                Pool.close()
            lost_list = findLostFile(LoadedPagesNo,len(tif.pages),diff,isdorsal)            
        """
    ##recombine transposed chuncks and save to 2D images
    # get required parameters, and calculate the resources
    
    if not final_list:
        if not yzlist or len(yzlist) < new_shape[0]-1:
            print("\nStep 2: saving transposed 3D image stack to 2D images slices,\nmight take up to 5 hours for a color in 2x whole-body images") 
            ram_use = mem.free*0.8/core_no
            if ram_use > 9*(1024**3):
                ram_use = 9*(1024**3)    
            temptifs = glob.glob("temp*.tif")
            one_temptif_size = os.stat(temptifs[0]).st_size
            one_x_layer_size = one_temptif_size/new_shape[0]
            x_layer_no_to_load = int(round(ram_use/len(temptifs)/one_x_layer_size))
            print("%d layers were loaded at once for recombination"%x_layer_no_to_load)

            # divided the chunck and multiprocessing 
            Pool_input = [(layer,temptifs,x_layer_no_to_load,new_shape[0],isdorsal) for layer in range(0,new_shape[0],x_layer_no_to_load)]
            while not yzlist or len(yzlist) < new_shape[0]-1:
                with get_context("spawn").Pool(processes = core_no) as Pool:
                    try:
                        result = Pool.starmap(image_recombination,Pool_input)
                        Pool.close()
                    except:
                        """
                        sometimes the multiprocessing breaks because of memory issue
                        this except prvent the crash, and remove problematic files
                        """
                        Pool.close()
                        Pool.join()
                        print("\npickling problem happens and causes memory error")
                        print(time.asctime())
                        yzlist = glob.glob(yz_name)
                        removeErrorFiles(yzlist,core_no)
                yzlist = glob.glob(yz_name)
                Pool.join()

    t_end = time.time()
    t_duration = t_end-t_start
    t_hour = t_duration // 3600
    t_minute = (t_duration % 3600) // 60
    t_second = (t_duration % 3600) % 60
    if isdorsal:
        side = "dorsal"
    else:
        side = "ventral"
    print("\ntotal duration for processing %s: %d hour(s) %d minute(s) %d second(s) \n"%(side,t_hour,t_minute,t_second))

def teratranspose(ventral_file,dorsal_file,folderpath, meta_file, is_mainChannel = True):
    if is_mainChannel:
        edge_index_ventral = find_image_edge(ventral_file)
        edge_index_dorsal = find_image_edge(dorsal_file)
        key = "ventral edge index"
        edit_meta(meta_file, key, edge_index_ventral)
        key = "dorsal edge index"
        edit_meta(meta_file, key, edge_index_dorsal)
    else:
        with open(meta_file,"r") as meta:
            im_info = meta.read()
            for side in ["ventral edge index","dorsal edge index"]:
                pattern = re.compile(r"[\[]%s[\]] \: [\[](-?\d+), (-?\d+), (-?\d+), (-?\d+)[\]]"%side)
                found_values = pattern.findall(im_info)
                found_values = found_values[0]
                if side == "ventral edge index":
                    edge_index_ventral = []
                    for value in found_values:
                        edge_index_ventral.append(int(value))
                elif side == "dorsal edge index":
                    edge_index_dorsal = []
                    for value in found_values:
                        edge_index_dorsal.append(int(value))                    
      
    #print(edge_index_ventral)
    #print(edge_index_dorsal)

    print("This step may take 10 hours or longer to run, depends on how big your images are\nIt has two parts:\n1) transpose the images from (x,y,z) to (z,y,x) \n2) save them to 2D images")
    # get the shape of both images
    dorsal_image = TFF.TiffFile(dorsal_file)
    ventral_image = TFF.TiffFile(ventral_file)
    dorsal_shape = [len(dorsal_image.pages),edge_index_dorsal[1]-edge_index_dorsal[0]+1, edge_index_dorsal[3]-edge_index_dorsal[2]+1]
    ventral_shape = [len(ventral_image.pages), edge_index_ventral[1]-edge_index_ventral[0]+1, edge_index_ventral[3]-edge_index_ventral[2]+1]
    print("The dimension of the ventral image and the dorsal image:\n %r, %r\n"%tuple([ventral_shape,dorsal_shape]))
    for n in [0,1]:
        if ventral_shape[n] > dorsal_shape[n]:
            diff = ventral_shape[n]-dorsal_shape[n]
            dorsal_shape[n] = dorsal_shape[n] + diff                    
        else:
            diff = dorsal_shape[n]-ventral_shape[n]
            ventral_shape[n] = ventral_shape[n] + diff      
    print("The new dimension of the ventral image and the dorsal image:\n %r, %r\n"%tuple([ventral_shape,dorsal_shape]))
    new_ventral_shape = [ventral_shape[2], ventral_shape[1],ventral_shape[0]]
    new_dorsal_shape = [dorsal_shape[2], dorsal_shape[1],dorsal_shape[0]]

    # convert ventral part
    
    if not os.path.isdir("ventral_image"):
        os.mkdir("ventral_image")
    os.chdir("ventral_image")
    print("transpose the ventral image...")
    trapoSave(ventral_file,new_ventral_shape,edge_index_ventral,False)
    for file in glob.glob("temp*.tif"):
        os.remove(file)
    
    # convert dorsal part
    os.chdir(folderpath)
    if not os.path.isdir("dorsal_image"):
        os.mkdir("dorsal_image")
    os.chdir("dorsal_image")
    print("transpose the dorsal image...")
    trapoSave(dorsal_file,new_dorsal_shape,edge_index_dorsal,True)
    for file in glob.glob("temp*.tif"):
        os.remove(file)
"""
if __name__ == "__main__":
    
    root = tk.Tk()
    root.withdraw()

    ventral_file = filedialog.askopenfilename(title = "select the ventral image")
    dorsal_file = filedialog.askopenfilename(title = "select the dorsal image")
    trapoSave()
"""