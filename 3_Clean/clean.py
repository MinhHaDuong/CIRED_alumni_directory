#!/usr/bin/env python3
"""
VCF Cleaner
-----------
This script reads VCF (vCard) data from standard input, cleans each contact card
using the vobject library, and outputs the cleaned VCF data to standard output.

Features:
- Drops entries with obsolete emails (ending with @centre-cired.fr)
- Drops entries with URLs that return HTTP 404
- Logs all cleaning actions
- Supports custom email domain filtering via --filter-domain
- Configurable timeout for URL checking

Usage examples:
    python clean.py < input.vcf > output.vcf
    python clean.py --filter-domain old-company.com --timeout 5 < input.vcf > output.vcf
"""

import sys
import os
import argparse
import logging
import re
import requests
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ingest_vcards, TypedVCard, setup_logging, get_vcard_identifier


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="VCF Cleaner")
    parser.add_argument(
        "--filter-domain",
        default="centre-cired.fr",
        help="Email domain to filter out (default: centre-cired.fr)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=3,
        help="Timeout for URL checking in seconds (default: 3)",
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


# --- Cleaning ---

def is_obsolete_email(email_value: str, filter_domain: str) -> bool:
    """Return True if the email contains the obsolete domain."""
    email_str = str(email_value).lower()
    # Handle both direct email addresses and mailto: URLs
    pattern = rf"(@|mailto:[^\s@]*@){re.escape(filter_domain.lower())}"
    return bool(re.search(pattern, email_str))


def find_urls(text: str) -> list[str]:
    """Extract all URLs from text and return as a list."""
    return re.findall(r'https?://[^\s;,\'"<>]+', str(text))


def url_is_unavailable(url: str, timeout: int = 3) -> bool:
    """
    Return True if the given URL is unavailable (404, DNS error, connection error, etc).
    Logs the reason for unavailability.
    """
    try:
        url = url.rstrip(".,;")
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logging.warning(f"Invalid URL format: {url}")
            return True
        resp = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers={"User-Agent": "VCF-Cleaner/1.0"},
        )
        if resp.status_code == 404:
            logging.info(f"URL {url} returned 404")
            return True
        return False
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout checking URL {url}")
        return True
    except requests.exceptions.RequestException as e:
        logging.warning(f"Error checking URL {url}: {e}")
        return True
    except Exception as e:
        logging.warning(f"Unexpected error checking URL {url}: {e}")
        return True


# --- Card Processing ---

def process_vcard(vcard: TypedVCard, args: argparse.Namespace) -> str:
    """
    Process a single vCard object:
    - Removes obsolete emails (logs removal, but never drops the card)
    - Removes URLs that are unavailable (logs removal)

    Returns the serialized vCard (never None).
    """
    identifier = get_vcard_identifier(vcard)
    logging.info(f"Processing '{identifier}'")

    logging.debug("Entry to process:")
    entry_text = vcard.serialize()
    logging.debug(f"\n{entry_text.strip()}\n")

    # Remove obsolete emails (but keep the card)
    if "email" in vcard.contents:
        emails_to_remove = []
        for email in vcard.contents["email"]:
            if is_obsolete_email(email.value, args.filter_domain):
                logging.info(
                    f"Removing obsolete email from '{identifier}': {email.value}"
                )
                emails_to_remove.append(email)
        for email in emails_to_remove:
            vcard.contents["email"].remove(email)
        if not vcard.contents["email"]:
            del vcard.contents["email"]

    # Remove unavailable URLs (but keep the card)
    if "url" in vcard.contents:
        urls_to_remove = []
        for url_field in vcard.contents["url"]:
            urls = find_urls(url_field.value)
            for url in urls:
                if url_is_unavailable(url, args.timeout):
                    logging.info(f"Removing unavailable URL from '{identifier}': {url}")
                    urls_to_remove.append(url_field)
                    break  # If any URL in this field is 404, remove the whole field
        for url_field in urls_to_remove:
            vcard.contents["url"].remove(url_field)
        if not vcard.contents["url"]:
            del vcard.contents["url"]

    logging.debug("Cleaned entry:")
    entry_text = vcard.serialize()
    logging.debug(f"\n{entry_text.strip()}\n")

    return entry_text



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
            result = process_vcard(vcard, args)
            if not result:
                raise RuntimeError("process_vcard returned no result for a vCard")
        except Exception as e:
            identifier = get_vcard_identifier(vcard)
            logging.error(
                f"Error processing vCard '{identifier}': {e}. Passing original."
            )
            result = vcard.serialize()
        finally:
            print(result.rstrip("\n") + "\n\n", end="")
            processed_count += 1
    logging.info(f"Processing complete: {processed_count} processed")


def main() -> int:
    """Clean and enrich vCards from stdin."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    process_vcards(vcards, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
