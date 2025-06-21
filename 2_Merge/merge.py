"""
Module for merging and normalizing vCard contact files for the CIRED alumni directory.

This script ingests multiple vCard sources, normalizes and merges contacts, writes the merged output,
and performs verification for inverted full names (FN).

HDM, 2025-06-21
"""

import vobject
import unicodedata
import re
import logging
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_FILES: list[str] = [
    "askCIRED.vcf",
    "askHAL.vcf",
    "askREPEC.vcf",
    "others.vcf",
    "askEmail.vcf",
    "askNaceur.vcf",
]


def normalize_name(name: str) -> str:
    """
    Normalize a name by removing accents, lowercasing, and reducing to a canonical form.

    Returns the alphabetically earlier of two forms: surname last or surname first.
    """
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
    "Louis Gaetan Marc Giraudet": "giraudet louis gaetan",
    "Franck Lecocq": "lecocq franck",
    "Franck Michel Lecocq": "lecocq franck",
}


def normalize_fn(vcard: vobject.vCard) -> str:
    """
    Normalize the FN (full name) field of a vCard, using whitelists and canonicalization.

    Returns a normalized string for grouping contacts.
    """
    try:
        raw: str = vcard.fn.value.strip()
    except Exception:
        return ""

    # Debug: print the raw FN value
    logging.debug(f"Raw FN: '{raw}'")

    # Check whitelist first - try exact match and also stripped/normalized versions
    whitelist_candidates: list[str] = [
        raw,  # Exact match
        raw.strip(),  # Stripped
        re.sub(r"\s+", " ", raw.strip()),  # Normalized whitespace
    ]

    for candidate in whitelist_candidates:
        if candidate in FN_NORMALIZATION_WHITELIST:
            result: str = normalize_name(FN_NORMALIZATION_WHITELIST[candidate])
            logging.debug(f"Whitelist match: '{candidate}' → '{result}'")
            return result

    # If no whitelist match, use standard normalization
    result: str = normalize_name(raw)
    logging.debug(f"Standard normalization: '{raw}' → '{result}'")
    return result


def merge_vcards(vcards: list[vobject.vCard], sources: list[str]) -> vobject.vCard:
    """Merge a list of vCards and their sources into a single vCard, combining fields and attributing notes/history."""
    base: vobject.vCard = vcards[0]
    merged: vobject.vCard = vobject.vCard()

    # Use expanded name if available
    if hasattr(base, "fn"):
        merged.add("fn").value = base.fn.value

    if hasattr(base, "n"):
        merged.add("n").value = base.n.value

    def add_unique_fields(field_name: str) -> None:
        seen: set[str] = set()
        for card in vcards:
            for field in card.contents.get(field_name, []):
                val: str = str(field.value).strip()
                if val and val not in seen:
                    merged.add(field_name).value = field.value
                    seen.add(val)

    for field in ["org", "email", "tel", "source"]:
        add_unique_fields(field)

    # Special case: preserve TYPEs for URLs
    url_seen: set[tuple[str, tuple]] = set()
    for card in vcards:
        for url_field in card.contents.get("url", []):
            val: str = str(url_field.value).strip()
            url_type: tuple = tuple(url_field.params.get("TYPE", []))
            key = (val, url_type)
            if val and key not in url_seen:
                new_field = merged.add("url")
                new_field.value = url_field.value
                if url_type:
                    new_field.type_param = list(url_type)
                url_seen.add(key)

    # Merge NOTE fields with attribution
    notes: list[str] = []
    seen_notes: set[str] = set()
    for card, source in zip(vcards, sources):
        for note_field in card.contents.get("note", []):
            note: str = str(note_field.value).strip()
            if note and note not in seen_notes:
                attributed_note: str = f"[{source}] {note}"
                notes.append(attributed_note)
                seen_notes.add(note)

    if notes:
        merged.add("note").value = "\n".join(notes)

    # Merge X-CIRED-HISTORY fields with attribution
    histories: list[str] = []
    seen_histories: set[str] = set()
    for card, source in zip(vcards, sources):
        for hist_field in card.contents.get("x-cired-history", []):
            hist: str = str(hist_field.value).strip()
            if hist and hist not in seen_histories:
                attributed_hist: str = f"[{source}] {hist}"
                histories.append(attributed_hist)
                seen_histories.add(hist)
    if histories:
        merged.add("x-cired-history").value = "\n".join(histories)

    return merged


# Debug function to check all FN values before processing
def debug_fn_values(all_contacts: list[vobject.vCard]) -> None:
    """Print all unique FN values to help identify what needs to be in the whitelist."""
    fn_values: set[str] = set()
    for contact in all_contacts:
        if hasattr(contact, "fn"):
            fn_values.add(contact.fn.value.strip())

    print("\n=== ALL UNIQUE FN VALUES ===")
    for fn in sorted(fn_values):
        print(f"'{fn}'")
    print("=" * 30 + "\n")


def ingest_contacts(input_files: list[str]) -> tuple[list[vobject.vCard], list[str]]:
    """
    Ingest vCards from a list of input files, applying FN expansion whitelist.

    Returns a tuple of (contacts, sources).
    """
    all_contacts: list[vobject.vCard] = []
    sources: list[str] = []
    for vcf_file in input_files:
        print(f"Ingesting {vcf_file}")
        with open(vcf_file, "r", encoding="utf-8") as f:
            vcards = list(vobject.readComponents(f.read()))
            print(f"OK ({len(vcards)} cards)")
            for vcard in vcards:
                if hasattr(vcard, "fn"):
                    raw: str = vcard.fn.value.strip()
                    if raw in FN_EXPANSION_WHITELIST:
                        vcard.fn.value = FN_EXPANSION_WHITELIST[raw]
                all_contacts.append(vcard)
                sources.append(vcf_file)
    print(f"Total ingested {len(all_contacts)} cards")
    return all_contacts, sources


def group_contacts(
    all_contacts: list[vobject.vCard], sources: list[str]
) -> tuple[dict[str, list[vobject.vCard]], dict[str, list[str]]]:
    """
    Group contacts and their sources by normalized FN.

    Returns two dictionaries: grouped contacts and grouped sources.
    """
    grouped: dict[str, list[vobject.vCard]] = defaultdict(list)
    grouped_sources: dict[str, list[str]] = defaultdict(list)
    for v, src in zip(all_contacts, sources):
        key: str = normalize_fn(v)
        grouped[key].append(v)
        grouped_sources[key].append(src)
    return grouped, grouped_sources


def merge_all_contacts(
    grouped: dict[str, list[vobject.vCard]], grouped_sources: dict[str, list[str]]
) -> list[vobject.vCard]:
    """Merge all grouped contacts into a list of merged vCards."""
    merged_contacts: list[vobject.vCard] = []
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
    return merged_contacts


def write_merged_contacts(
    merged_contacts: list[vobject.vCard], output_file: str = "merged.vcf"
) -> None:
    """Write merged vCards to an output file in vCard format."""
    with open(output_file, "w", encoding="utf-8") as f:
        for vcard in merged_contacts:
            f.write(vcard.serialize())
            f.write("\n")


def verify_inverted_fn_pairs(vcf_path: str = "merged.vcf") -> None:
    """Find all FN names that appear in both direct and inverted order in the merged vCard file."""
    fn_lines: list[str] = []
    with open(vcf_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("FN:"):
                fn: str = line[3:].strip()
                fn_lines.append(fn)
    fn_set: set[str] = set(fn_lines)
    inverted_pairs: list[tuple[str, str]] = []

    def invert_name(name: str) -> str | None:
        parts: list[str] = name.strip().split()
        if len(parts) < 2:
            return None
        return " ".join(reversed(parts))

    seen: set[tuple[str, str]] = set()
    for fn in fn_lines:
        inverted = invert_name(fn)
        if inverted and inverted in fn_set and (inverted, fn) not in seen:
            inverted_pairs.append((fn, inverted))
            seen.add((fn, inverted))
            seen.add((inverted, fn))
    print("\n=== FN names that appear in both orders ===")
    if inverted_pairs:
        for a, b in sorted(inverted_pairs):
            print(f"{a}  ⇄  {b}")
    else:
        print("No inverted FN pairs found.")
    print("=" * 50)


def main() -> None:
    """Ingest, debug, group, merge, write, and verify contacts."""
    all_contacts, sources = ingest_contacts(INPUT_FILES)
    debug_fn_values(all_contacts)
    grouped, grouped_sources = group_contacts(all_contacts, sources)
    merged_contacts = merge_all_contacts(grouped, grouped_sources)
    write_merged_contacts(merged_contacts)
    verify_inverted_fn_pairs()


if __name__ == "__main__":
    main()
