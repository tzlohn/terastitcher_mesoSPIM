import re,os,glob
import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
root.withdraw()

root_dir = filedialog.askdirectory()
os.chdir(root_dir)

all_raw_file = glob.glob("*.raw")
all_file = glob.glob("*")
for a_raw in all_raw_file:
    pattern = re.compile(r"(6.*)_nm(_\d+).raw")
    name = pattern.findall(a_raw)
    if name:
        print(a_raw)
        name_prefix = name[0][0]
        ori_SN = int(name[0][1][1:len(name[0][1])])
        pattern = re.compile(r"%s_nm(_\d+)?.raw(_meta.txt)?"%name_prefix)
        found_file = []
        SN = []
        file_type = []
        isSN = []
        for each_file in all_file:
            found = pattern.findall(each_file)
            if found:
                found_file.append(each_file)
                file_type.append(found[0][1])
                isSN.append(found[0][0])  
                if found[0][0]:
                    SN.append(int(found[0][0][1:len(found[0][0])]))   
        if len(SN) == 2:    
            for idx,a_file in enumerate(found_file):
                if not isSN[idx]:
                    if SN[0] == SN[1]:
                        if SN[0] % 2 == 0:
                            new_SN =SN[0]+1
                        else:
                            new_SN = SN[0]-1
                        new_SN = str(new_SN)
                        new_SN = "_"+"0"*(6-len(new_SN))+new_SN
                        #print(" %s\n %s"%(a_file,new_name))
                    else:
                        if file_type[idx] != "":
                            new_SN = name[0][1]
                        else:
                            ori_idx = SN.index(ori_SN)
                            if ori_idx == 0:
                                new_SN = SN[1]
                            elif ori_idx == 1:
                                new_SN = SN[0]
                            new_SN = str(new_SN)
                            new_SN = "_"+"0"*(6-len(new_SN))+new_SN    
                    new_name = name_prefix+"_nm"+new_SN+".raw"+file_type[idx]
                    print(" %s"%(new_name))
                    os.rename(a_file,new_name)
                else:
                    print(" %s"%(a_file))

        elif len(SN) == 3:
            print("=========found one=============\n%s"%a_raw)
            pass



            