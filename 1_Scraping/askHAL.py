import requests
import re
import csv
import unicodedata
from collections import defaultdict
from typing import TypedDict

# Structure URLs from HAL API
urls = [
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true&facet.field=structHasAuthIdHal_fs&facet.prefix=1042364_",
    "https://api.archives-ouvertes.fr/search/?q=*:*&rows=0&facet=true&facet.field=structHasAuthIdHal_fs&facet.prefix=135977",
]

# Regex to extract relevant fields from HAL JSON
facet_pattern = re.compile(
    r"^(?P<struct_id>\d+)_FacetSep_.*?_JoinSep_(?P<hal_id>.*?)_FacetSep_(?P<full_name>.+)$"
)


def final_normalize_name(name):
    # Remove accents and lowercase
    name = "".join(
        c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn"
    ).lower()
    # Normalize punctuation and spacing
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    parts = name.split()
    if not parts:
        return ""
    surname = parts[0]
    initials = "".join(p[0] for p in parts[1:])
    return f"{surname} {initials}"


# Data structure to aggregate authors
class AuthorInfo(TypedDict):
    names: set[str]
    hal_ids: set[str]
    count: int

authors : defaultdict[str, AuthorInfo] = defaultdict(lambda: {"names": set(), "hal_ids": set(), "count": 0})

# Query and parse both URLs
for url in urls:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    entries = data["facet_counts"]["facet_fields"]["structHasAuthIdHal_fs"]

    for i in range(0, len(entries), 2):
        entry, count = entries[i], entries[i + 1]
        match = facet_pattern.match(entry)
        if match:
            hal_id = match.group("hal_id") or None
            full_name = match.group("full_name").strip()
            norm_key = final_normalize_name(full_name)

            authors[norm_key]["names"].add(full_name)
            if hal_id:
                authors[norm_key]["hal_ids"].add(hal_id)
            authors[norm_key]["count"] += count

# Write deduplicated results to CSV
output_path = "cired_authors_deduplicated.csv"
with open(output_path, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["Full Name", "HAL ID(s)", "Publication Count"])
    for key in sorted(authors):
        data = authors[key]
        preferred_name = sorted(data["names"])[0]
        hal_ids = ";".join(sorted(data["hal_ids"])) if data["hal_ids"] else ""
        writer.writerow([preferred_name, hal_ids, data["count"]])

print(f"Saved to {output_path}")
