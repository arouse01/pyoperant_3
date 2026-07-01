#!/bin/bash

input_file="go_nogo_interrupt_stimuli.json"  # Replace with your JSON file name
output_file="go_nogo_interrupt_stimuli.json"  # The resulting JSON file

# Use jq to process the JSON file and apply the renaming logic
jq 'walk(if type == "string" and test("^b[0-9]+.*\\.wav$") then
      if (. | capture("^b(?<num>[0-9]+)").num | tonumber) >= 5 then
        sub("^b(?<num>[0-9]+)"; "g\\(.num)")
      else
        sub("^b(?<num>[0-9]+)"; "z\\(.num)")
      end
    else .
    end)' "$input_file" > "$output_file"

echo "Processed JSON saved to $output_file"
