'''
This code is an accident. It was used to find out the bug for the Terasticher.
What is it doing is find out the perfect correlation of x column between original and stitched images 
'''

import numpy as np    
import tifffile as TFF 
import os,re
import tkinter as tk
import matplotlib.pyplot as plt 
from tkinter import filedialog

def dimwise_matrix_operation(mat,ax):
    mat_mean = np.mean(mat, axis = ax)
    mat_mean = np.matrix(mat_mean)
    identity_array = np.ones([mat.shape[ax],1])
    mat_mean = np.dot(identity_array,mat_mean)
    norm_mat = mat - mat_mean
    return norm_mat

root = tk.Tk()
root.withdraw()

#current_folder = filedialog.askdirectory()
test_image_name = filedialog.askopenfilename()
ventral_image_name = filedialog.askopenfilename()

pattern = re.compile(r'image_(\d+).tif')
layer_no = pattern.findall(test_image_name)
layer_no = int(layer_no[0])

with TFF.TiffFile(ventral_image_name) as ventral_file:
    standard_images = ventral_file.pages[layer_no-10:layer_no+10]

test_image = TFF.imread(test_image_name)

max_v_test = np.max(test_image)
max_ind = np.argmax(test_image)
max_ind_test_image = np.unravel_index(max_ind,test_image.shape)
print(max_v_test)
max_v = 0
n = 0
while max_v != max_v_test:
    standard_image = standard_images[n].asarray()
    max_v = np.max(standard_image)
    min_v = np.min(standard_image)
    n = n+1
    print(max_v)

max_ind = np.argmax(standard_image)
max_ind_standard_image = np.unravel_index(max_ind,standard_image.shape)

diff = max_ind_test_image[0] - max_ind_standard_image[0]
if diff > 0:
    filling_matrix = np.zeros([diff,standard_image.shape[1]], dtype = "uint16")
    standard_image = np.concatenate([filling_matrix,standard_image], axis = 0)
elif diff< 0:
    filling_matrix = np.zeros([abs(diff),test_image.shape[1]], dtype = "uint16")
    test_image = np.concatenate([filling_matrix,test_image], axis = 0)

norm_test_image = dimwise_matrix_operation(test_image,0)
norm_standard_image = dimwise_matrix_operation(standard_image,0)

test_std_array = np.std(test_image, axis = 0)
for n in range(test_std_array.shape[0]):
    if test_std_array[n] == 0:
        test_std_array[n] = 1e8
        print(n)
test_std_array = 1/test_std_array
test_std_array = np.asmatrix(test_std_array)
test_std_array = np.diagflat(test_std_array)

standard_std_array = np.std(standard_image, axis = 0)
for n in range(standard_std_array.shape[0]):
    if standard_std_array[n] == 0:
        standard_std_array[n] = 1e8
        print(n)
standard_std_array = 1/standard_std_array
standard_std_array = np.asmatrix(standard_std_array)
standard_std_array = np.diagflat(standard_std_array)

corr_matrix = np.dot(np.transpose(norm_test_image),norm_standard_image)/norm_standard_image.shape[0]
corr_matrix = np.dot(test_std_array, corr_matrix)
corr_matrix = np.dot(corr_matrix,standard_std_array)

for n in range(corr_matrix.shape[0]):
    one_row = corr_matrix[n,:]
    max_ind = np.argmax(one_row)
    print([max_ind,corr_matrix[n,max_ind]])