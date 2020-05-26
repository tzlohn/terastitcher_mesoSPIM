import numpy as np 
import tiffile as TFF
import scipy.stats  
import os
import matplotlib.pyplot as plt

def pearsonCorrelation(x,y):
     x = x - np.mean(x)
     y = y - np.mean(y)
     corr = np.sum(np.multiply(x,y))/(np.std(x)*np.std(y))
     corr = corr/(x.shape[0]*x.shape[1])
     return corr


def x_correlation(ventral_file,dorsal_file,z_layer,searching_range_x,search_range_y):
    
    with TFF.TiffFile(ventral_file) as v_tif:
        ventral_tif = v_tif.pages[z_layer]
        ventral_image = ventral_tiff.asarray()
        #ventral_stack = v_tif.pages[ven_layer-searching_range:ven_layer+searching_range]
        #ventral_stack = ventral_stack[0].asarray()

    dorsal_first_image = TFF.imread(dorsal_file, key = 0)
    
    '''
    corr_array = []
    layer_array = []
    n=0
    for ventral_layer in ventral_stack:
        ventral_image = ventral_layer.asarray()
        corr = pearsonCorrelation(ventral_image,dorsal_first_image)
        corr_array.append(corr)
        layer_array.append(overlap_z-searching_range+n)
        n=n+1

    corr_array = np.asarray(corr_array)
    max_ind = np.argmax(corr_array)
    layer_array = np.asarray(layer_array)
    plt.subplot().plot(layer_array,corr_array)
    plt.show()
    '''

    plt.subplot().imshow(ventral_image)
    plt.subplot().imshow(dorsal_first_image)
    plt.show()
    sx = round(searching_range/2)
    sy = round(searching_range/2)
    end_x = ventral_image.shape[1]
    end_y = ventral_image.shape[0]
    corr_matrix = np.zeros([dy,dx])
    n = 0
    for x in range(searching_range):
        for y in range(searching_range):
            dx = sx-x
            dy = sy-y
            if dx >= 0 and dy >= 0:
                ven_shift_img = ventral_image[0:end_y-dy,0:end_x-dx]
                dor_shift_img = dorsal_first_image[dy-1:-1,dx-1:-1]
            elif dx >= 0 and dy < 0:
                ven_shift_img = ventral_image[dy-1:-1,0:end_x-dx]
                dor_shift_img = dorsal_first_image[0:end_y-dy,dx-1:-1]
            elif dx < 0 and dy >= 0:
                ven_shift_img = ventral_image[0:end_y-dy,dx-1:-1]
                dor_shift_img = dorsal_first_image[dy-1:-1,0:end_x-dx]
            elif dx < and dy < 0:
                ven_shift_img = ventral_image[dy-1:-1,dx-1:-1]
                dor_shift_img = dorsal_first_image[0:end_y-dy,0:end_x-dx]                                            

            corr = pearsonCorrelation(ven_shift_img,dor_shift_img)
            corr_matrix[y,x] = corr
            n=n+1
            print([x,y,n,corr])    
    plt.subplot().imshow(corr_matrix)
    plt.show()
                

os.chdir("F:\TL200508\DV_fusion")
x_correlation("X0_Y-36216_rot_178_647_nm_647LP_1x.tif","X0_Y-37716_rot_358_647_nm_1x.tif",1732,40,40)