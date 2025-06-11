import requests
import re
import csv
import unicodedata
import datetime
from collections import defaultdict

# Structure URLs from HAL API
urls = [
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true&facet.field=structHasAuthIdHal_fs&facet.prefix=1042364_",
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true&facet.field=structHasAuthIdHal_fs&facet.prefix=135977"
]

# Regex to extract relevant fields from HAL JSON
facet_pattern = re.compile(
    r"^(?P<struct_id>\d+)_FacetSep_.*?_JoinSep_(?P<hal_id>.*?)_FacetSep_(?P<full_name>.+)$"
)

def final_normalize_name(name):
    # Remove accents and lowercase
    name = ''.join(
        c for c in unicodedata.normalize('NFD', name)
        if unicodedata.category(c) != 'Mn'
    ).lower()
    # Normalize punctuation and spacing
    name = re.sub(r'[^a-z0-9\s]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()
    parts = name.split()
    if not parts:
        return ""
    surname = parts[0]
    initials = ''.join(p[0] for p in parts[1:])
    return f"{surname} {initials}"

# Data structure to aggregate authors
authors = defaultdict(lambda: {"names": set(), "hal_ids": set(), "count": 0})

# Query and parse both URLs
for url in urls:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    entries = data["facet_counts"]["facet_fields"]["structHasAuthIdHal_fs"]
    
    for i in range(0, len(entries), 2):
        entry, count = entries[i], entries[i+1]
        match = facet_pattern.match(entry)
        if match:
            hal_id = match.group("hal_id") or None
            full_name = match.group("full_name").strip()
            norm_key = final_normalize_name(full_name)

            authors[norm_key]["names"].add(full_name)
            if hal_id:
                authors[norm_key]["hal_ids"].add(hal_id)
            authors[norm_key]["count"] += count

# Write deduplicated results to vCard
output_path = "cired_authors.vcf"
with open(output_path, mode="w", encoding="utf-8") as f:
    for key in sorted(authors):
        data = authors[key]
        preferred_name = sorted(data["names"])[0]
        # Séparer nom et prénom
        parts = preferred_name.split()
        if len(parts) > 1:
            surname = parts[-1]
            given = " ".join(parts[:-1])
        else:
            surname = preferred_name
            given = ""
        uid = sorted(data["hal_ids"])[0] if data["hal_ids"] else ""
        count = data["count"]
        f.write("BEGIN:VCARD\n")
        f.write("VERSION:4.0\n")
        f.write("PRODID:askHAL.py\n")
        f.write(f"SOURCE:{','.join(urls)}\n")
        f.write(f"REV:{datetime.datetime.utcnow().replace(microsecond=0).isoformat()}Z\n")
        f.write(f"FN:{preferred_name}\n")
        f.write(f"N:{surname};{given};;;\n")
        if uid:
            f.write(f"UID:{uid}\n")
            f.write(f"URL;TYPE=HAL:https://cv.hal.science/{uid}\n")
        f.write(f"NOTE:Publications on HAL: {count}\n")
        f.write("END:VCARD\n\n")

print(f"Saved to {output_path}")

