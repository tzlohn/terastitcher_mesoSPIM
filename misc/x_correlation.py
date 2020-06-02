'''
This is a code under development.
This code tries to find out the shift of 2 images by automatically maximize their correlations.
Different from the autocorrleation function is Scipy, this code provides some function which
can perform autocorrelation in a narrow range, which can save a lot of computing time.
'''

import numpy as np 
import tiffile as TFF
import scipy.stats  
import os
import matplotlib.pyplot as plt

def matchImageSize(img1,img2):
    
    diff_y = img1.shape[0] - img2.shape[0]
    diff_x = img1.shape[1] - img2.shape[1]

    if diff_y <= 0 and diff_x <= 0:
        filling_matrix_y = np.zeros([abs(diff_y),img1.shape[1]])
        img1 = np.concatenate([img1,filling_matrix_y], axis = 0)
        filling_matrix_x = np.zeros([img1.shape[0],abs(diff_x)])
        img1 = np.concatenate([img1,filling_matrix_x], axis = 1)
    elif diff_y > 0 and diff_x < 0:
        filling_matrix_y = np.zeros([abs(diff_y),img2.shape[1]])
        img2 = np.concatenate([img2,filling_matrix_y], axis = 0)        
        filling_matrix_x = np.zeros([img1.shape[0],abs(diff_x)])
        img1 = np.concatenate([img1,filling_matrix_x], axis = 1)    
    elif diff_x < 0 and diff_y > 0:
        filling_matrix_y = np.zeros([abs(diff_y),img2.shape[1]])
        img2 = np.concatenate([img2,filling_matrix_y], axis = 0)
        filling_matrix_x = np.zeros([img1.shape[0],abs(diff_x)])        
        img1 = np.concatenate([img1,filling_matrix_x], axis = 1)
    elif diff_x > 0 and diff_x > 0:
        filling_matrix_y = np.zeros([abs(diff_y),img2.shape[1]])
        img1 = np.concatenate([img1,filling_matrix_y], axis = 0)
        filling_matrix_x = np.zeros([img2.shape[0],abs(diff_x)])
        img1 = np.concatenate([img1,filling_matrix_x], axis = 1)

    return [img1,img2]

def pearsonCorrelation(x,y):
    x = x - np.mean(x)
    y = y - np.mean(y)
    corr = np.sum(np.multiply(x,y))/(np.std(x)*np.std(y))
    corr = corr/(x.shape[0]*x.shape[1])
    return corr

def shiftImage(matrix1,matrix2,dx,dy):
    end_y = matrix1.shape[0]
    end_x = matrix1.shape[1]
    shift_mx1 = np.zeros([end_y-dy,end_x-dx], dtype = "uint16")
    shift_mx2 = np.zeros([end_y-dy,end_x-dx], dtype = "uint16")
    if dx >= 0 and dy >= 0:
        shift_mx1 = matrix1[0:end_y-dy,0:end_x-dx]
        shift_mx2 = matrix2[dy:end_y,dx:end_x]
    elif dx >= 0 and dy < 0:
        dy = abs(dy)
        shift_mx1 = matrix1[dy:end_y,0:end_x-dx]
        shift_mx2 = matrix2[0:end_y-dy,dx:end_x]
    elif dx < 0 and dy >= 0:
        dx = abs(dx)
        shift_mx1 = matrix1[0:end_y-dy,dx:end_x]
        shift_mx2 = matrix2[dy:end_y,0:end_x-dx]
    elif dx < 0 and dy <0:
        dx = abs(dx)
        dy = abs(dy)
        shift_mx1 = matrix1[dy:end_y,dx:end_x]
        shift_mx2 = matrix2[0:end_y-dy,0:end_x-dx]
    
    return [shift_mx1,shift_mx2]


def narrorwXcorrelation(matrix1,matrix2, shift_x, shift_y, range_x, range_y):

    sx = round(range_x/2)
    sy = round(range_y/2)
    corr_matrix = np.zeros([range_y,range_x], dtype = "float32")
    for x in range(range_x):
        for y in range(range_y):
            dx = sx-x+shift_x
            dy = sy-y+shift_y
            [shift_mx1,shift_mx2] = shiftImage(matrix1,matrix2,dx,dy)
            corr = pearsonCorrelation(shift_mx1,shift_mx2)
            corr_matrix[y,x] = corr
    return corr_matrix

def Xcorrelation(ventral_file,dorsal_file,z_layer,sf_x,sf_y,sf_z):
    '''
        ventral_file and dorsal_file must have the same dimension size in x and y
        z_layer is the most similar layer in ventral file to the first layer of the dorsal file
        sf_x, sf_y, and sf_z is the initial guess of the shift. the first image of the ventral file is the base to compare
    '''
    # magic-number zone. Following numbers are the searching ranges 
    sr_x = 60
    sr_y = 60
    sr_z = 30

    with TFF.TiffFile(ventral_file) as v_tif:
        ventral_tif = v_tif.pages[z_layer]
        ventral_image = ventral_tif.asarray()
        ventral_stack = v_tif.pages[z_layer-round(sr_z/2):z_layer+round(sr_z/2)]
        #ventral_stack = ventral_stack[0].asarray()

    dorsal_first_image = TFF.imread(dorsal_file, key = 0)
    
    repeat = 0
    current_layer = z_layer
    next_layer = 0
    while current_layer != next_layer:
        current_layer = next_layer
        # calculate the correlation in x,y plane
        [ventral_image,dorsal_image] = matchImageSize(ventral_image,dorsal_first_image)
        print("Images are matched")
        corr_matrix = narrorwXcorrelation(ventral_image,dorsal_image,sf_x,sf_y,sr_x,sr_y)
        max_ind = corr_matrix.argmax()
        shift_yx = np.unravel_index(max_ind,corr_matrix.shape)
        print([repeat,shift_yx,corr_matrix[shift_yx[0],shift_yx[1]]])
        plt.subplot().imshow(corr_matrix)
        plt.show()
        dy = round(sr_y/2)-shift_yx[0]
        dx = round(sr_x/2)-shift_yx[1]    

        # shift the x,y according to what it is found in the above step, and finding the best correlation along z
        n=0
        corr_array = []
        layer_array = []
        for ventral_layer in ventral_stack:
            ventral_image = ventral_layer.asarray()
            [ventral_image,dorsal_image] = matchImageSize(ventral_image,dorsal_first_image)
            [ventral_image,dorsal_image] = shiftImage(ventral_image,dorsal_image,dx,dy)
            corr = pearsonCorrelation(ventral_image,dorsal_image)
            corr_array.append(corr)
            layer_array.append(z_layer-round(sr_z/2)+n)
            n=n+1    
        corr_array = np.asarray(corr_array)
        layer_array = np.asarray(layer_array)
        max_ind = np.argmax(corr_array)
        next_layer = layer_array[max_ind]
        print([repeat,layer_array[max_ind],corr_array[max_ind]])
        ventral_image = ventral_stack[max_ind].asarray()
        repeat = repeat+1
    
    [shift_ventral,shift_dorsal] = shiftImage(ventral_image,dorsal_image,dy,dx)
    TFF.imwrite("ventral_shift.tif",shift_ventral)
    TFF.imwrite("dorsal_shift.tif",shift_dorsal)

os.chdir("E:\DV_fusion")
Xcorrelation("ventral.tif","dorsal.tif",1753,-30,30,40)