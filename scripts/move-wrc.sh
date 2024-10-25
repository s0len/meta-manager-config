#!/bin/bash

################################################################################
# Script to move files from a source directory to a destination directory
# Author: solen
# Works with WRC content with All Stages included in one directory
################################################################################

SEASON_YEAR="2024"
SOURCE_DIR="/mnt/rust/data/torrents/sport/motor"  # Replace with the actual source directory
DEST_DIR="/mnt/rust/data/media/motorsport/WRC $SEASON_YEAR"  # Destination directory
USER="apps"
GROUP="apps"
DRY_RUN=false

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dry-run) DRY_RUN=true ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# Function to zero-pad episode numbers and treat them as base-10 (avoid octal)
pad_number() {
  # Ensure the input is numeric before padding
  if [[ "$1" =~ ^[0-9]+$ ]]; then
    # Strip any leading zeros before passing to printf
    number=$(echo "$1" | sed 's/^0*//')
    printf "%02d" "$number"
  else
    echo "$1"  # Return the input as-is if it's not numeric
  fi
}

# Recursively search for all .mp4 and .mkv files in the source directory and its subdirectories
find "$SOURCE_DIR" -type f \( -name "*.mp4" -o -name "*.mkv" \) | while read -r file; do
  # Check if the file path contains "WRC 2024" to avoid touching unrelated files
  if [[ "$file" =~ WRC[.\ ]$SEASON_YEAR ]]; then
    if [[ -f "$file" ]]; then
      # Extract the round (e.g., "Round04"), rally name (e.g., "Rally Estonia"), and stage (e.g., "SS01" or "Highlights")
      if [[ "$file" =~ WRC[.\ ]$SEASON_YEAR[.\ ](Round[0-9]+)[.\ ](.+?)[.\ ](SS[0-9]+(-SS[0-9]+)?|[Hh]ighlights|[Ee]vent\.[Hh]ighlights|Highlights) ]]; then
        round="${BASH_REMATCH[1]}"
        full_rally_name="${BASH_REMATCH[2]}"
        stage="${BASH_REMATCH[3]}"  

        # Extract just the rally name without extra information
        rally=$(echo "$full_rally_name" | sed -E 's/ All Stages.*$//' | sed -E 's/\.Event\.([Hh]ighlights).*$//' | tr '.' ' ')

        # Extract the round number and pad it to two digits
        round_number=$(echo "$round" | sed 's/Round//')
        padded_round_number=$(printf "%02d" "${round_number#0}")

        # Set episode number
        if [[ "$stage" =~ [Hh]ighlights|[Ee]vent\.[Hh]ighlights ]]; then
          episode="22"
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

      # Create the season directory
      season_dir="$DEST_DIR/$padded_round_number $rally"
      if [ "$DRY_RUN" = true ]; then
        echo "[DRY RUN] Would create season directory: $season_dir"
      else
        mkdir -p "$season_dir"
        echo "Created season directory: $season_dir"
      fi

      # Prepare the destination filename and path
      file_extension="${file##*.}"
      new_filename="${padded_round_number}x$(pad_number "$episode").${file_extension}"
      destination_path="$season_dir/$new_filename"  

      # Check if the file already exists in the destination
      if [ ! -f "$destination_path" ]; then
        if [ "$DRY_RUN" = true ]; then
          echo "[DRY RUN] Would create hardlink: $file -> $destination_path"
        else
          # Create a hardlink to the file in the destination
          ln "$file" "$destination_path"
          
          # Set the correct ownership
          chown -R "$USER:$GROUP" "$DEST_DIR"
          
          echo "Created hardlink and set ownership: $file -> $destination_path"
        fi
      else
        echo "File already exists, skipping: $destination_path"
      fi
    else
      echo "File not found, skipping: $file"
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