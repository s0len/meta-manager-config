#!/bin/bash

SEASON_YEAR="2024"
SOURCE_DIR="/mnt/rust/data/torrents/sport/motor"  # Replace with actual source directory
DEST_DIR="/mnt/rust/data/media/motorsport/MotoGP $SEASON_YEAR"  # Destination directory
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

# Function to zero-pad numbers
pad_number() {
  printf "%02d" "$1"
}

# Recursively search for all .mkv files in the source directory and its subdirectories
find "$SOURCE_DIR" -type f -name "*.mkv" | while read -r file; do
  # Check if the file path contains "MotoGP" to avoid touching unrelated files
  if [[ "$file" == *"MotoGP"* ]]; then
    if [[ -f "$file" ]]; then
      # Extract the round number and country
      if [[ "$file" =~ (Round([0-9]+)\.([A-Za-z\.]+)\.(Free\.Practice|Qualifying|Q1|Q2|Sprint|Race))|(Round[[:space:]]?([0-9]+)[[:space:]]([A-Za-z]+)[[:space:]](Free\.Practice|Qualifying|Q1|Q2|Sprint|Race)) ]]; then
        # If it matches the first pattern (with dots)
        if [[ -n "${BASH_REMATCH[1]}" ]]; then
          round="${BASH_REMATCH[2]}"
          country=$(echo "${BASH_REMATCH[3]}" | tr '.' ' ')
          event_type="${BASH_REMATCH[4]}"
        # If it matches the second pattern (with spaces)
        else
          round="${BASH_REMATCH[6]}"
          country="${BASH_REMATCH[7]}"
          event_type="${BASH_REMATCH[8]}"
        fi

        # Change Q1/Q2 to Qualifying 1/Qualifying 2 for specificity
        if [[ "$event_type" == "Q1" ]]; then
          event_type="Qualifying 1"
        elif [[ "$event_type" == "Q2" ]]; then
          event_type="Qualifying 2"
        fi
      else
        echo "Unable to extract round and country from filename: $file"
        continue
      fi

      # Determine the session type and episode number
      case "$event_type" in
        "Free.Practice")
          if [[ "$file" == *"Free.Practice.1"* ]]; then
            episode_number=1
            session_name="Free Practice 1"
          elif [[ "$file" == *"Free.Practice.2"* ]]; then
            episode_number=2
            session_name="Free Practice 2"
          fi
          ;;
        "Qualifying")
          if [[ "$file" == *"Qualifying.Q1"* ]]; then
            episode_number=3
            session_name="Qualifying 1"
          elif [[ "$file" == *"Qualifying.Q2"* ]]; then
            episode_number=4
            session_name="Qualifying 2"
          else
            episode_number=3
            session_name="Qualifying"
          fi
          ;;
        "Sprint")
          episode_number=5
          session_name="Sprint"
          ;;
        "Race")
          episode_number=6
          session_name="Race"
          ;;
        *)
          echo "Unknown session type, skipping file: $file"
          continue
          ;;
      esac

      # Prepare the season directory
      season_dir="$DEST_DIR/$(pad_number "$round") $country"

      # Create the season directory if it doesn't exist
      mkdir -p "$season_dir"

      # Prepare the destination filename and path
      new_filename="$(pad_number "$round")x$(pad_number "$episode_number") $session_name.mkv"
      destination_path="$season_dir/$new_filename"

      # Check if the file already exists in the destination
      if [ ! -f "$destination_path" ]; then
        if [ "$DRY_RUN" = true ]; then
          echo "[DRY RUN] Would create hardlink: $file -> $destination_path"
          echo "[DRY RUN] Would set ownership to $USER:$GROUP for $destination_path"
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
    fi
  else
    echo "Skipping unrelated file: $file"
  fi
done

# Clean up any empty directories in the destination
if [ "$DRY_RUN" = true ]; then
  echo "[DRY RUN] Would clean up empty directories in $DEST_DIR"
else
  find "$DEST_DIR" -type d -empty -delete
fi