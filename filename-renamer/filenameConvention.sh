output=$(exec python filenameConvention.py "$1" "$2")
mv "$1" "$output"
