#!/usr/bin/env python3
"""
vCard Merger - Merge multiple vCard files into one
"""

import vobject
import sys
from pathlib import Path

def safe_serialize(vcard):
    """Serialize vCard safely, flatten list values and clean up lines."""
    try:
        raw = vcard.serialize()
        if isinstance(raw, list):
            raw = ''.join(raw)
        return raw
    except Exception as e:
        print(f"Warning: safe_serialize fallback: {e}", file=sys.stderr)
        lines = ["BEGIN:VCARD"]
        for comp_list in vcard.contents.values():
            for comp in comp_list:
                data = comp.serialize()
                if isinstance(data, list):
                    data = ''.join(data)
                for line in data.splitlines():
                    line = line.strip()
                    if line.upper() not in ["BEGIN:VCARD", "END:VCARD", ""]:
                        lines.append(line)
        lines.append("END:VCARD")
        return "\r\n".join(lines) + "\r\n"

def read_vcards_from_file(file_path):
    """Read all vCards from a file and return them as a list."""
    vcards = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Handle multiple vCards in one file
        vcard_blocks = content.split('BEGIN:VCARD')

        for block in vcard_blocks[1:]:  # Skip first empty element
            vcard_text = 'BEGIN:VCARD' + block
            try:
                vcard = vobject.readOne(vcard_text)
                vcards.append(vcard)
            except Exception as e:
                print(f"Warning: Could not parse vCard block in {file_path}: {e}")
                continue

    except FileNotFoundError:
        print(f"Error: File {file_path} not found")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

    return vcards

def merge_vcard_files(file_paths, output_path):
    """Merge multiple vCard files into one."""
    all_vcards = []

    # Read vCards from all input files
    for file_path in file_paths:
        print(f"Reading vCards from {file_path}...")
        vcards = read_vcards_from_file(file_path)
        all_vcards.extend(vcards)
        print(f"Found {len(vcards)} vCard(s)")

    if not all_vcards:
        print("No vCards found in any of the input files!")
        return False

    # Write merged vCards to output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, vcard in enumerate(all_vcards):
                if i > 0:
                    f.write('\n')  # Add blank line between vCards
                f.write(safe_serialize(vcard))

        print(f"Successfully merged {len(all_vcards)} vCard(s) into {output_path}")
        return True

    except Exception as e:
        print(f"Error writing to {output_path}: {e}")
        return False

def remove_duplicates(vcards):
    """Remove duplicate vCards based on name and email."""
    seen = set()
    unique_vcards = []

    for vcard in vcards:
        # Create a unique identifier
        name = getattr(vcard, 'fn', None)
        email = getattr(vcard, 'email', None)

        name_val = name.value if name else "Unknown"
        email_val = email.value if email else "No Email"

        identifier = f"{name_val}|{email_val}".lower()

        if identifier not in seen:
            seen.add(identifier)
            unique_vcards.append(vcard)
        else:
            print(f"Skipping duplicate: {name_val}")

    return unique_vcards

def merge_with_dedup(file_paths, output_path):
    """Merge vCard files and remove duplicates."""
    all_vcards = []

    # Read all vCards
    for file_path in file_paths:
        print(f"Reading vCards from {file_path}...")
        vcards = read_vcards_from_file(file_path)
        all_vcards.extend(vcards)
        print(f"Found {len(vcards)} vCard(s)")

    if not all_vcards:
        print("No vCards found!")
        return False

    print(f"Total vCards before deduplication: {len(all_vcards)}")

    # Remove duplicates
    unique_vcards = remove_duplicates(all_vcards)
    print(f"Unique vCards after deduplication: {len(unique_vcards)}")

    # Write to output file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            for i, vcard in enumerate(unique_vcards):
                if i > 0:
                    f.write('\n')
                f.write(safe_serialize(vcard))

        print(f"Successfully merged {len(unique_vcards)} unique vCard(s) into {output_path}")
        return True

    except Exception as e:
        print(f"Error writing to {output_path}: {e}")
        return False

def main():
    """Main function to handle command line usage."""
    if len(sys.argv) < 4:
        print("Usage: python vcard_merger.py <file1.vcf> <file2.vcf> <file3.vcf> [output.vcf]")
        print("Example: python vcard_merger.py contacts1.vcf contacts2.vcf contacts3.vcf merged.vcf")
        sys.exit(1)

    # Get input files
    input_files = sys.argv[1:-1] if len(sys.argv) > 4 else sys.argv[1:4]
    output_file = sys.argv[-1] if len(sys.argv) > 4 else "merged_contacts.vcf"

    # Verify input files exist
    for file_path in input_files:
        if not Path(file_path).exists():
            print(f"Error: File {file_path} does not exist")
            sys.exit(1)

    print(f"Merging {len(input_files)} vCard files...")
    print(f"Input files: {', '.join(input_files)}")
    print(f"Output file: {output_file}")
    print()

    # Ask user about deduplication
    while True:
        choice = input("Remove duplicates? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            # success = merge_with_dedup(input_files, output_file)  # Déduplication désactivée
            success = merge_vcard_files(input_files, output_file)
            break
        elif choice in ['n', 'no']:
            success = merge_vcard_files(input_files, output_file)
            break
        else:
            print("Please enter 'y' or 'n'")

    if success:
        print("\nMerge completed successfully!")
    else:
        print("\nMerge failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
