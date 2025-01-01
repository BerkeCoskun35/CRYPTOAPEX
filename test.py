import json
from collections import OrderedDict

# File paths
input_file = "xrp_hourly_data_merged.json"
output_file = "xrp_hourly_data_with_name.json"

# Cryptocurrency name to add
crypto_name = "XRP"

# Load the JSON data
with open(input_file, "r") as file:
    data = json.load(file)

# Add the cryptocurrency name to each entry, ensuring it appears first
updated_data = []
for entry in data:
    reordered_entry = OrderedDict([("crypto_name", crypto_name)])  # Add 'crypto_name' first
    reordered_entry.update(entry)  # Add the rest of the original fields
    updated_data.append(reordered_entry)

# Save the updated JSON back to a new file
with open(output_file, "w") as file:
    json.dump(updated_data, file, indent=4)

print(f"Updated JSON saved to {output_file}")
