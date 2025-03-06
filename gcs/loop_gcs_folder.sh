#!/bin/bash

# Check if GCS path argument is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a GCS directory path as argument"
    echo "Usage: $0 gs://your-bucket/parent-path/"
    exit 1
fi

PARENT_PATH="$1"
SCRIPT_PATH="./zip_gcs_folder.sh"  # Path to your original script

# Get list of direct sub-directories (non-recursive)
IFS=$'\n'  # Handle directories with spaces
SUB_DIRS=$(gsutil ls -d "${PARENT_PATH}/*" 2>/dev/null)

if [ -z "$SUB_DIRS" ]; then
    echo "No sub-directories found in $PARENT_PATH"
    exit 0
fi

echo "Found sub-directories:"
echo "$SUB_DIRS"

# Process each sub-directory
for subdir in $SUB_DIRS; do
    echo "Processing directory: $subdir"
    "$SCRIPT_PATH" "$subdir"
done

echo "Completed processing all sub-directories"
