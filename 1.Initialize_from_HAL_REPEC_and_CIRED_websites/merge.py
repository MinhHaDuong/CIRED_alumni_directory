#!/usr/bin/env python3
"""
vCard Merger - Fusion basique de fichiers vCard avec python-vcard
"""

import sys
from vcard import readComponents

def main():
    if len(sys.argv) < 4:
        print("Usage: python merge.py <file1.vcf> <file2.vcf> ... <output.vcf>")
        sys.exit(1)

    *input_files, output_file = sys.argv[1:]
    cards = []
    for file_path in input_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            for card in readComponents(f):
                cards.append(card)

    with open(output_file, 'w', encoding='utf-8') as f:
        for card in cards:
            f.write(card.serialize())
            f.write('\n')

    print(f"Fusion terminée : {len(cards)} vCard(s) dans {output_file}")

if __name__ == "__main__":
    main()
