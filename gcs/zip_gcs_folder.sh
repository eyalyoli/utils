#!/bin/bash

# Check if GCS path argument is provided
if [ $# -eq 0 ]; then
    echo "Error: Please provide a GCS path as argument"
    echo "Usage: $0 gs://your-bucket/path/"
    exit 1
fi

GCS_PATH=$1
TMP_DIR="/tmp/gcs_download"

# Extract and sanitize path components
SUBDIR_PATH="${GCS_PATH#gs://*/}"  # Remove bucket name
SUBDIR_PATH="${SUBDIR_PATH%/}"     # Remove trailing slash
SANITIZED_NAME=$(echo "$SUBDIR_PATH" | sed 's#/#_#g')
OUTPUT_GZIP="$HOME/job_posts_raw_zips/${SANITIZED_NAME}.tar.gz"

# Create temporary directory
mkdir -p "$TMP_DIR"

# Download files using gsutil with multithreading
echo "Downloading files from $GCS_PATH..."
gsutil -m cp -r "${GCS_PATH%/}/*" "$TMP_DIR"

# Compress downloaded files to gzip
echo "Compressing files to $OUTPUT_GZIP..."
tar -czf "$OUTPUT_GZIP" -C "$TMP_DIR" .

# Cleanup temporary files
echo "Cleaning up temporary files..."
rm -rf "$TMP_DIR"

echo "Operation completed successfully! Output: $OUTPUT_GZIP"
