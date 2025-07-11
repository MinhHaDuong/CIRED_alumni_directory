#!/usr/bin/env python3
"""
List people without email addresses in their vCard.

This script reads vCard data from stdin and outputs the full names (FN) of people
who don't have any email address in their vCard, or who have only empty email addresses.
This helps identify contacts that need email addresses to be added.

Usage:
    cat cleaned.vcf | python no_email.py
    python no_email.py < cleaned.vcf
"""

import sys
import argparse
import logging
from pathlib import Path

# Add parent directory to path for utils import
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import ingest_vcards, setup_logging, get_vcard_identifier, TypedVCard


def has_email(vcard: TypedVCard) -> bool:
    """
    Check if a vCard has at least one non-empty email address.
    
    Args:
        vcard: The vCard to check
        
    Returns:
        True if the vCard has at least one non-empty email address, False otherwise
    """
    if "email" not in vcard.contents:
        return False
    
    # Check if any email address is non-empty
    for email in vcard.contents["email"]:
        if email.value and email.value.strip():
            return True
    
    return False


def get_people_without_email(vcards: list[TypedVCard]) -> list[str]:
    """
    Get a list of full names (FN) for people without email addresses or with only empty email addresses.
    
    Args:
        vcards: List of vCards to analyze
        
    Returns:
        List of full names of people without email addresses or with only empty email addresses
    """
    people_without_email = []
    
    for vcard in vcards:
        if not has_email(vcard):
            # Try to get the full name (FN)
            if "fn" in vcard.contents and vcard.fn.value.strip():
                people_without_email.append(vcard.fn.value.strip())
            else:
                # Fallback to a generic identifier
                identifier = get_vcard_identifier(vcard)
                people_without_email.append(f"[No FN] {identifier}")
    
    return people_without_email


def main():
    parser = argparse.ArgumentParser(
        description="List people without email addresses or with only empty email addresses from vCard data"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--count-only", 
        action="store_true", 
        help="Only output the count of people without email, not the names"
    )
    parser.add_argument(
        "--sort", 
        action="store_true", 
        help="Sort the output alphabetically"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Read vCards from stdin
    vcards = ingest_vcards(sys.stdin)
    
    if not vcards:
        logging.error("No vCards found in input")
        sys.exit(1)
    
    # Get people without email
    people_without_email = get_people_without_email(vcards)
    
    # Sort if requested
    if args.sort:
        people_without_email.sort()
    
    # Output results
    if args.count_only:
        print(f"{len(people_without_email)}")
    else:
        if people_without_email:
            print(f"People without email addresses or with only empty email addresses ({len(people_without_email)} total):")
            print("=" * 70)
            for name in people_without_email:
                print(name)
        else:
            print("All people have non-empty email addresses.")
    
    # Log summary
    total_people = len(vcards)
    people_with_email = total_people - len(people_without_email)
    logging.info(f"Total people: {total_people}")
    logging.info(f"People with email: {people_with_email}")
    logging.info(f"People without email: {len(people_without_email)}")
    logging.info(f"Email coverage: {people_with_email/total_people*100:.1f}%")


if __name__ == "__main__":
    main()
