import tiffile as TFF
import numpy as np
import time,os,glob
from tkinter import filedialog
import tkinter as tk
import multiprocessing

def segmented_transpose(n,filename,LoadedPagesNo,new_shape,isdorsal):
    # new_shape is a transposed shape
    # n is the serial number of the first page to be loaded.
    with TFF.TiffFile(filename) as tif:
        ori_z_layers = len(tif.pages)

    diff = new_shape[1] - ori_z_layers
        
    if n + LoadedPagesNo < ori_z_layers :
        # when this if statement is satisfied, images can be loaded fully without worrying out of index 
        an_image = TFF.imread(filename, key = range(n,n+LoadedPagesNo))
    else:
        an_image = TFF.imread(filename, key = range(n,ori_z_layers-1))

    if isdorsal:
        if len(an_image.shape) == 3:
            an_image = np.flip(an_image,axis = 1)
        elif len(an_image.shape) == 2:
            an_image = np.flip(an_image,axis = )

    # create a zero matrix for filling to match the size of both images
    if tif.pages[0].shape[2] < new_shape[2]:
        filling_shape = (an_image.shape[0], tif.pages[0].shape[0], new_shape[2]-tif.pages[0].shape[1])
        filling_image = np.zeros(filling_shape,dtype = 'uint16')
        an_image = np.concatenate([filling_image,an_image], axis = 2)   
        
    an_image = an_image.transpose(1,0,2)
    if diff > 0:
        str_n = str(n+diff)
    else:
        str_n = str(n)
    digit_diff = len(str(new_shape[2])) - len(str_n)
    str_n = "0"*digit_diff + str_n
    temp_img_name = "temp_" + str_n + ".tif"
    TFF.imwrite(temp_img_name, an_image, bigtiff = True)
    return True

def image_recombination(n,temptifs_name,x_layer_no,x_size,isdorsal):  
    if n + x_layer_no < x_size:
        loading_range = range(n , n+x_layer_no)
    else:
        loading_range = range(n , x_size-1)

    img = []
    for tempname in temptifs_name:  
        tmp = TFF.imread(tempname, key = loading_range)
        img.append(tmp)

    img = np.concatenate(img, axis = 1)

    if isdorsal:
        img = np.flip(img, axis = 1)

    for m in loading_range:
        str_m = str(m)
        digit_diff = len(str(x_size)) - len(str_m)
        str_m = "0"*digit_diff + str_m
        img_name = "image_" + str_m + ".tif"    
        TFF.imwrite(img_name, img[m-n], bigtiff = True)

def Save2Raw(filename,new_shape,isdorsal):

    core_no = multiprocessing.cpu_count()-1
    ram_use = 2e9

    new_shape = tuple(new_shape)

    tif = TFF.TiffFile(filename)    
    if tif.pages[0].dtype ==  "uint16":
        byte = 2
    elif tif.pages[0].dtype == "uint8":
        byte = 1
    else:
        print("dtype is neither uint16 or uint8")

    BytesOnePage = byte * new_shape[0]*new_shape[2]
    # calculate the adequate number of pages to load
    LoadedPagesNo = int(np.ceil(ram_use/BytesOnePage))
    print("%d pages were loaded at once for conversion"%LoadedPagesNo)

    t_start = time.time()
    
    # create filling matrices for matching the shape of both images (ventral/dorsal)
    diff = new_shape[1] - len(tif.pages)
    if diff > 0:
        Filling_SN = range(0,diff,LoadedPagesNo)
        filling_shape_z = (new_shape[0], new_shape[2], LoadedPagesNo)
        filling_image = np.zeros(filling_shape_z,dtype = 'uint16')
        for n in Filling_SN:
            string_n = "0"*(len(str(new_shape[1])) - len(str(n)))+str(n)
            temp_img_name = "temp_" + string_n + ".tif"
            if n == Filling_SN[-1]:
                filling_shape_z = (new_shape[0], new_shape[2], diff-n)
                filling_image = np.zeros(filling_shape_z,dtype = 'uint16')
            TFF.imwrite(temp_img_name, filling_image, bigtiff = True)
    
    # get chunks and transpose the axis to z,y,x
    print("Step 1: segmented and transpose,\nmight take up to 3 hours for a color in 2X whole-body images")   
    Pool_input = [(layers,filename,LoadedPagesNo,new_shape,isdorsal) for layers in range(0,len(tif.pages),LoadedPagesNo)]   
    Pool = multiprocessing.Pool(processes= core_no)
    result = Pool.starmap(segmented_transpose,Pool_input)
    Pool.close()
    
    ##recombine transposed chuncks and save to 2D images
    # get required parameters, and calculate the resources
    print("Step 2: save transposed 3D image stack to 2D images slices,\nmight take up to 5 hours for a color in 2x whole-body images")
    temptifs = glob.glob("temp*.tif")
    one_temptif_size = os.stat(temptifs[0]).st_size
    one_x_layer_size = one_temptif_size/new_shape[0]
    x_layer_no_to_load = round(ram_use/len(temptifs)/one_x_layer_size)
    print("%d layers were loaded at once for recombination"%LoadedPagesNo)

    # divided the chunck and multiprocessing 
    Pool_input = [(layer,temptifs,x_layer_no_to_load,new_shape[0],isdorsal) for layer in range(0,new_shape[0],x_layer_no_to_load)]    
    Pool = multiprocessing.Pool(processes= core_no)
    Pool.starmap(image_recombination,Pool_input)
    Pool.close()

    t_end = time.time()
    print("%d"%(t_end-t_start))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    ventral_file = filedialog.askopenfilename(title = "select the ventral image")
    dorsal_file = filedialog.askopenfilename(title = "select the dorsal image")

    print("The program may take 10 hours or longer to run, depends on how big your images are\nIt has two parts:\n1) transpose the images from (x,y,z) to (z,y,x) \n2) save the two 2D images")
    # get the shape of both images
    ventral_image = TFF.TiffFile(ventral_file)
    dorsal_image = TFF.TiffFile(dorsal_file)
    dorsal_shape = [len(dorsal_image.pages),dorsal_image.pages[0].shape[0], dorsal_image.pages[0].shape[1]]
    ventral_shape = [len(ventral_image.pages), ventral_image.pages[0].shape[0], ventral_image.pages[0].shape[1]]
    print("The dimension of the ventral image and the dorsal image: %r, %r\n"%tuple([ventral_shape,dorsal_shape]))
    for n in [0,2]:
        if ventral_shape[n] > dorsal_shape[n]:
            diff = ventral_shape[n]-dorsal_shape[n]
            dorsal_shape[n] = dorsal_shape[n] + diff                    
        else:
            diff = dorsal_shape[n]-ventral_shape[n]
            ventral_shape[n] = ventral_shape[n] + diff      
    print("The new dimension of the ventral image and the dorsal image: %r, %r\n"%tuple([ventral_shape,dorsal_shape]))
    new_ventral_shape = [ventral_shape[1], ventral_shpae[0],ventral_shape[2]]
    new_dorsal_shape = [dorsal_shape[1], dorsal_shpae[0],dorsal_shape[2]]

    folderpath = filedialog.askdirectory(title = "select the folder for storing converted data")
    os.chdir(folderpath)
    
    # convert ventral part
    if not os.path.isdir("ventral_image"):
        os.mkdir("ventral_image")
    os.chdir("ventral_image")
    Save2Raw(ventral_file,new_ventral_shape,False)
    for file in glob.glob("temp*.tif"):
        os.remove(file)

    # convert dorsal part
    os.chdir(folderpath)
    if not os.path.isdir("dorsal_image"):
        os.mkdir("dorsal_image")
    os.chdir("dorsal_image")
    Save2Raw(dorsal_file,new_dorsal_shape,True)
    for file in glob.glob("temp*.tif"):
        os.remove(file)