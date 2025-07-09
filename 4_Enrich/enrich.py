#!/usr/bin/env python3
"""
VCF Enricher
-----------
This script reads VCF (vCard) data from standard input, processes each contact card
using the vobject library, and outputs the enriched VCF data to standard output.

Features:
- Logs all actions and what would be sent to the LLM
- Optionally calls an LLM for enrichment if --exec is passed

Usage examples:
    python enrich.py < cleaned.vcf > enriched.vcf
    python enrich.py --exec < cleaned.vcf > enriched.vcf
"""

import sys
import os
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ingest_vcards, TypedVCard, setup_logging, get_vcard_identifier


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="VCF Enricher")
    parser.add_argument(
        "--exec", action="store_true", help="Actually call the LLM for enrichment"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit processing to first N cards (for testing)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    return parser.parse_args()


# --- Enrichment ---


def find_email(vcard: TypedVCard) -> TypedVCard:
    """
    Search for an email address in the vCard, and return it if found.
    """
    logging.debug("Searching for email in vCard")
    assert vcard, "vCard cannot be empty"

    if hasattr(vcard, 'email'):
        logging.debug(f"Has email: {vcard.email.value}.")
        return vcard

    logging.info("Email not found, extracting...")

    # TODO: Implement actual email search logic here

    vcard.add('email')
    vcard.email.value = "<extracted_email>"
    return vcard


# --- Card Processing ---



def enrich(vcard: TypedVCard, args: argparse.Namespace) -> TypedVCard:
    """
    Process a single vCard object:
    - Logs what would be sent to the LLM
    - If exec_mode is True, calls LLM for enrichment

    Returns the serialized vCard (never None).
    """
    identifier = get_vcard_identifier(vcard)
    logging.info(f"Enriching '{identifier}'")
    logging.debug(f"\n{vcard.serialize().strip()}")

    enriched = find_email(vcard)
    return enriched


def process_vcards(vcards: list[TypedVCard], args: argparse.Namespace) -> None:
    """
    Process a list of vCard objects and print results to stdout.
    Applies limit if specified in args. Never drops a card: if processing fails, outputs the original.
    Uses a finally clause to always print a result.
    """
    if not vcards:
        logging.warning("No valid vCards found in input")
        return
    cards_to_process = vcards
    if args.limit:
        cards_to_process = vcards[: args.limit]
        logging.info(f"Processing limited to first {len(cards_to_process)} cards")
    processed_count = 0
    for vcard in cards_to_process:
        result = None
        try:
            result = enrich(vcard, args)
            processed_count += 1
        except Exception as e:
            identifier = get_vcard_identifier(vcard)
            logging.error(
                f"Error processing vCard '{identifier}': {e}. Passing original."
            )
            result = vcard
        finally:
            if not result:
                raise RuntimeError("process_vcard returned no result for a vCard")
            print(result.serialize().rstrip("\n") + "\n\n", end="")
    logging.info(f"Processing complete: {processed_count} processed")


def main() -> int:
    """Enrich vCards from stdin."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    process_vcards(vcards, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
