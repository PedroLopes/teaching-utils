import argparse
import os
import sys
import datetime
import time

today=time.localtime().tm_wday
day=time.localtime().tm_mday
hour=time.localtime().tm_hour
month=time.localtime().tm_mon


def main(argv):
  if len(argv) == 1: # not enough, where is the file?
    #print("SORRY: Where is the file you wanna change?")
    exit()
  filename = str(argv[1]).replace('-', "_")
  #print ("1:"+filename)
  l = filename.split(".")
  filetype = "." + str(l[len(l)-1])
  filename =  filename.split(" ")[0]
  #print ("2:"+filename)
  if len(argv)==3: #we have >python filename_to_change "name to suffix" = 3
    filename = filename + "_" + argv[2] + filetype
    #print ("3:"+filename)
  print filename

if __name__ == '__main__':
  main(sys.argv)
