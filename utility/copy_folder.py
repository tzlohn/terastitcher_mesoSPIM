import shutil,os
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

src_dir = filedialog.askdirectory(title = "select source directory")
dst_dir = filedialog.askdirectory(title = "select destination folder")

os.chdir(src_dir)
all_items = os.listdir(src_dir)
for an_item in all_items:
    if os.path.isdir(an_item):
        shutil.copytree(an_item,dst_dir,symlinks = False,ignore = None)
    else:
        shutil.copy(an_item,dst_dir)