import glob,os,shutil
import tkinter as tk
from tkinter import filedialog
from shutil import copyfile

root = tk.Tk()
root.withdraw()

dir_1 = filedialog.askdirectory()
dir_2 = filedialog.askdirectory()
if dir_1 == dir_2:
    exit()
os.chdir(dir_1)
os.mkdir("temp")
all_raw_1 = glob.glob("*.raw")
os.chdir(dir_2)
all_raw_2 = glob.glob("*.raw")
for a_raw in all_raw_2:
    if a_raw in all_raw_1:
        os.chdir(dir_2)
        file_size_2 = os.stat(a_raw).st_size
        os.chdir(dir_1)
        file_size_1 = os.stat(a_raw).st_size
        if file_size_1 > file_size_2:
            os.chdir(dir_2)
            os.remove(a_raw)
            os.chdir(dir_1)
            shutil.move(a_raw,dir_2)
        if file_size_1 == file_size_2:
            os.chdir(dir_1)
            print(a_raw)
            shutil.move(a_raw,"temp")
            #os.remove(a_raw)    
            #print("%s,%d"%(a_raw,file_size_2))