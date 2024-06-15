#!/bin/bash

# Check if the folder path is provided as an argument
if [ -z "$1" ]; then
  echo "Usage: $0 <folder_path>"
  exit 1
fi

FOLDER_PATH=$1

# Check if the folder exists
if [ ! -d "$FOLDER_PATH" ]; then
  echo "Error: Folder $FOLDER_PATH does not exist."
  exit 1
fi

# Delete the contents of the folder
echo "Deleting contents of folder: $FOLDER_PATH"
rm -rf "${FOLDER_PATH:?}"/*

echo "Contents of $FOLDER_PATH have been deleted."