#!/usr/bin/env python3
import re
import sys
import gzip
import argparse  # argument parsing
import os

parser = argparse.ArgumentParser(
    description='Replaces occurrences of cells in def or verilog files')
parser.add_argument('--log_file', '-l', required=True,
        help='Log file of ECO task1 containing timing report: ECO will be performed based on those reports')
parser.add_argument('--verilog_file', '-v', required=True,
                    help='Input verilog File that needs to be changed')
parser.add_argument('--def_file', '-d', required=True,
                    help='Input DEF File that needs to be changed')
parser.add_argument('--result_dir', '-r', required=True,
                    help='Location where the DEF and Verilog files would be saved')

args = parser.parse_args()

L_R_delay_redn = 0.15
SL_L_delay_redn = 0.12
SL_R_delay_redn = L_R_delay_redn + SL_L_delay_redn

log = args.log_file
file = open(log,'r')
lines = file.readlines()
file.close()
timing_info_idx = []
for idx in range(len(lines)):
    if lines[idx] == '************************\n':
        if lines[idx + 1] == lines[idx]:
            timing_info_idx.append(idx)

start = timing_info_idx[0] + 2
stop  = timing_info_idx[1] - 2
tim_path_idx = []
end_data_path = []
for idx in range(start, stop):
    if(lines[idx][0:5]) == "-----":
        tim_path_idx.append(idx)
    if(lines[idx] == '\n'):
        if(len(tim_path_idx)%3 == 1):
            end_data_path.append(idx)

num_paths = int(len(tim_path_idx)/3)
print("Number of timing paths in Eco log files = " + str(int(len(tim_path_idx)/3)))
print(end_data_path)
#data_path = []
print('*****')
replace_list = []
for idx in range(num_paths):
    print("Starting for paths :" + str(idx))
    data_path = []
    slack = float(lines[tim_path_idx[3*idx + 2] + 1].split()[0])
    print("Slack from the report:" + str(slack))    
    data_arr_time = lines[tim_path_idx[3*idx + 1] + 2].split()[0]
    for dp in range(tim_path_idx[3*idx]+1,end_data_path[idx]-1):
        if (lines[dp].split()[2] == '^' or lines[dp].split()[2] == 'v'):
            delay = float(lines[dp].split()[0])
            cell = lines[dp].split()[3].split('/')[0]
            gate = lines[dp].split()[-1][1:-1]
            #print(gate[-2:])
            if (gate[-2:] == "_L" or gate[-2:] == "_R" or gate[-3:] == "_SL"):
                data_path.append([delay, cell, gate])
    data_path.sort(reverse = True,key = lambda x: x[0])
   


    # Check updated slack with already replaced cells
    replace_cell = [i[0] for i in replace_list]    
    for data in data_path:
        #print(data)
        #replace_cell = [i[0] for i in replace_list]
        if data[1] in replace_cell:
            #print('**********')
            replace_info = replace_list[replace_cell.index(data[1])]
            if (replace_info[1][-2:] == '_L' and replace_info[2][-2:] == '_R'):
                slack = slack + data[0]*L_R_delay_redn
            if (replace_info[1][-3:] == '_SL' and replace_info[2][-2:] == '_L'):
                slack = slack + data[0]*SL_L_delay_redn
            if (replace_info[1][-3:] == '_SL' and replace_info[2][-2:] == '_R'):
                slack = slack + data[0]*SL_R_delay_redn

                #print(slack)
    print("Slack after recalculating delay from ECOs of other paths:"+ str(slack))
    if slack < 0:
        for data in data_path:
            if data[1] in replace_cell:
                pass
            else:
                if(data[2][-2:] == '_R' and slack < 10):
                    replace_list.append([data[1],data[2][0:-2]+'_L',data[2]])
                    slack = slack + data[0]*L_R_delay_redn
                    #print(slack)
        if slack < 0:
            # If all the cells in datapath are LVT and timing is not met this loop will convert LVT to SLVT cells
            print("Using SLVT cells in design")
            for data in data_path:
                if data[2][-2:] == '_L' and slack < 3:
                    #print("Slack before resizing:" + str(slack))
                    if data[1] not in replace_cell:
                        #print('*#$%@')                        
                        slack = slack + data[0]*SL_L_delay_redn
                        replace_list.append([data[1],data[2][0:-2]+'_SL',data[2]])
                        print(replace_list[-1])
                    else:
                        replace_info = replace_list[replace_cell.index(data[1])]
                        if (replace_info[1][-2:] == '_L'):
                            #print('*#$%@')
                            slack = slack + data[0]*SL_L_delay_redn
                            replace_list[replace_cell.index(data[1])][1] = replace_list[replace_cell.index(data[1])][1][0:-2] + '_SL'
                            print(replace_list[replace_cell.index(data[1])])
                    #print("Slack after resizing:" + str(slack))
                            
                        


    print("Slack after performing ECO on this path:"+ str(slack))
    print("List of replacement suggested by the tool:")
    print(replace_list)
    print('**********')

print("End of ECO, cell change reccomendation:")
print("Name of cell: New cell :               Old cell")
for rep in replace_list:
    print(rep[0] + '      | ' + rep[1] + '      ' + rep[2])
# End of ECO

print("Incorporating those changes in def and verilog file")
v_file = open(args.verilog_file,'r')

v_lines = v_file.readlines()
v_file.close()
iid = 0
replace_cell = [i[0] for i in replace_list]    

for vline in v_lines:
    if len(vline.split()) >= 3:
        if vline.split()[1] in replace_cell:
            #print(vline)
            new_cell = replace_list[replace_cell.index(vline.split()[1])][1]
            new_line = ' ' + new_cell + ' ' + v_lines[iid].split()[1] + v_lines[iid].split(v_lines[iid].split()[1])[1]
            #print(new_line)
            v_lines[iid] = new_line
    iid = iid + 1
v_file_o = open(args.result_dir + '/7_eco.v','w')

for vline in v_lines:
    v_file_o.writelines(vline)
v_file_o.close()


replace_cell.sort()
print(replace_cell)
print('*******')
def_file = open(args.def_file,'r')
def_lines = def_file.readlines()
def_file.close()
#linee = def_lines[33819]
#for cell in replace_list:
#    if cell[0] + ' ' + cell[2] in linee:
#        print("***")
iid = 0
for defline in def_lines:
    for cell in replace_list:
        if cell[0] + ' ' + cell[2] in defline:
            splitted = defline.split(cell[0] + ' ' + cell[2])
            def_lines[iid] = splitted[0] + cell[0] + ' ' + cell[1] + splitted[1]

    iid = iid + 1

def_file_o = open(args.result_dir + '/7_eco.def','w')
for defline in def_lines:
    def_file_o.writelines(defline)
def_file_o.close()

