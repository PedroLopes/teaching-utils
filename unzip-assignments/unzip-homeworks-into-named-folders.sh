for filename in *.zip; do
    filename_clean=${filename%%.zip}
    filename_only_name=${filename_clean##*- }
    unzip "$filename" -d "$filename_only_name";
done
