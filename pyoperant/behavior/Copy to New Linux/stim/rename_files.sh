#!/bin/bash

for file in b*[0-9]*[a-zA-Z]*[0-9]*_*.wav; do
  # Extract the number after 'b'
  number="${file:1:1}"

  # Check if it's a number
  if [[ "$number" =~ ^[0-9]+$ ]]; then
    # Convert to integer for comparison (important!)
    number_int=$((number))

    if (( number_int > 4 )); then
      new_file="g${file:1}" # Replace 'b' with 'g'
    else
      new_file="z${file:1}" # Replace 'b' with 'z'
    fi

    mv "$file" "$new_file"
    echo "Renamed '$file' to '$new_file'" # Optional: Print what was changed
  fi
done
