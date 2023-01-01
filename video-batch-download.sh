#!/bin/bash

# Information / README
#  This script batch downloads a list of youtube URLs (or other videos, as long as supported by your youtube-dl). 
#  The source_file should be a text file that only contains video URLs (one per line)
#   
# How to use this (via command line, see command example below)
#  >  video-batch-download.sh source_file 

input=$1
while IFS= read -r line
do
  echo "getting:"
  echo "$line"
  youtube-dl --format mp4 "$line"
done < "$input"
