from multiprocessing import Process, Queue, Pipe
from multiprocessing.shared_memory import SharedMemory
import multiprocessing as mp
import tkinter as tk
from tkinter import filedialog
import tifffile as TFF
import glob,os,time
import numpy as np
from psutil import virtual_memory

def load(q_comb,layerNo,layerSN):
    # layerNo: the number in the height axis used to be load
    all_temp_tif = glob.glob("temp*.tif")
    shm_list = list()
    shared_img_list = list()
    core_no = mp.cpu_count()-2

    for n in range(core_no):
        shm_list.append(SharedMemory(create = True, size = 2*layerNo*5*9261))
        shared_img_list.append(np.ndarray(shape = (layerNo,9261,5),dtype = "uint16",buffer = shm_list[n].buf))

    for idx,tif_name in enumerate(all_temp_tif):
        img = TFF.imread(tif_name, key = range(layerSN,layerSN+core_no*layerNo))
        for n in range(core_no):
            shared_img_list[n]=np.ndarray(shape = (layerNo,img.shape[1],img.shape[2]), dtype = img.dtype, buffer = shm_list[n].buf)
            np.copyto(shared_img_list[n],img[n*layerNo:(n+1)*layerNo,:,:])    
        for idx,a_pipe in enumerate(q_comb):
            a_pipe[0].send([tif_name,shm_list[idx].name,shared_img_list[idx].shape,idx])
          
def combine(q_comb,n,layerSN,x_temp_layers):
    
    temptif = glob.glob("temp*.tif")
    sub_trunk = np.zeros(shape = (x_temp_layers,9261,2749),dtype = "uint16")
    tif_name = str() 
    t_start = time.time()
    while tif_name != temptif[-1]:  #while True runs the following loop infinitely, until some command in the loop raise break
        if n==0:
            onetemp_start=time.time()
        #name_and_tif= q_comb.get(True)
        name_and_tif= q_comb[1].recv()
        shm = SharedMemory(name_and_tif[1])
        tif = np.ndarray(shape = name_and_tif[2], dtype = "uint16", buffer = shm.buf)
        idx = name_and_tif[3]
        if (idx+1)*5 < 2749:
            sub_trunk[:,:,idx*5:(idx+1)*5] = tif
        else:
            sub_trunk[:,:,idx*5:2749] = tif    
        tif_name = name_and_tif[0]
        
        if n==0:
            onetemp_end=time.time()
            print("     Used %.3f seconds for %s"%(onetemp_end-onetemp_start,tif_name))

    t_end = time.time()    
    print("time for layer_%d to load all temptif: %.3f"%(layerSN,t_end-t_start))

    for m in range(x_temp_layers):
        str_m = str(layerSN+n*x_temp_layers+m)
        digit_diff = 5 - len(str_m)
        str_m = "0"*digit_diff + str_m
        img_name = "yz_" + str_m + ".tif"    
        TFF.imwrite(img_name, sub_trunk[m], bigtiff = True)

if __name__=='__main__':
    root = tk.Tk()
    root.withdraw()

    WorkingDirectory = filedialog.askdirectory()
    os.chdir(WorkingDirectory)

    core_no = mp.cpu_count()-2
    mem = virtual_memory()
    ram_use = mem.free*0.8/core_no

    temptifs = glob.glob("temp*.tif")
    BytesOnePage = os.stat(temptifs[0]).st_size
    x_temp_layers = int(round(ram_use/(2*2749*9261)))
    print(x_temp_layers)
    
    for trunkSN in range(0,27618,6*x_temp_layers):
        print("Processing trunk %d"%trunkSN)
        q_comb = list()
        for n in range(core_no):
            q_comb.append(Pipe())

        Load_process = Process(target=load, args=(q_comb,x_temp_layers,trunkSN))    
        comb_process = list()
        for n in range(core_no):
            comb_process.append(Process(target=combine, args=(q_comb[n],n,trunkSN,x_temp_layers)))

        print("start doing")
        for n in range(core_no):
            comb_process[n].start()
        Load_process.start() 

        for n in range(core_no):
            comb_process[n].join() 
        Load_process.join()

    print("finished")