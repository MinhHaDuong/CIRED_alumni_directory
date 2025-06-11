import vobject
import unicodedata
import re
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def normalize_name(name):
    name = "".join(
        c for c in unicodedata.normalize("NFD", name) if unicodedata.category(c) != "Mn"
    ).lower()
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    parts = name.split()
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]

    # Option 1: surname last
    surname1 = parts[-1]
    initials1 = "".join(p[0] for p in parts[:-1])
    form1 = f"{surname1} {initials1}"

    # Option 2: surname first
    surname2 = parts[0]
    initials2 = "".join(p[0] for p in parts[1:])
    form2 = f"{surname2} {initials2}"

    # Return the alphabetically earlier one to group both forms together
    return min(form1, form2)


FN_EXPANSION_WHITELIST = {
    # Entries without a given name
    "Grazi F": "Fabio Grazi",
    "Grazi F.": "Fabio Grazi",
    "Gasser T.": "Thomas Gasser",
    "Gasser T": "Thomas Gasser",
    "Combet E.": "Emmanuel Combet",
    "Combet E": "Emmanuel Combet",
    "Hamdi-Cherif M.": "Meriem Hamdi-Cherif",
    "Hamdi-Cherif M": "Meriem Hamdi-Cherif",
    "Monjon S": "Stéphanie Monjon",
    "Monjon S.": "Stéphanie Monjon",
    "Genovese E.": "Elisabetta Genovese",
    "Finon D": "Dominique Finon",
    "Ha-Duong Minh": "Minh Ha-Duong",
    "Nguyen Hoai Son": "Hoai Son Nguyen",
    "Nguyen Nhan Than": "Nhan Than Nguyen",
    "Nguyen Trinh Hoang Anh": "Hoang Anh Nguyen Trinh",
    "Godard Olivier": "Olivier Godard",
    "Labussiere Olivier": "Olivier Labussiere",
    "Barbier Bruno": "Bruno Barbier",
    "Boemare Catherine Agnès": "Catherine Boemare",
    "Cointe Béatrice": "Béatrice Cointe",
    "Espagne Etienne": "Étienne Espagne",
    "Etchart-vincent Nathalie": "Nathalie Etchart-Vincent",
    "Hallegatte Stéphane": "Stéphane Hallegatte",
    "Gusdorf François": "François Gusdorf",
    "Hourcade Jc": "Jean-Charles Hourcade",
}
FN_NORMALIZATION_WHITELIST = {
    # Handle variations with and without periods, different spacing
    "Cassen C.": "cassen christophe",
    "Cassen C": "cassen christophe",
    "Levrel H.": "levrel harold",
    "Levrel H": "levrel harold",
    "Waisman H.": "waisman henri",
    "Waisman H": "waisman henri",
    "Waisman Henri-David": "waisman henri",
    "Waisman Henri David": "waisman henri",
    "Vallet A.": "vallet ameline",
    "Vallet A": "vallet ameline",
    "Olivier Pierre Sassi": "sassi olivier",
    "Pierre Olivier Sassi": "sassi olivier",
    "Sassi Olivier": "sassi olivier",
    "Hourcade J-C": "hourcade jean charles",
    "Hourcade J.C": "hourcade jean charles",
    "Hourcade J.C.": "hourcade jean charles",
    "Hourcade Jean-Charles": "hourcade jean charles",
    "Hourcade Jean Charles": "hourcade jean charles",
    "Louis-Gaëtan Giraudet": "giraudet louis gaetan",
    "Louis-Gaetan Giraudet": "giraudet louis gaetan",
    "Louis Gaetan Giraudet": "giraudet louis gaetan",
    "Louis-Gaetan Marc Giraudet": "giraudet louis gaetan",
    "Louis Gaetan Marc Giraudet": "giraudet louis gaetan",
    "Franck Lecocq": "lecocq franck",
    "Franck Michel Lecocq": "lecocq franck",
}


def normalize_fn(vcard):
    try:
        raw = vcard.fn.value.strip()
    except Exception:
        return ""

    # Debug: print the raw FN value
    logging.debug(f"Raw FN: '{raw}'")

    # Check whitelist first - try exact match and also stripped/normalized versions
    whitelist_candidates = [
        raw,  # Exact match
        raw.strip(),  # Stripped
        re.sub(r"\s+", " ", raw.strip()),  # Normalized whitespace
    ]

    for candidate in whitelist_candidates:
        if candidate in FN_NORMALIZATION_WHITELIST:
            result = normalize_name(FN_NORMALIZATION_WHITELIST[candidate])
            logging.debug(f"Whitelist match: '{candidate}' → '{result}'")
            return result

    # If no whitelist match, use standard normalization
    result = normalize_name(raw)
    logging.debug(f"Standard normalization: '{raw}' → '{result}'")
    return result


def merge_vcards(vcards, sources):
    base = vcards[0]
    merged = vobject.vCard()

    # Use expanded name if available
    if hasattr(base, "fn"):
        merged.add("fn").value = base.fn.value

    if hasattr(base, "n"):
        merged.add("n").value = base.n.value

    def add_unique_fields(field_name):
        seen = set()
        for card in vcards:
            for field in card.contents.get(field_name, []):
                val = str(field.value).strip()
                if val and val not in seen:
                    merged.add(field_name).value = field.value
                    seen.add(val)

    for field in ["org", "email", "tel", "source"]:
        add_unique_fields(field)

    # Special case: preserve TYPEs for URLs
    url_seen = set()
    for card in vcards:
        for url_field in card.contents.get("url", []):
            val = str(url_field.value).strip()
            url_type = tuple(url_field.params.get("TYPE", []))  # a tuple to use as key
            key = (val, url_type)
            if val and key not in url_seen:
                new_field = merged.add("url")
                new_field.value = url_field.value
                if url_type:
                    new_field.type_param = list(url_type)  # this sets the TYPE=xxx
                url_seen.add(key)

    # Merge NOTE fields with attribution
    notes = []
    seen_notes = set()
    for card, source in zip(vcards, sources):
        for note_field in card.contents.get("note", []):
            note = str(note_field.value).strip()
            if note and note not in seen_notes:
                attributed_note = f"[{source}] {note}"
                notes.append(attributed_note)
                seen_notes.add(note)

    if notes:
        merged.add("note").value = "\n".join(notes)

    # Merge X-CIRED-HISTORY fields with attribution
    histories = []
    seen_histories = set()
    for card, source in zip(vcards, sources):
        for hist_field in card.contents.get("x-cired-history", []):
            hist = str(hist_field.value).strip()
            if hist and hist not in seen_histories:
                attributed_hist = f"[{source}] {hist}"
                histories.append(attributed_hist)
                seen_histories.add(hist)
    if histories:
        merged.add("x-cired-history").value = "\n".join(histories)

    return merged


# Debug function to check all FN values before processing
def debug_fn_values(all_contacts):
    """Print all unique FN values to help identify what needs to be in the whitelist"""
    fn_values = set()
    for contact in all_contacts:
        if hasattr(contact, "fn"):
            fn_values.add(contact.fn.value.strip())

    print("\n=== ALL UNIQUE FN VALUES ===")
    for fn in sorted(fn_values):
        print(f"'{fn}'")
    print("=" * 30 + "\n")


# Ingest
all_contacts = []
sources = []
for vcf_file in ["askCIRED.vcf", "askHAL.vcf", "askREPEC.vcf"]:
    print(f"Ingesting {vcf_file}")
    with open(vcf_file, "r", encoding="utf-8") as f:
        vcards = list(vobject.readComponents(f.read()))
        print(f"OK ({len(vcards)} cards)")
        for vcard in vcards:
            if hasattr(vcard, "fn"):
                raw = vcard.fn.value.strip()
                if raw in FN_EXPANSION_WHITELIST:
                    vcard.fn.value = FN_EXPANSION_WHITELIST[raw]
            all_contacts.append(vcard)
            sources.append(vcf_file)
print(f"Total ingested {len(all_contacts)} cards")

# Debug: Show all FN values
debug_fn_values(all_contacts)

# Group by normalized FN
grouped = defaultdict(list)
grouped_sources = defaultdict(list)

for v, src in zip(all_contacts, sources):
    key = normalize_fn(v)
    grouped[key].append(v)
    grouped_sources[key].append(src)

# Merge and log
merged_contacts = []

for fn_key in sorted(grouped.keys()):
    vcards = grouped[fn_key]
    sources_list = grouped_sources[fn_key]

    if len(vcards) > 1:
        merged_fn = vcards[0].fn.value if hasattr(vcards[0], "fn") else "(no FN)"
        logging.info(f"Merging normalized FN '{fn_key}' → '{merged_fn}'")
        for v, src in zip(vcards, sources_list):
            orig_fn = v.fn.value if hasattr(v, "fn") else "(no FN)"
            logging.info(f"  └─ from {src}: '{orig_fn}'")

    merged_contacts.append(merge_vcards(vcards, sources_list))

merged_contacts.sort(key=lambda v: v.fn.value.lower() if hasattr(v, "fn") else "")

# Write
with open("merged.vcf", "w", encoding="utf-8") as f:
    for vcard in merged_contacts:
        f.write(vcard.serialize())
        f.write("\n")

print(f"Written {len(merged_contacts)} merged cards.")

# Step 1: Read back all FN lines from merged.vcf
fn_lines = []
with open("merged.vcf", "r", encoding="utf-8") as f:
    for line in f:
        if line.startswith("FN:"):
            fn = line[3:].strip()
            fn_lines.append(fn)

# Step 2: Store the original and inverted forms
fn_set = set(fn_lines)
inverted_pairs = []


def invert_name(name):
    parts = name.strip().split()
    if len(parts) < 2:
        return None  # cannot invert
    return " ".join(reversed(parts))


# Step 3: Check for inverted name pairs
seen = set()
for fn in fn_lines:
    inverted = invert_name(fn)
    if inverted and inverted in fn_set and (inverted, fn) not in seen:
        inverted_pairs.append((fn, inverted))
        seen.add((fn, inverted))
        seen.add((inverted, fn))  # avoid double reporting

# Step 4: Print results
print("\n=== FN names that appear in both orders ===")
if inverted_pairs:
    for a, b in sorted(inverted_pairs):
        print(f"{a}  ⇄  {b}")
else:
    print("No inverted FN pairs found.")
print("=" * 50)
