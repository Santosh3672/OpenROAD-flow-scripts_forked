#!/usr/bin/env python3
import re
import sys
import gzip
import argparse  # argument parsing
import os

parser = argparse.ArgumentParser(
    description='Replaces occurrences of cells in def or verilog files')
parser.add_argument('--patterns', '-p', required=True,
                    help='List of search patterns')
parser.add_argument('--inputFile', '-i', required=True,
                    help='Input File')
parser.add_argument('--outputFile', '-o', required=True,
                    help='Output File')
args = parser.parse_args()


if os.path.exists(args.outputFile):
    os.remove(args.outputFile)
    print("Deleted the existing file")
file = open(args.inputFile, 'r')
lines = file.readlines()
file.close()

#file = open(args.outputFile, 'w')
#for line in lines:
#    file.writelines(line)
#file.close()

patternList = args.patterns.replace('*','.*').split()
print(patternList)
pattern = r"(^\s*cell\s*\(\s*([\"]*"+"[\"]*|[\"]*".join(patternList)+"[\"]*)\)\s*\{)"
print(pattern)
for idx in range(len(lines)):

    matchh = re.search(pattern, lines[idx])
    if(matchh):
        #print(lines[idx])
        if(lines[idx + 1][0:20]) == "    dont_use : true;":
            lines[idx + 1] = "    dont_use : false;\n"
            #print('**')
        #print('***' + lines[idx + 1][-1] + '***')

file = open(args.outputFile, 'w')
for line in lines:
    file.writelines(line)
file.close()



