#!/bin/bash

# Source directory where the files are located
SOURCE_DIR="/mnt/rust/data/torrents/sport/motor"  # Replace with the actual source directory
DEST_DIR="/mnt/rust/data/media/motorsport/ERC 2024"  # Destination directory
USER="apps"
GROUP="apps"
SEASON_YEAR="2024"
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
  # Strip any leading zeros before passing to printf
  number=$(echo "$1" | sed 's/^0*//')
  printf "%02d" "$number"
}

# Recursively search for all .mkv files in the source directory and its subdirectories
find "$SOURCE_DIR" -type f -name "*.mkv" | while read -r file; do
  # Check if the file path contains "erc" to avoid touching unrelated files
  if [[ "$file" == *"erc"* ]]; then
    if [[ -f "$file" ]]; then
      # Extract the season (e.g., "silesia") and episode number (e.g., "01")
      if [[ "$file" =~ erc\.fia\.european\.rally\.championship\.$SEASON_YEAR\.([a-zA-Z]+)\.ss([0-9]{2}) ]]; then
        season="${BASH_REMATCH[1]}"
        episode="${BASH_REMATCH[2]}"
      else
        echo "Unable to extract season and episode from filename: $file"
        continue
      fi

      # Convert season name to lowercase for case-insensitive matching
      season_lower=$(echo "$season" | tr '[:upper:]' '[:lower:]')

      # Find the season directory (case-insensitive search) that contains the season name
      season_dir=$(find "$DEST_DIR" -type d -iname "*${season_lower}*" -print -quit)

      if [[ -n "$season_dir" ]]; then
        # Extract the season number (e.g., "08" from "08 Silesia")
        season_number=$(basename "$season_dir" | cut -d ' ' -f 1)

        # Prepare the destination filename and path
        new_filename="${season_number}x$(pad_number "$episode").mkv"
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
        echo "Season directory for '$season' not found, skipping file: $file"
      fi
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