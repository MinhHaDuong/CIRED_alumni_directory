#!/usr/bin/env python3
"""
Quick fix script to inject known emails for specific people.
"""

import sys
import os
import argparse
import logging
from typing import Literal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ingest_vcards, TypedVCard, setup_logging, process_vcards, output_vcards

# Known email mappings - populate these with actual emails
KNOWN_EMAILS = {
    "Clément Feger": "clement.fege@agroparistech.fr",
    "Daniel Thery": "",
    "Guillaume Calas": "erthindol@hotmail.com",
    "Hoby Ratsihoarana": "hoby.ratsihoarana@gmail.com",
    "Héloïse Guillaumin": "heloise.guillaumin@gmail.com",
    "Ilaria Brunetti": "ilaria.brunetti@uzh.ch",
    "Isabelle Billy": "isabelle.billy348@orange.fr",
    "Jean-Charles Hourcade": "jch.hourcade@gmail.com",
    "Joël Hamann": "hamann.joel@orange.fr",
    "Laure Lampin": "laure.grazi@dgtresor.gouv.fr",
    "Li Jun": "prunush208@gmail.com",
    "Minh Ha-Duong": "minh.ha-duong@cnrs.fr",
    "Nhan Nguyen": "nhanait@yahoo.com",
    "Samuel Juhel": "samuel.juhel@usys.ethz.ch",
    "Serine Guichoud": "",
    "Sébastien Duquesnoy": "sebastien.duquesnoy@gmail.com",
    "Ta Mai-Thi": "",
    "Thanh Nguyen": "",
    "Thibault Corneloup": "thi.loup3@gmail.com",
}

def fix_vcard(vcard: TypedVCard, args: argparse.Namespace) -> TypedVCard:
    """
    Fix a single vCard by injecting known email if available.

    Args:
        vcard: The vCard to potentially fix
        args: Command line arguments (unused but required for process_vcards interface)

    Returns:
        The vCard, potentially modified with injected email
    """
    if not hasattr(vcard, 'fn'):
        logging.error(f"No FN found for vCard, skipping {vcard.serialize()}")
        return vcard

    fn_value = vcard.fn.value.strip()

    if fn_value not in KNOWN_EMAILS:
        return vcard

    email_to_add = KNOWN_EMAILS[fn_value].strip()

    if email_to_add == "":
        return vcard

    add_vcard_field(vcard, "email", email_to_add)
    add_vcard_field(vcard, "note", "Email manually added via fix script")

    logging.info(f"Fixed email for: {fn_value} -> {email_to_add}")
    return vcard


def add_vcard_field(vcard: TypedVCard, field: Literal["email", "note"], value: str) -> None:
    """Add a field (email, note, etc.) to vCard if it's not already present."""
    existing_values = [line.value for line in vcard.contents.get(field, [])]
    if value not in existing_values:
        line = vcard.add(field)
        line.value = value


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="VCF Email Fixer")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit processing to first N cards (for testing)",
    )
    return parser.parse_args()


def main() -> int:
    """Fix vCards from stdin by injecting known emails."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    processed_vcards = process_vcards(vcards, args, fix_vcard)
    output_vcards(processed_vcards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
