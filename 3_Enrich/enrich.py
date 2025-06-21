#!/usr/bin/env python3
"""
VCF Enricher Filter
------------------
This script reads VCF (vCard) data from standard input, processes each contact card
using the vobject library, and outputs the filtered/enriched VCF data to standard output.

Features:
- Drops entries with obsolete emails (ending with @centre-cired.fr)
- Drops entries with URLs that return HTTP 404
- Logs all actions and what would be sent to the LLM
- Optionally calls an LLM for enrichment if --exec is passed
- Supports custom email domain filtering via --filter-domain
- Configurable timeout for URL checking

Usage examples:
    python enrich.py < input.vcf > output.vcf
    python enrich.py --exec < input.vcf > output.vcf
    python enrich.py --filter-domain old-company.com --timeout 5 < input.vcf > output.vcf
"""

import sys
import argparse
import logging
import re
import requests
import vobject
from urllib.parse import urlparse


# --- Logging setup ---
def setup_logging(verbose=False):
    """Configure logging to output INFO level messages to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stderr
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="VCF Enricher Filter")
    parser.add_argument(
        "--exec", action="store_true", help="Actually call the LLM for enrichment"
    )
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
def is_obsolete_email(email_value, filter_domain):
    """Return True if the email contains the obsolete domain."""
    email_str = str(email_value).lower()
    # Handle both direct email addresses and mailto: URLs
    pattern = rf"(@|mailto:[^\s@]*@){re.escape(filter_domain.lower())}"
    return bool(re.search(pattern, email_str))


def find_urls(text):
    """Extract all URLs from text and return as a list."""
    return re.findall(r'https?://[^\s;,\'"<>]+', str(text))


def url_is_unavailable(url, timeout=3):
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
            headers={"User-Agent": "VCF-Enricher/1.0"},
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


# --- Enrichment ---


def call_llm(entry_text):
    """
    Placeholder for LLM enrichment.

    In a real implementation, this would:
    1. Send the vCard data to an LLM service
    2. Ask for enrichment (e.g., standardized formatting, additional info)
    3. Parse and validate the response
    4. Return the enriched vCard data

    For now, returns the entry unchanged.
    """
    logging.info("LLM enrichment called (placeholder)")
    # TODO: Implement actual LLM integration
    return entry_text


# --- Card Processing ---


def get_vcard_identifier(vcard):
    """Extract a human-readable identifier from a vCard for logging."""
    # Try to get name, email, or org for identification
    if "fn" in vcard.contents:
        return str(vcard.fn.value)
    elif "email" in vcard.contents:
        return str(vcard.email.value)
    elif "org" in vcard.contents:
        return str(vcard.org.value)
    else:
        return "Unknown contact"


def process_vcard(vcard, args):
    """
    Process a single vCard object:
    - Removes obsolete emails (logs removal, but never drops the card)
    - Removes URLs that are unavailable (logs removal)
    - Logs what would be sent to the LLM
    - If exec_mode is True, calls LLM for enrichment

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

    if args.exec:
        enriched = call_llm(entry_text)
        return enriched
    else:
        return entry_text


def ingest_vcards(stdin):
    """
    Read VCF data from stdin and return a list of vCard objects.
    """
    vcf_text = stdin.read()
    if not vcf_text.strip():
        logging.error("No VCF data provided on stdin")
        return []
    vcards = list(vobject.readComponents(vcf_text))
    logging.info(f"Read {len(vcards)} vCard(s)")
    return vcards


def process_vcards(vcards, args):
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
                raise RuntimeError("process_vcf_entry returned no result for a vCard")
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


def main():
    """Clean and enrich vCards from stdin."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    process_vcards(vcards, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
