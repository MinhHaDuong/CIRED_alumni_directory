"""
Module for merging and normalizing vCard contact files for the CIRED alumni directory.

This script ingests multiple vCard sources, normalizes and merges contacts, writes the merged output,
and performs verification for inverted full names (FN).

HDM, 2025-06-21
"""

import sys
import unicodedata
import re
import os
import logging
from collections import defaultdict
from typing import cast
import locale
import vobject

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import TypedVCard

# Set locale for collation and sorting
locale.setlocale(locale.LC_COLLATE, "fr_FR.UTF-8")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

INPUT_DIR = "1_Scrape"

INPUT_FILES_NAMES: list[str] = [
    "askCIRED.vcf",
    "askHAL.vcf",
    "askREPEC.vcf",
    "others.vcf",
    "askEmail.vcf",
    "askNaceur.vcf",
]

INPUT_FILES = [
    os.path.join(INPUT_DIR, fname)
    for fname in INPUT_FILES_NAMES
    if os.path.isfile(os.path.join(INPUT_DIR, fname))
]

OUTPUT_FILE = "2_Merge/merged.vcf"


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


# Substitution table for nameforms
# NB: for initialized given names only specify the base form (no dot)
FN_SUBSTITUTION_BASE = {
    "Annick De Barros": "Annick Osthoff Ferreira de Barros",
    "Barbier Bruno": "Bruno Barbier",
    "Boemare Catherine Agnès": "Catherine Boemare",
    "Ben-Ari Tamara": "Tamara Ben-Ari",
    "Cassen C": "Christophe Cassen",
    "Cointe Béatrice": "Béatrice Cointe",
    "Combet E": "Emmanuel Combet",
    "Comte Adrien": "Adrien Comte",
    "Espagne Etienne": "Étienne Espagne",
    "Etchart-vincent Nathalie": "Nathalie Etchart-Vincent",
    "Finon D": "Dominique Finon",
    "Genovese E": "Elisabetta Genovese",
    "Godard Olivier": "Olivier Godard",
    "Grazi F": "Fabio Grazi",
    "Gasser T": "Thomas Gasser",
    "Gusdorf François": "François Gusdorf",
    "Hallegatte Stéphane": "Stéphane Hallegatte",
    "Hourcade Jc": "Jean-Charles Hourcade",
    "Hourcade J-C": "Jean-Charles Hourcade",
    "HC Meriem": "Meriem Hamdi-Cherif",
    "Hamdi-Cherif Meriem": "Meriem Hamdi-Cherif",
    "Hamdi-Cherif M": "Meriem Hamdi-Cherif",
    "Ha-Duong Minh": "Minh Ha-Duong",
    "Levrel H": "Harold Levrel",
    "Louis-Gaetan Marc Giraudet": "Louis-Gaëtan Giraudet",
    "Marta Benito": "Marta Benito Garzon",
    "Monjon S": "Stéphanie Monjon",
    "Nguyen Hoai Son": "Hoai Son Nguyen",
    "Nguyen Nhan Than": "Nhan Than Nguyen",
    "Nguyen Trinh Hoang Anh": "Hoang Anh Nguyen Trinh",
    "Trinh Nguyen Hoang Anh": "Hoang Anh Nguyen Trinh",
    "Trinh Hoang Anh Nguyen": "Hoang Anh Nguyen Trinh",
    "Hoang Anh Trinh Nguyen": "Hoang Anh Nguyen Trinh",
    "Labussiere Olivier": "Olivier Labussiere",
    "Vallet A": "Ameline Vallet",
    "DE LAURETIS Simona": "Simona De Lauretis",
    "EOIN O Broin": "Eoin Ó Broin",
    "Ó Broin Eoin": "Eoin Ó Broin",
    "Thubin": "Camille Thubin",
    "Calas": "Guillaume Calas",
    "FERREIRA da CUNHA Roberto": "Roberto Ferreira da Cunha",
    "Vogt-Schilb Adrien": "Adrien Vogt-Schilb",
    "Marcos Aurélio Vasconcelos Freitas": "Marcos Aurélio Vasconcelos de Freitas",
    "Marcos Aurelio Vasconcelos De Freitas": "Marcos Aurélio Vasconcelos de Freitas",
}

# Dynamically expand to include both 'Lastname X' and 'Lastname X.'
FN_SUBSTITUTION_WHITELIST = {}
for k, v in FN_SUBSTITUTION_BASE.items():
    FN_SUBSTITUTION_WHITELIST[k] = v
    if re.match(r".+ [A-Z]$", k):
        FN_SUBSTITUTION_WHITELIST[k + "."] = v

# Group these names by their normalized form
FN_NORMALIZATION_WHITELIST = {
    "Waisman H.": "waisman henri",
    "Waisman H": "waisman henri",
    "Henri-David Waisman": "waisman henri",
    "Waisman Henri-David": "waisman henri",
    "Waisman Henri David": "waisman henri",
    "Olivier Pierre Sassi": "sassi olivier",
    "Pierre Olivier Sassi": "sassi olivier",
    "Sassi Olivier": "sassi olivier",
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
    "Fisch-Romito Vivien": "vivien fisch romito",
    "Vivien Fisch-Romito": "vivien fisch romito",
}

N_SUBSTITUTION_WHITELIST = {
    "Hoang Anh Nguyen Trinh": ["Nguyen Trinh", "Hoang Anh", "", "", ""],
    "Adrien Comte": ["Comte", "Adrien", "", "", ""],
    "Adrien Vogt-Schilb": ["Vogt-Schilb", "Adrien", "", "", ""],
    "Tamara Ben-Ari": ["Ben-Ari", "Tamara", "", "", ""],
    "Marcos Aurélio Vasconcelos De Freitas": [
        "Freitas",
        "Marcos",
        "Aurélio Vasconcelos de",
        "",
        "",
    ],
    "Annick Osthoff Ferreira de Barros": [
        "Barros",
        "Annick",
        "Osthoff Ferreira de",
        "",
        "",
    ],
    "Roberto Ferreira da Cunha": ["Cunha", "Roberto", "Ferreira da", "", ""],
}


def normalize_fn(vcard: TypedVCard) -> str:
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

    result: str = ""

    for candidate in whitelist_candidates:
        if candidate in FN_NORMALIZATION_WHITELIST:
            result = normalize_name(FN_NORMALIZATION_WHITELIST[candidate])
            logging.debug(f"Whitelist match: '{candidate}' → '{result}'")
            return result

    # If no whitelist match, use standard normalization
    result = normalize_name(raw)
    logging.debug(f"Standard normalization: '{raw}' → '{result}'")
    return result


def merge_vcards(vcards: list[TypedVCard], sources: list[str]) -> TypedVCard:
    """Merge a list of vCards and their sources into a single vCard, combining fields and attributing notes/history."""
    base: TypedVCard = vcards[0]
    merged = cast(TypedVCard, vobject.vCard())

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
def debug_fn_values(all_contacts: list[TypedVCard]) -> None:
    """Print all unique FN values to help identify what needs to be in the whitelist."""
    fn_values: set[str] = set()
    for contact in all_contacts:
        if hasattr(contact, "fn"):
            fn_values.add(contact.fn.value.strip())

    print("\n=== ALL UNIQUE FN VALUES ===")
    for fn in sorted(fn_values):
        print(f"'{fn}'")
    print("=" * 30 + "\n")


def ingest_contacts(input_files: list[str]) -> tuple[list[TypedVCard], list[str]]:
    """
    Ingest vCards from a list of input files, applying FN expansion whitelist.

    Returns a tuple of (contacts, sources).
    """
    all_contacts: list[TypedVCard] = []
    sources: list[str] = []
    for vcf_file in input_files:
        print(f"Ingesting {vcf_file}")
        with open(vcf_file, "r", encoding="utf-8") as f:
            vcards = list(vobject.readComponents(f.read()))  # type: ignore[attr-defined]
            print(f"OK ({len(vcards)} cards)")
            for vcard in vcards:
                if hasattr(vcard, "fn"):
                    raw: str = vcard.fn.value.strip()
                    if raw in FN_SUBSTITUTION_WHITELIST:
                        vcard.fn.value = FN_SUBSTITUTION_WHITELIST[raw]
                if hasattr(vcard, "n"):
                    key = vcard.fn.value.strip()
                    if key in N_SUBSTITUTION_WHITELIST:
                        parts = N_SUBSTITUTION_WHITELIST[key]
                        vcard.n.value = vobject.vcard.Name(
                            family=parts[0],
                            given=parts[1],
                            additional=parts[2],
                            prefix=parts[3],
                            suffix=parts[4],
                        )
                all_contacts.append(vcard)
                sources.append(vcf_file)
    print(f"Total ingested {len(all_contacts)} cards")
    return all_contacts, sources


def group_contacts(
    all_contacts: list[TypedVCard], sources: list[str]
) -> tuple[dict[str, list[TypedVCard]], dict[str, list[str]]]:
    """
    Group contacts and their sources by normalized FN.

    Returns two dictionaries: grouped contacts and grouped sources.
    """
    grouped: dict[str, list[TypedVCard]] = defaultdict(list)
    grouped_sources: dict[str, list[str]] = defaultdict(list)
    for v, src in zip(all_contacts, sources):
        key: str = normalize_fn(v)
        grouped[key].append(v)
        grouped_sources[key].append(src)
    return grouped, grouped_sources


def merge_all_contacts(
    grouped: dict[str, list[TypedVCard]], grouped_sources: dict[str, list[str]]
) -> list[TypedVCard]:
    """Merge all grouped contacts into a list of merged vCards."""
    merged_contacts: list[TypedVCard] = []
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

    merged_contacts.sort(
        key=lambda v: locale.strxfrm(v.fn.value) if hasattr(v, "fn") else ""
    )
    return merged_contacts


def write_merged_contacts(
    merged_contacts: list[TypedVCard], output_file: str = "merged.vcf"
) -> None:
    """Write merged vCards to an output file in vCard format."""
    with open(output_file, "w", encoding="utf-8") as f:
        for vcard in merged_contacts:
            f.write(vcard.serialize())
            f.write("\n")
    print(f"Wrote {len(merged_contacts)} merged contacts to {output_file}")


def verify_inverted_fn_pairs(vcf_path: str = "merged.vcf") -> int:
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
    if inverted_pairs:
        print("\n===== FN names that appear in both orders =====")
        for a, b in sorted(inverted_pairs):
            print(f"{a}  ⇄  {b}")
        print("=" * 47)
    else:
        print("No inverted FN pairs found.")
    return len(inverted_pairs)


def verify_start_similar(vcf_path: str = "merged.vcf") -> int:
    """Find pairs of FN names with identical initial two parts."""
    with open(vcf_path, "r", encoding="utf-8") as f:
        fn_lines = [line[3:].strip() for line in f if line.startswith("FN:")]
    prefix_map: dict[str, list[str]] = defaultdict(list)
    for fn in fn_lines:
        parts = fn.split()
        if len(parts) >= 2:
            prefix = " ".join(parts[:2])
            prefix_map[prefix].append(fn)
    similar_pairs: list[tuple[str, str]] = []
    for fns in prefix_map.values():
        if len(fns) > 1:
            for i in range(len(fns)):
                for j in range(i + 1, len(fns)):
                    similar_pairs.append((fns[i], fns[j]))
    if similar_pairs:
        print("\n===== FN names with identical first two parts =====")
        for a, b in sorted(similar_pairs):
            print(f"{a}  ~  {b}")
        print("=" * 47)
    else:
        print("No FN pairs with identical first two parts found.")
    return len(similar_pairs)

def test_fn_contains_cired(all_contacts: list[TypedVCard], sources: list[str]) -> int:
    """Print and count all vCards whose FN contains 'cired' (case-insensitive)."""
    matches = []
    for v, src in zip(all_contacts, sources):
        if hasattr(v, "fn") and "cired" in v.fn.value.lower():
            matches.append((v.fn.value, src))

    if matches:
        print(f"\n===== FNs suspiciously containing 'cired' =====")
        print(f"\n{len(matches)} found:")
        for fn, src in matches:
            print(f"{fn}  [source: {src}]")
        print("=" * 47)
    else:
        print("No FNs containing 'cired' found.")
    return len(matches)


def test_fn_form(merged_vcf_path: str = "merged.vcf") -> int:
    """
    Print FNs from merged.vcf that have:
    - Any part (word) in ALLCAPS (2+ letters, not just 'R.' or 'H.')
    - Any part that is a single letter (e.g. 'R.' or 'H.')
    - Only one part total (suspicious single-word names)
    """
    with open(merged_vcf_path, encoding="utf-8") as f:
        vcf_data = f.read()
    matches = []
    for v in vobject.readComponents(vcf_data):
        if not hasattr(v, "fn"):
            continue
        fn = v.fn.value
        parts = fn.split()
        has_allcaps = any(
            len(p) >= 2 and p.isupper() and not (len(p) == 2 and p[1] == ".")
            for p in parts
        )
        has_single_letter = any(
            (len(p) == 1 and p.isascii() and p.isalpha())
            or (len(p) == 2 and p[0].isascii() and p[0].isalpha() and p[1] == ".")
            for p in parts
        )

        has_single_part = len(parts) == 1

        if has_allcaps or has_single_letter or has_single_part:
            matches.append((fn, has_allcaps, has_single_letter, has_single_part))

    if matches:
        print(
            "\n=== FNs in merged.vcf with ALLCAPS parts (2+ letters, not 'R.'), single-letter parts, or single-word names ==="
        )
        for fn, has_allcaps, has_single_letter, has_single_part in matches:
            flags = []
            if has_allcaps:
                flags.append("ALLCAPS")
            if has_single_letter:
                flags.append("single-letter")
            if has_single_part:
                flags.append("single-word")
            print(f"{fn} ({', '.join(flags)})")
        print("=" * 40)
    else:
        print("No FNs with ALLCAPS, single-letter parts, or single-word names found.")
    return len(matches)


def main() -> None:
    """Ingest, debug, group, merge, write, and verify contacts."""
    all_contacts, sources = ingest_contacts(INPUT_FILES)
    debug_fn_values(all_contacts)
    grouped, grouped_sources = group_contacts(all_contacts, sources)
    merged_contacts = merge_all_contacts(grouped, grouped_sources)

    write_merged_contacts(merged_contacts, OUTPUT_FILE)

    verify_inverted_fn_pairs(OUTPUT_FILE)
    verify_start_similar(OUTPUT_FILE)
    test_fn_contains_cired(all_contacts, sources)
    test_fn_form(OUTPUT_FILE)


if __name__ == "__main__":
    main()
