import tiffile as TFF
import numpy as np
import time,os,glob
from tkinter import filedialog
import tkinter as tk
import multiprocessing

# x flipped: done
# z order flipped in dorsal:
# z number donesn't match new shape

def segmented_transpose(n,filename,LoadedPagesNo,new_shape,isdorsal):
    #new_shape is a transposed shape, the order is axis 2 = z
    with TFF.TiffFile(filename) as tif:
        ori_z_layers = len(tif.pages)
    
    if isdorsal:
        z_start = ori_z_layers-1
        z_end = 0
        LoadedPagesNo = -LoadedPagesNo
        load_order = -1
    else:
        z_start = 0
        z_end = ori_z_layers
        load_order = 1
    
    ori_n = n
    diff = new_shape[2] - ori_z_layers
    if diff > 0:
        # check whether all the layers needed to load are simply zero filling matrix
        # if yes, skip the process
        if diff - (np.ceil(n/LoadedPagesNo)*LoadedPagesNo - z_start) > LoadedPagesNo:
            print("test")
        else:    
            filling_shape_z = (diff, tif.pages[0].shape[0],tif.pages[0].shape[1])
            if not isdorsal:
                # when new shape has z layers more than the image, the first several layers should
                # not be loaded from the original image. In this situation, any n smaller than
                # diff should not be loaded. so n-diff will make some n smaller than 0 in ventral 
                # cases. When n-diff<0, images should not be loaded, instead, 0 should be created
                # and filled.                
                n = n - diff
    
    if n + LoadedPagesNo < ori_z_layers or n + LoadedPagesNo > 0:
        print("n+LoadedPagesNo:%d"%(n + LoadedPagesNo))
        # when this if statement is satisfied, images can be loaded fully without worrying out of index 
        if n < 0 or n > ori_z_layers:
            filling_image = np.zeros(filling_shape_z,dtype = 'uint16')
            an_image = TFF.imread(filename, key = range(0,n+LoadedPagesNo-(diff%LoadedPagesNo),load_order))
            an_image = np.concatenate([filling_image,an_image], axis = 0)
        else:
            an_image = TFF.imread(filename, key = range(n,n+LoadedPagesNo,load_order))
        """        
        elif n < 0 and diff > LoadedPagesNo:
            remain_diff = diff - np.ceil(ori_n/LoadedPagesNo)*LoadedPagesNo
            if  remain_diff >= LoadedPagesNo:
                filling_shape = (LoadedPagesNo, tif.pages[0].shape[0],tif.pages[0].shape[1])
                an_image = np.zeros(filling_shape,dtype = 'uint16')
            else:
                filling_shape = (remain_diff, tif.pages[0].shape[0],tif.pages[0].shape[1])
                filling_image = np.zeros(filling_shape,dtype = 'uint16')
                an_image = TFF.imread(filename, key = range(n,n+LoadedPageNo-remain_diff))
                an_image = np.concatenate([filling_image,an_image], axis = 0)
        """           
    elif n + LoadedPagesNo > ori_z_layers or n+ LoadedPagesNo < 0:
        print(print("step_1:%d"%n))
        an_image = TFF.imread(filename, key = range(n,z_end,load_order))
        if isdorsal and diff > 0:
            filling_image = np.zeros(filling_shape_z,dtype = 'uint16')
            an_image = TFF.imread(filename, key = range(n+LoadedPagesNo-(diff%LoadedPagesNo),0,load_order))
            an_image = np.concatenate([an_image,filling_image], axis = 0)

    if isdorsal:
        an_image = np.flip(an_image,axis = 2)

    # create a zero matrix for filling to match the size of both images
    if tif.pages[0].shape[0] < new_shape[1]:
        filling_shape = (an_image.shape[0], new_shape[1]-tif.pages[0].shape[0],tif.pages[0].shape[1])
        filling_image = np.zeros(filling_shape,dtype = 'uint16')
        an_image = np.concatenate([filling_image,an_image], axis = 1)   
        
    an_image = an_image.transpose(2,1,0)
    str_n = str(ori_n)
    digit_diff = len(str(new_shape[2])) - len(str_n)
    str_n = "0"*digit_diff + str_n
    temp_img_name = "temp_" + str_n + ".tif"
    TFF.imsave(temp_img_name, an_image, bigtiff = True)

def image_recombination(n,temptifs_name,x_layer_no,x_size,isdorsal):  
    if n + x_layer_no < x_size:
        loading_range = range(n , n+x_layer_no)
    else:
        loading_range = range(n , x_size-1)
    #p = 0
    img = []
    for tempname in temptifs_name:  
        tmp = TFF.imread(tempname, key = loading_range)
        img.append(tmp)
        #p = p+1
    img = np.concatenate(img, axis = 2)
    #print("%d,%d"%(p,img.shape[2]))
    if isdorsal:
        img = np.flip(img, axis = 2)

    for m in loading_range:
        str_m = str(m)
        digit_diff = len(str(x_size)) - len(str_m)
        str_m = "0"*digit_diff + str_m
        img_name = "image_" + str_m + ".tif"    
        TFF.imsave(img_name, img[m-n], bigtiff = True)


def Save2Raw(filename,new_shape,isdorsal):
#def save_as_raw(filename, new_shape,isdorsal):
    core_no = multiprocessing.cpu_count()-1
    ram_use = 2e9
    """
    isdorsal = False
    new_shape = []
    # loading the image and getting its shape
    with TFF.TiffFile(filename) as tif:
        new_shape.append(tif.pages[0].shape[1]) 
        new_shape.append(tif.pages[0].shape[0])
        new_shape.append(len(tif.pages))
    """
    z_layers = new_shape[2]
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
    LoadedPagesNo = int(np.ceil(ram_use/BytesOnePage))
    print(LoadedPagesNo)

    t_start = time.time()
   
    # get chunks and transpose the axis to z,y,x
    Pool_input = [(layers,filename,LoadedPagesNo,new_shape,isdorsal) for layers in range(0,z_layers,LoadedPagesNo)]   
    Pool = multiprocessing.Pool(processes= core_no)
    Pool.starmap(segmented_transpose,Pool_input)
    Pool.close()
    
    ##recombine transposed chuncks and save to 2D images
    # get required parameters, and calculate the resources
    temptifs = glob.glob("temp*.tif")
    one_temptif_size = os.stat(temptifs[1]).st_size
    one_x_layer_size = one_temptif_size/new_shape[0]
    x_layer_no_to_load = round(ram_use/len(temptifs)/one_x_layer_size)
    print(x_layer_no_to_load)

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

    # get the shape of both images
    ventral_image = TFF.TiffFile(ventral_file)
    dorsal_image = TFF.TiffFile(dorsal_file)
    dorsal_shape = [len(dorsal_image.pages),dorsal_image.pages[0].shape[0], dorsal_image.pages[0].shape[1]]
    ventral_shape = [len(ventral_image.pages), ventral_image.pages[0].shape[0], ventral_image.pages[0].shape[1]]
    print([ventral_shape,dorsal_shape])
    print("step 1/6: aligning y-z frame")
    for n in [0,1]:
        if ventral_shape[n] > dorsal_shape[n]:
            diff = ventral_shape[n]-dorsal_shape[n]
            dorsal_shape[n] = dorsal_shape[n] + diff                    
        else:
            diff = dorsal_shape[n]-ventral_shape[n]
            ventral_shape[n] = ventral_shape[n] + diff      
    print(dorsal_shape,ventral_shape)
    folderpath = filedialog.askdirectory(title = "select the folder for storing converted data")
    os.chdir(folderpath)
    # convert ventral part
    """
    os.mkdir("ventral_image")
    os.chdir("ventral_image")
    Save2Raw(ventral_file,ventral_shape[::-1],False)
    os.remove("temp*.tif")
    """
    # convert dorsal part
    os.chdir(folderpath)
    #os.mkdir("dorsal_image")
    os.chdir("dorsal_image")
    Save2Raw(dorsal_file,dorsal_shape[::-1],True)
    os.remove("temp*.tif")
