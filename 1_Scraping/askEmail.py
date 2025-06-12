#!/usr/bin/env python3
"""
askEmailArchives.py

This module provides utilities to extract, clean, and normalize email addresses and associated display names
from a directory of archived email files. It is tailored for the CIRED alumni directory, focusing on emails
from the domain 'centre-cired.fr'. The script processes email files in parallel, applies heuristics to select
the most appropriate display name for each email, and outputs the results in vCard format.

Functions:
    decode_display_name(name): Decode MIME-encoded display names from email headers.
    extract_emails_from_file(filepath): Extracts (name, email) pairs from a single email file.
    collect_emails(mail_dir): Collects all unique (name, email) pairs from email files in a directory tree.
    count_diacritics(s): Counts the number of diacritic marks in a string.
    is_title_case(s): Checks if all words in a string are title-cased.
    is_initialized(form, full): Determines if a name is an initialized form of another (e.g., "A. Lastname" vs "Adrien Lastname").
    is_all_caps(s): Checks if a string is in all uppercase letters.
    normalize_family_name(s): Normalizes a family name by lowercasing and removing dashes and spaces.
    filter_names(names, email=None): Applies a series of heuristics to select the best display name(s) for an email.
    clean_name(name, email): Cleans and sanitizes a display name, removing unwanted characters and substrings.
    group_emails(emails): Groups display names by email address, skipping mailing lists and cleaning names.
    print_emails(grouped): Prints grouped emails and their filtered display names.
    print_vcards(emails): Outputs grouped emails and names in vCard 4.0 format.

Constants:
    MAIL_DIR: Path to the directory containing archived email files.
    EMAIL_PATTERN: Regular expression pattern for matching CIRED email addresses.

Usage:
    Run as a script to extract and print vCards for all unique CIRED email addresses found in the archive.
"""

import os
import re
import concurrent.futures
from collections import defaultdict
import unicodedata
from datetime import datetime, UTC

from email.utils import getaddresses
from email.header import decode_header, make_header

MAIL_DIR = "/home/haduong/.mail/Archives"
EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@centre-cired\.fr"


def decode_display_name(name):
    try:
        return str(make_header(decode_header(name)))
    except Exception:
        return name

def extract_emails_from_file(filepath):
    emails = set()
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith(("To:", "From:", "Cc:")):
                    # Remove the header name (e.g., "To: ") for getaddresses
                    header_value = line.split(":", 1)[1].strip()
                    for name, email in getaddresses([header_value]):
                        email = email.lower()   # Normalize email to lowercase
                        if re.fullmatch(EMAIL_PATTERN, email):
                            decoded_name = decode_display_name(name)
                            emails.add((decoded_name, email))
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return emails

def collect_emails(mail_dir):
    file_paths = []
    for root, _, files in os.walk(mail_dir):
        for file in files:
            name = file.split(":")[0]
            if name.endswith(".txt") or name.endswith(".eml"):
                path = os.path.join(root, file)
                file_paths.append(path)
    total_files = len(file_paths)
    print(f"Number of files to read: {total_files}")

    all_emails = set()
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(extract_emails_from_file, file_paths)
            for idx, emails in enumerate(results, 1):
                all_emails.update(emails)
                if idx % 500 == 0 or idx == total_files:
                    percent = (idx / total_files) * 100
                    print(f"Processed {idx} files... ({percent:.1f}%)")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Returning results collected so far.")
        return sorted(all_emails)
    return sorted(all_emails)

def count_diacritics(s):
    return sum(1 for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) == 'Mn')

def is_title_case(s):
    # Returns True if all words are title-cased (first letter uppercase, rest lowercase)
    return all(word[:1].isupper() and word[1:].islower() for word in s.split() if word)

def is_initialized(form, full):
    # "A. Lastname" vs "Adrien Lastname"
    parts = form.split()
    if len(parts) < 2 or '.' not in parts[0]:
        return False
    initial = parts[0][0].lower()
    full_parts = full.split()
    if not full_parts:
        return False
    return initial == full_parts[0][0].lower() and parts[-1].lower() == full_parts[-1].lower()

def is_all_caps(s):
    return s.isupper()

def normalize_family_name(s):
    # Lowercase and remove dashes and spaces
    return s.lower().replace("-", "").replace(" ", "")

def filter_names(names, email=None):
    names = set(names)

    # Prefer forms with the most diacritics
    diacritic_counts = {n: count_diacritics(n) for n in names}
    if diacritic_counts:
        max_diacritics = max(diacritic_counts.values())
        names = {n for n, count in diacritic_counts.items() if count == max_diacritics}

    # Remove names that are substrings of others (case-insensitive)
    filtered = set()
    lowered = [n.lower() for n in names]
    for n in names:
        n_l = n.lower()
        if not any((n_l != o and n_l in o) for o in lowered):
            filtered.add(n)
    names = filtered

    # Remove initialized forms if full form exists
    to_remove = set()
    for n in names:
        for o in names:
            if n != o and is_initialized(n, o):
                to_remove.add(n)
    names = names - to_remove

    # Prefer capitalized over all-caps
    capitalized = {n for n in names if not is_all_caps(n)}
    if capitalized:
        names = capitalized

    # Prefer title case (all words capitalized) if available
    title_cased = {n for n in names if is_title_case(n)}
    if title_cased:
        names = title_cased

    # Prefer forms where the normalized last name (from email) matches the normalized last word
    if email:
        last_name = normalize_family_name(email.split('@')[0].split('.')[-1])
        preferred = set()
        for n in names:
            last_word = n.split()[-1]
            if normalize_family_name(last_word) == last_name:
                preferred.add(n)
        if preferred:
            # If both hyphenated and non-hyphenated forms exist, prefer hyphenated (anywhere in the last word)
            hyphenated = {n for n in preferred if '-' in n.split()[-1]}
            if hyphenated:
                names = hyphenated
            else:
                names = preferred

    # Handle "Lastname, Firstname" -> "Firstname Lastname"
    comma_processed = set()
    for n in names:
        if ',' in n:
            parts = [p.strip() for p in n.split(',', 1)]
            if len(parts) == 2:
                # Reorder and titlecase both parts
                comma_processed.add(f"{parts[1].title()} {parts[0].title()}")
                continue
        comma_processed.add(n)
    if comma_processed:
        names = comma_processed

    # Special handling for two-part names with one part all caps
    processed = set()
    for n in names:
        parts = n.split()
        if len(parts) == 2:
            # Case 1: first part is all caps and matches email last name
            if parts[0].isupper() and email:
                last_name = normalize_family_name(email.split('@')[0].split('.')[-1])
                if normalize_family_name(parts[0]) == last_name:
                    # Move it to the end and titlecase both
                    processed.add(f"{parts[1].title()} {parts[0].title()}")
                    continue
            # Case 2: second part is all caps
            if parts[1].isupper():
                processed.add(f"{parts[0].title()} {parts[1].title()}")
                continue
        processed.add(n)
    if processed:
        names = processed

    # Override for specific known cases
    if email == "haduong@centre-cired.fr":
        return {"Minh Ha-Duong"}
    if email == "hourcade@centre-cired.fr":
        return {"Jean-Charles Hourcade"}

    # Title case if necessary
    if len(names) == 1:
       single = next(iter(names))
       if single.islower():
           names = {single.title()}

    return names

def clean_name(name, email):
    """Remove unwanted characters and drop names containing the email address."""
    name = name.strip(" '\"\t[]()")
    for unwanted in ["_POP local", "_poplocal", " - CIRED"]:
        name = name.replace(unwanted, "")
    # Remove if the email address is a substring (case-insensitive)
    if name and email.lower() in name.lower():
        return ""
    return name


def group_emails(emails):
    grouped = defaultdict(set)
    for name, email in emails:
        skip_prefixes = ["liste-", "cired-", "resident", "summer.", "hoby."]
        if any(email.startswith(prefix) for prefix in skip_prefixes):
            continue  # Skip mailing lists
        cleaned = clean_name(name, email)
        if cleaned:
            grouped[email].add(cleaned)
    return grouped

def print_emails(grouped):
    for email, names in sorted(grouped.items()):
        filtered_names = filter_names(names, email=email)
        name_list = ", ".join(sorted(n for n in filtered_names if n))
        print(f"{email}: {name_list}" if name_list else email)
        # Debug: print the original list of names for this email
#        print(f"  [original: {', '.join(sorted(names))}]")

def print_vcards(emails, output_file=None):
    now = datetime.now(UTC).isoformat(timespec='seconds') + "Z"
    lines = []
    for email, names in sorted(emails.items()):
        filtered_names = filter_names(names, email=email)
        for name in sorted(filtered_names):
            lines.append("BEGIN:VCARD")
            lines.append("VERSION:4.0")
            lines.append("PRODID:-//askEmail.py//")
            lines.append(f"REV:{now}")
            lines.append(f"SOURCE:{MAIL_DIR}")
            lines.append(f"FN:{name}")
            lines.append(f"EMAIL;TYPE=obsolete:{email}")
            lines.append("END:VCARD\n")
    content = "\n".join(lines)
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print(content)


if __name__ == "__main__":
    emails = collect_emails(MAIL_DIR)
    grouped_emails = group_emails(emails)
    # print_emails(grouped_emails)
    print_vcards(grouped_emails, output_file="askEmail.vcf")