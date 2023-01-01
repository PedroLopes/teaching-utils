find . -name '*.zip' -exec sh -c 'unzip -d "${1%.*}" "$1"' _ {} \;
read -p "Are you sure? " -n 1 -r
echo    # (optional) move to a new line
if [[ $REPLY =~ ^[Yy]$ ]]
then
    rm *.zip
fi
