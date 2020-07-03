import tiffile as TFF
import tkinter as tk
from tkinter import filedialog
import os,time

root = tk.Tk()
root.withdraw()

folderpath = filedialog.askdirectory(title = "select the folder containing 3D tiffs for both sides")
os.chdir(folderpath)
filename = filedialog.askopenfilename(title = "select the ventral image")
new_file_name = "ventral.tif"

tif = TFF.TiffFile(filename)
z_layers = len(tif.pages)

t_start = time.time()
for n in range(0,z_layers):
    an_image = TFF.imread(filename, key = n)
    TFF.imwrite(new_file_name, an_image, append = True, bigtiff = True)
t_end = time.time()
print("%d"%(t_end-t_start))