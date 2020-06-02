import re,os,tkinter,glob
from tkinter import filedialog

root = tkinter.Tk()
root.withdraw()

working_folder = filedialog.askdirectory()
os.chdir(working_folder)

filelist = glob.glob('*.tif')

pattern = re.compile(r"image_(\d+).tif")
for a_file in filelist:
    index = pattern.findall(a_file)
    index = index[0]
    add_len = 5 - len(index)
    while len(index) < 5:
        index = "0"+index
    new_name = "image_"+index+".tif"
    os.rename(a_file,new_name)
