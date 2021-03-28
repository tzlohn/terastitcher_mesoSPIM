from multiprocessing import Process, Queue
from multiprocessing.shared_memory import SharedMemory
import multiprocessing as mp
import tkinter as tk
from tkinter import filedialog
import tifffile as TFF
import glob,os,time
import numpy as np
from psutil import virtual_memory

def load(q_load,q_comb,layerNo):
    # layerNo: the number in the height axis used to be load
    all_temp_tif = glob.glob("temp*.tif")
    request_count = dict()
    shm_list = list()
    shared_img_list = list()
    core_no = mp.cpu_count()-2

    for n in range(core_no):
        shm_list.append(SharedMemory(create = True, size = 2*layerNo*5*9261))
        shared_img_list.append(np.ndarray(shape = (layerNo,9261,5),dtype = "uint16",buffer = shm_list[n].buf))

    while True: #while True runs the following loop infinitely, until some command in the loop raise break
        if not q_load.empty():
            request_info = q_load.get(True)
            tif_name = request_info[0]
            layer = request_info[1] # starting layer of the trunk from the comb
            if not tif_name in request_count:
                request_count[tif_name] = 1
                img = TFF.imread(tif_name)
                for n in range(core_no):
                    shared_img_list[n]=np.ndarray(shape = (layerNo,img.shape[1],img.shape[2]), dtype = img.dtype, buffer = shm_list[n].buf)
                    np.copyto(shared_img_list[n],img[layer+n*layerNo:layer+(n+1)*layerNo,:,:])    
                for idx,a_queue in enumerate(q_comb):
                    a_queue.put([tif_name,shm_list[idx].name,shared_img_list[idx].shape])            
            else:
                request_count[tif_name] = request_count[tif_name]+1
            
            if tif_name == all_temp_tif[-1] and request_count[tif_name] == core_no:
                break
 

def combine(q_load,q_comb,n,layerSN,x_temp_layers):
    
    temptif = glob.glob("temp*.tif")
    sub_trunk = np.zeros(shape = (x_temp_layers,9261,2749),dtype = "uint16")

    t_start = time.time()
    for idx,a_temp in enumerate(temptif):
        if n==0:
            onetemp_start=time.time()
        #t_start = time.time()
        #img = TFF.imread(a_temp,key = range(10000))
        #t_end = time.time()
        #print("time for layer_%d to load %s : %.3f"%(layer,a_temp,t_end-t_start))
        
        #t_start = time.time()
        q_load.put([a_temp,layerSN])
        name_and_tif= q_comb.get(True)
        shm = SharedMemory(name_and_tif[1])
        tif = np.ndarray(shape = name_and_tif[2], dtype = "uint16", buffer = shm.buf)

        sub_trunk[:,:,idx*5:(idx+1)*5] = tif
        if n==0:
            onetemp_end=time.time()
            print("     Used %.3f seconds for %s"%(onetemp_end-onetemp_start,a_temp))
        #print(tif.shape,layer,name_and_tif[0])
        #t_end = time.time()
        #print("time for layer_%d to get %s : %.3f"%(layer,a_temp,t_end-t_start))
        """
        mem = virtual_memory()
        print("before killing in combine, %d MB"%(mem.free/1000000))
        shm.close()
        del(tif)
        mem = virtual_memory()
        print(" after killing in combine, %d MB"%(mem.free/1000000))        
        shm.unlink()
        """
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
            q_comb.append(Queue())
        q_load = Queue()

        Load_process = Process(target=load, args=(q_load,q_comb,x_temp_layers))    
        comb_process = list()
        for n in range(core_no):
            comb_process.append(Process(target=combine, args=(q_load,q_comb[n],n,trunkSN,x_temp_layers)))

        print("start doing")
        for n in range(core_no):
            comb_process[n].start()
        Load_process.start() 

        for n in range(core_no):
            comb_process[n].join() 
        Load_process.join()

    print("finished")