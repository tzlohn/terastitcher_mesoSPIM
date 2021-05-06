import shutil
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

src_file = filedialog.askopenfilename(title = "select source file")
dst_dir = filedialog.askdirectory(title = "select destination folder")

shutil.copy(src_file,dst_dir)