import argparse
import os
import sys
import datetime
import time


def main(argv):
  if len(argv) < 3: # not enough, where is the file?
    print("SORRY: Where is the file you wanna change + What to suffix? EXAMPLE: arg1=2012-02-02 12.12am.jpeg and arg2=brainstorming")
    exit()
  filename = str(argv[1]).replace('-', "_")
  l = filename.split(".")
  filetype = "." + str(l[len(l)-1])
  filename =  filename.split(" ")[0]
  if len(argv)==3: #we have >python filename_to_change "name to suffix" = 3
    filename = filename + "_" + argv[2] + filetype
  print filename

if __name__ == '__main__':
  main(sys.argv)
