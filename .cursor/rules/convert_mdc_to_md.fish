#!/usr/bin/env fish

# Script to copy .mdc files to .md files in a new directory
# Define source and destination directories
set SRC_DIR (pwd)
set DEST_DIR "$HOME/Downloads/mdc_to_md_converted"

# Ensure the destination directory exists
test -d $DEST_DIR; or mkdir -p $DEST_DIR; or begin
    echo "Error: Failed to create destination directory $DEST_DIR" >&2
    exit 1
end

# Find all .mdc files in the source directory
set files (find $SRC_DIR -name "*.mdc" -type f)
set file_count (count $files)

if test $file_count -eq 0
    echo "Error: No .mdc files found in $SRC_DIR" >&2
    exit 1
else
    echo "Found $file_count .mdc files to convert"
end

# Counter for successful copies
set success_count 0

# Loop through each file and copy with new extension
for f in $files
    set filename (basename $f .mdc)
    set dest_file "$DEST_DIR/$filename.md"
    
    # Copy the file with new extension
    cp $f $dest_file; or begin
        echo "Error: Failed to copy $f to $dest_file" >&2
        continue
    end
    
    # If successful, increment counter
    set success_count (math $success_count + 1)
    echo "Copied: $filename.mdc → $filename.md"
end

# Verify copy operations
if test $success_count -eq $file_count
    echo "Success: All $success_count files converted and saved to $DEST_DIR"
else
    echo "Warning: Only $success_count out of $file_count files were successfully converted" >&2
    exit 1
end

exit 0

