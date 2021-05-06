import shutil,os,glob
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

src_dir = filedialog.askdirectory(title = "select source directory")
dst_dir = filedialog.askdirectory(title = "select destination folder")

os.chdir(src_dir)
all_file = glob.glob("*")
for a_file in all_file:
    shutil.copy(a_file,dst_dir)