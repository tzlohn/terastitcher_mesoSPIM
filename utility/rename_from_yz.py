from tkinter import filedialog
import os,glob,re

dirs = filedialog.askdirectory()
os.chdir(dirs)

all_tif = glob.glob("*.tif")
pattern = re.compile(r"C01_(\d+).tif")
for n,a_tif in enumerate(all_tif):
    #SN = pattern.findall(a_tif)
    #SN = (len(str(len(all_tif)))-len(str(n)))*"0"+str(n)
    SN = str(n+13460)
    #new_name = "ventral_"+SN[0]+".tif"
    new_name = "C01_Z"+SN+".tif"
    #print(new_name)
    os.rename(a_tif,new_name)
