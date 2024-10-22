#!/bin/bash

################################################################################
# Script to move files from a source directory to a destination directory
# Author: solen
# Works with ERC content with All Stages included in one directory
################################################################################

# Source directory where the files are located
SOURCE_DIR="/mnt/rust/data/torrents/sport/motor"    # Replace with the actual source directory
DEST_DIR="/mnt/rust/data/media/motorsport/ERC 2024" # Destination directory
USER="apps"
GROUP="apps"
SEASON_YEAR="2024"
DRY_RUN=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
    --dry-run) DRY_RUN=true ;;
    *)
        echo "Unknown parameter passed: $1"
        exit 1
        ;;
    esac
    shift
done

# Function to zero-pad episode numbers and treat them as base-10 (avoid octal)
pad_number() {
    # Strip any leading zeros before passing to printf
    number=$(echo "$1" | sed 's/^0*//')
    printf "%02d" "$number"
}

# Recursively search for all .mp4 files in the source directory and its subdirectories
find "$SOURCE_DIR" -type f \( -name "*.mp4" -o -name "*.mkv" \) | while read -r file; do
    # Check if the file path contains "ERC 2024" to avoid touching unrelated files
    if [[ "$file" == *"ERC $SEASON_YEAR"* ]]; then
        if [[ -f "$file" ]]; then
            # Extract the round (e.g., "Round04"), rally name (e.g., "Rally Estonia"), and stage (e.g., "SS01" or "Qualifying")
            if [[ "$file" =~ ERC\ 2024\ (Round[0-9]+)\ Rally\ ([a-zA-Z\ ]+)\ (SS[0-9]+(-SS[0-9]+)?|Qualifying) ]]; then
                round="${BASH_REMATCH[1]}"
                rally="${BASH_REMATCH[2]}"
                stage="${BASH_REMATCH[3]}"  

                # Set episode number
                if [[ "$stage" == "Qualifying" ]]; then
                    episode="00"
                elif [[ "$stage" =~ SS([0-9]+)-SS([0-9]+) ]]; then
                    # For combined stages, use the first stage number
                    episode="${BASH_REMATCH[1]}"
                else
                    episode="${stage#SS}" # Remove "SS" prefix
                fi
            else
                echo "Unable to extract round, rally, and stage from filename: $file"
                continue
            fi
            # Convert rally name to lowercase for case-insensitive matching
            rally_lower=$(echo "$rally" | tr '[:upper:]' '[:lower:]')

            # Find the season directory (case-insensitive search) that contains the rally name
            season_dir=$(find "$DEST_DIR" -type d -iname "*${rally_lower}*" -print -quit)

            if [[ -z "$season_dir" ]]; then
                # If the season directory does not exist, create it
                season_number=$(echo "$round" | sed 's/Round//')
                season_dir="$DEST_DIR/${season_number} $rally"
                if [ "$DRY_RUN" = true ]; then
                    echo "[DRY RUN] Would create season directory: $season_dir"
                else
                    mkdir -p "$season_dir"
                    echo "Created season directory: $season_dir"
                fi
            else
                # Extract the season number (e.g., "08" from "08 Estonia")
                season_number=$(basename "$season_dir" | cut -d ' ' -f 1)
            fi

            # Prepare the destination filename and path
            file_extension="${file##*.}"
            new_filename="${season_number}x$(pad_number "$episode").${file_extension}"
            destination_path="$season_dir/$new_filename"

            # Check if the file already exists in the destination
            if [ ! -f "$destination_path" ]; then
                if [ "$DRY_RUN" = true ]; then
                    echo "[DRY RUN] Would create hardlink: $file -> $destination_path"
                else
                    # Create a hardlink to the file in the destination
                    ln "$file" "$destination_path"

                    # Set the correct ownership
                    chown "$USER:$GROUP" "$destination_path"

                    echo "Created hardlink and set ownership: $file -> $destination_path"
                fi
            else
                echo "File already exists, skipping: $destination_path"
            fi
        else
            echo "Season directory for '$rally' not found, skipping file: $file"
        fi
    else
        echo "Skipping unrelated file: $file"
    fi
done

# Modify the cleanup section
if [ "$DRY_RUN" = true ]; then
    echo "[DRY RUN] Would clean up empty directories in: $DEST_DIR"
else
    # Clean up any empty directories in the destination
    find "$DEST_DIR" -type d -empty -delete
fi
