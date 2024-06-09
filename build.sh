#!/bin/bash

SOURCES=("ptest.py")
MISSING_FILES=false

for SOURCE in "${SOURCES[@]}"; do
    if [ ! -e "$SOURCE" ]; then
        echo "ERROR: Source file '$SOURCE' not found in the current directory."
        MISSING_FILE=true
    fi
done

if [ "$MISSING_FILE" = true ]; then
    exit 1
fi

for SOURCE in "${SOURCES[@]}"; do
    DESTINATION="/usr/local/bin/${SOURCE%%.*}"
    if [ -e "$DESTINATION" ]; then
        while true; do

            read -p "$DESTINATION already exists. Do you want to overwrite it? [y/N]" response

            case $response in 
	            [yY] )
                    sudo cp $SOURCE $DESTINATION
                    echo "Successful installation. You can now run '${SOURCE%%.*}' from anywhere"
		            break;;
	            [nN] )
                    echo "Installation aborted."
		            exit;;
	            * )
            esac
        done

    else
        sudo cp $SOURCE $DESTINATION
        echo "Successful installation. You can now run '${SOURCE%%.*}' from anywhere"
    fi
done
