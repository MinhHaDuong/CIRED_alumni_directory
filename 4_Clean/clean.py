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
import time
import random
import requests
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ingest_vcards, TypedVCard, VCardLine, setup_logging, get_vcard_identifier, process_vcards, output_vcards

# --- Card Processing ---

def clean(vcard: TypedVCard, args: argparse.Namespace) -> TypedVCard:
    """
    Process a single vCard object:
    - Removes obsolete emails (logs removal, but never drops the card)
    - Removes URLs that are unavailable (logs removal)

    Returns the modified vCard (never None).
    """
    logging.info(f"Processing '{get_vcard_identifier(vcard)}'")
    logging.debug(f"Entry to clean:\n{vcard.serialize().strip()}\n")

    remove_obsolete_emails(vcard, args.filter_domain)
    remove_dead_urls(vcard, args.timeout)

    logging.debug(f"Cleaned entry:\n{vcard.serialize().strip()}\n")
    return vcard


# --- Email Processing ---

def remove_obsolete_emails(vcard: TypedVCard, filter_domain: str) -> None:
    """
    Remove obsolete emails from a vCard (but keep the card).

    Args:
        vcard: The vCard to clean
        filter_domain: Domain to filter out
        identifier: Human-readable identifier for logging
    """
    if "email" not in vcard.contents:
        return

    emails_to_remove: list[VCardLine] = []
    for email in vcard.contents["email"]:
        if is_obsolete_email(email.value, filter_domain):
            logging.info(f"Removing obsolete email': {email.value}")
            emails_to_remove.append(email)

    for email in emails_to_remove:
        vcard.contents["email"].remove(email)

    if not vcard.contents["email"]:
        del vcard.contents["email"]


def is_obsolete_email(email_value: str, filter_domain: str) -> bool:
    """Return True if the email contains the obsolete domain."""
    email_str = str(email_value).lower()
    # Handle both direct email addresses and mailto: URLs
    pattern = rf"(@|mailto:[^\s@]*@){re.escape(filter_domain.lower())}"
    return bool(re.search(pattern, email_str))

# --- URL Processing ---

def remove_dead_urls(vcard: TypedVCard, timeout: int) -> None:
    """
    Remove dead URLs from a vCard (but keep the card).

    Args:
        vcard: The vCard to clean
        timeout: Timeout for URL checking in seconds
        identifier: Human-readable identifier for logging
    """
    if "url" not in vcard.contents:
        return

    urls_to_remove: list[VCardLine] = []
    for url_field in vcard.contents["url"]:
        urls = find_urls(url_field.value)
        for url in urls:
            if not url_available(url, timeout):
                logging.info(f"Removing unavailable URL: {url}")
                urls_to_remove.append(url_field)
                break

    for url_field in urls_to_remove:
        vcard.contents["url"].remove(url_field)

    if not vcard.contents["url"]:
        del vcard.contents["url"]



def find_urls(text: str) -> list[str]:
    """Extract all URLs from text and return as a list."""
    return re.findall(r'https?://[^\s;,\'"<>]+', str(text))


def url_available(url: str, timeout: int = 3) -> bool:
    """
    Return True if the given URL is available (accessible).
    Logs the reason for unavailability when URL is not accessible.
    """
    if "user=abc" in url:
        logging.debug(f"Removing fake URL: {url}")
        return False

    if "1234-5678" in url:
        logging.debug(f"Removing fake URL: {url}")
        return False

    if "linkedin.com" in url:
        logging.warning(f"Skipping uncheckable LinkedIn page: {url}")
        return True

    try:
        url = url.rstrip(".,;")
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            logging.warning(f"Invalid URL format: {url}")
            return False
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/114.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        response = requests.head(
            url,
            allow_redirects=True,
            timeout=timeout,
            headers=headers,
        )
        if response.status_code == 405: # If HEAD is not allowed, fall back to GET
            logging.debug(f"HEAD request not allowed for {url}, falling back to GET")
            time.sleep(random.uniform(1.5, 3.0))  # reduce bot detection
            response = requests.get(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers=headers,
            )
        if response.status_code == 200:
            return True
        if response.status_code == 404:
            logging.info(f"URL {url} returned 404")
            return False
        if response.status_code == 999:
            logging.info(f"URL {url} returned 999, indicating a rate limit or bot block (Linkedin)")
            return True
        return False
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout checking URL {url}")
        return False
    except requests.exceptions.ConnectionError as e:
        # Handle DNS resolution failures and connection errors
        error_msg = str(e)
        if "NameResolutionError" in error_msg or "Name or service not known" in error_msg:
            logging.info(f"Domain not found: {url}")
        elif "Connection refused" in error_msg:
            logging.info(f"Connection refused: {url}")
        else:
            logging.info(f"Connection error for {url}: {e}")
        return False
    except requests.exceptions.RequestException as e:
        logging.info(f"Request error checking URL {url}: {e}")
        return False
    except Exception as e:
        logging.warning(f"Unexpected error checking URL {url}: {e}")
        return False

# --- Command line interface ---

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


def main() -> int:
    """Clean vCards from stdin."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    processed_vcards = process_vcards(vcards, args, clean)
    output_vcards(processed_vcards)
    return 0


if __name__ == "__main__":
    sys.exit(main())
