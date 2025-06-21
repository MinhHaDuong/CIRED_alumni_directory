#!/usr/bin/env python3
"""
Excel to VCARDS Converter Script
Converts an Excel file containing contact information to VCARDS format.

Requirements:
- pandas
- openpyxl (for Excel file reading)

Install with: pip install pandas openpyxl
"""

import pandas as pd
from datetime import datetime
import sys
import os

def excel_to_vcards(excel_file, output_file=None):
    """
    Convert Excel file to VCARDS format.

    Args:
        excel_file (str): Path to the Excel file
        output_file (str): Path for the output VCARDS file (optional)

    Returns:
        str: VCARDS content
    """

    # Read Excel file
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

    # Expected columns: NOM, Prénom, Mail
    required_columns = ['NOM', 'Prénom', 'Mail']

    # Check if required columns exist
    for col in required_columns:
        if col not in df.columns:
            print(f"Warning: Column '{col}' not found in the Excel file.")
            print(f"Available columns: {list(df.columns)}")

    # Clean data - remove NaN values and convert to string
    df = df.fillna('')
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()

    # Generate timestamp for REV field
    timestamp = datetime.now().isoformat() + 'Z'

    vcards_content = []
    processed_count = 0

    for index, row in df.iterrows():
        nom = row.get('NOM', '').strip()
        prenom = row.get('Prénom', '').strip()
        email = row.get('Mail', '').strip()

        # Skip empty records
        if not nom and not prenom and not email:
            continue

        # Convert last name from ALL CAPS to title case (initialized)
        if nom:
            nom = nom.title()

        # Create FN (Full Name) as "Prénom Nom"
        full_name = f"{prenom} {nom}".strip()

        # Handle multiple email addresses (separated by newlines or other delimiters)
        emails = []
        if email:
            # Split by common delimiters
            email_parts = email.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            emails = [e.strip() for e in email_parts if e.strip()]

        # Start VCARD
        vcard = []
        vcard.append('BEGIN:VCARD')
        vcard.append('VERSION:3.0')
        vcard.append(f'FN:{full_name}')
        vcard.append(f'N:{nom};{prenom};;;')

        # Add email addresses
        for email_addr in emails:
            if email_addr:
                vcard.append(f'EMAIL:{email_addr}')

        # Add required fields
        vcard.append('SOURCE:Naceur Chaabane email')
        vcard.append(f'REV:{timestamp}')
        vcard.append('END:VCARD')

        vcards_content.append('\n'.join(vcard))
        processed_count += 1

    # Join all VCARDs
    final_content = '\n\n'.join(vcards_content)

    # Write to file if output path specified
    if output_file:
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(final_content)
            print(f"VCARDS file saved to: {output_file}")
        except Exception as e:
            print(f"Error writing to file: {e}")
            return None

    print(f"Successfully processed {processed_count} contacts")
    return final_content

def main():
    """Main function to handle command line arguments."""

    if len(sys.argv) < 2:
        print("Usage: python toVcards.py CIRED_Anciens.xlsx ../askNaceur.vcf")
        sys.exit(1)

    excel_file = sys.argv[1]

    # Check if input file exists
    if not os.path.exists(excel_file):
        print(f"Error: File '{excel_file}' not found.")
        sys.exit(1)

    # Generate output filename if not provided
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        base_name = os.path.splitext(excel_file)[0]
        output_file = f"{base_name}.vcf"

    # Convert the file
    vcards_content = excel_to_vcards(excel_file, output_file)

    if vcards_content:
        print("Conversion completed successfully!")
        print(f"Output file: {output_file}")
    else:
        print("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
