import json
import re

# Load the JSON file
input_file = "go_nogo_interrupt_stimuli.json"
output_file = "modified_go_nogo_interrupt_stimuli.json"

with open(input_file, "r") as file:
    data = json.load(file)

# Function to modify file names
def modify_filename(filename):
    match = re.match(r"b(\d+)([a-zA-Z])(\d+)_.*", filename)
    if match:
        num = int(match.group(1))
        if num <= 4:
            filename = "z" + filename[1:]  # Replace 'b' with 'z'
        elif num >= 5:
            filename = "g" + filename[1:]  # Replace 'b' with 'g'
    return filename

# Update the JSON structure
data["stims"] = {modify_filename(k): modify_filename(v) for k, v in data["stims"].items()}

# Save the updated JSON to a file
with open(output_file, "w") as file:
    json.dump(data, file, indent=4)


