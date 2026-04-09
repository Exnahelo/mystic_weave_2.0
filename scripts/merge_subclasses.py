# This script merges two JSON arrays of subclass entries, deduplicating by 'index'.
import json
import sys

# Load both files
with open('data/srd/subclasses.json') as f:
    base = json.load(f)
with open('/Users/danielhowe/Downloads/subclasses_new_entries.json') as f:
    new = json.load(f)

# Build a dict by 'index' for fast deduplication
merged = {entry['index']: entry for entry in base}
for entry in new:
    merged[entry['index']] = entry  # Overwrite or add

# Write merged result back to subclasses.json
with open('data/srd/subclasses.json', 'w') as f:
    json.dump(list(merged.values()), f, indent=2)

print(f"Merged {len(base)} + {len(new)} entries → {len(merged)} unique subclasses.")
