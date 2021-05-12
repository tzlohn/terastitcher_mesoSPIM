from mit import rename_stitched_2D
import tkinter as tk
from tkinter import filedialog
import shutil,os,glob

root = tk.Tk()
root.withdraw()

#root_dir = filedialog.askdirectory()
#rename_stitched_2D(root_dir,0)

source_dir = filedialog.askdirectory()
dest_dir = filedialog.askdirectory()
os.chdir(source_dir)
all_tif = glob.glob("*.tif")
for a_tif in all_tif:
    shutil.move(a_tif,dest_dir)

