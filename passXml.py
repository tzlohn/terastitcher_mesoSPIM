import tkinter as tk
from tkinter import filedialog
import re,glob

root = tk.Tk()
root.withdraw()

working_folder = filedialog.askdirectory(title = "select the folder containing images to be stitched")
os.chdir(working_folder)
all_names = glob.glob("*.tif")

def find_position_in_name(name):
   
    pattern = re.compile(r"(.*)_nm")
    position_name = pattern.findall(name)
    position_name = position_name[0]
    position_name = position_name[0:len(position_name)-3]
    return position_name

xml_file = filedialog.askopenfilename(title = "select the xml file")
filename_dict = {}
with open(xml_file, "r") as xml:
    file_context_str = xml.readlines()
    pattern = re.compile(r"IMG_REGEX=[\"](.*)[\"]")
    for index,string in enumerate(file_context_str):
        img_name = pattern.findall(string)
        if img_name:
            filename_dict[index] = img_name[0]
            string.replace(img_name[0],"test.tif")
            print(string)

for line_ind in filename_dict:
    name_of_position = find_position_in_name(filename_dict[line_ind])
    n = -1
    img_name = ""
    pattern = re.compile(r"(%s)"%(name_of_position))
    while not img_name:
        n = n+1
        img_name = pattern.findall(all_names[n])
    file_context_str[line_ind] = file_context_str[line_ind].replace(filename_dict[line_ind],all_names[n])

with open(xml_file, "w") as xml:
    xml.writelines(file_context_str)


