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
from openai import OpenAI
import vobject

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import ingest_vcards, TypedVCard, setup_logging, get_vcard_identifier, process_vcards, output_vcards

MODEL = "gpt-4.1-mini"  # Use a smaller model for cost efficiency and speed
# MODEL = "gpt-4.1"  # Uncomment to use the full model

# --- Card Processing ---

prompt = """
# Task: Find information about a colleague affiliated or formerly with CIRED/CNRS, France.

Search the internet to find their current professional contact details, based on public sources.

# Instructions:

- Search across Google, HAL, ORCID, LinkedIn, Google Scholar and other public sources.
- Strive to get at least email and current affiliation.
- Once you have the email or affiliation, launch a second, more precise websearch.
- Provide the most recent and professional affiliation and contact details.
- DO NOT invent or guess missing information.
- Verify the URLs are reachable and correspond to the person.
- Return only the VCard format, without any additional text, explanation or enclosing tags.
- DO NOT INCLUDE any line with missing, incomplete, or not publicly available information.

# Target format (VCard):

BEGIN:VCARD
FN: [Full Name]
EMAIL: [Professional email]
ORG: [Current institution]
TITLE: [Current title or role]
URL;TYPE=LINKEDIN: [LinkedIn profile]
URL;TYPE=ORCID: [ORCID profile]
URL;TYPE=SCHOLAR: [Google Scholar profile]
URL;TYPE=INSTITUTIONAL: [Official lab or institutional profile]
URL;TYPE=HOME: [Personal or professional homepage]
END:VCARD

# CIRED alumni to update:
"""


def enrich(vcard: TypedVCard, args: argparse.Namespace) -> TypedVCard:
    """
    Process a single vCard object:
    - Logs what would be sent to the LLM
    - If exec is True, calls LLM for enrichment

    Returns the serialized vCard (never None).
    """
    assert vcard, "vCard cannot be empty"
    logging.info(f"Enriching '{get_vcard_identifier(vcard)}'")
    logging.debug(f"\n{vcard.serialize().strip()}")

    name = vcard.fn.value if hasattr(vcard, 'fn') else None
    if not name:
        logging.warning("vCard has no FN (full name), skipping.")
        return vcard

    logging.debug(f"Enriching:\n{vcard.serialize().strip()}\n")

    full_prompt = prompt + f"\nFN: {name}\n"

    if args.exec:
        response = call_llm(full_prompt)
        parsed_vcard = enrich_vcard_from_response(vcard, response)
        logging.debug(f"Enriched vCard:\n{parsed_vcard.serialize().strip()}\n")
        return parsed_vcard or vcard
    else:
        logging.info(f"[DRY RUN] Would call LLM with:\n{full_prompt}")
        return vcard


def call_llm(prompt: str) -> str:
    """
    Ask the LLM to search and enrich a person's information.
    """
    logging.debug(f"Calling LLM with prompt:\n{prompt}")

    client = OpenAI()

    response = client.responses.create(
        model=MODEL,
        tools=[{"type": "web_search_preview"}],
        input=prompt
    )

    logging.debug(response.output_text)

    result = clean_response(response.output_text)

    return result

def clean_response(response: str) -> str:
    """
    Clean the LLM response to ensure it is in valid vCard format.
    Removes any leading or trailing whitespace and ensures it starts with BEGIN:VCARD.
    """
    response = response.strip()
    if not response.startswith("BEGIN:VCARD"):
        logging.error("LLM response does not start with BEGIN:VCARD")
        logging.error(f"\n{response[:100]}\n")  # Log first 100 chars for context
        return ""
    if not response.endswith("END:VCARD"):
        logging.error("LLM response does not end with END:VCARD")
        logging.error(f"\n{response[:100]}\n")  # Log first 100 chars for context
        return ""
    kill_patterns = ["FN:", ": [", "protected]", "not available", "not publicly available", "not found", "not reachable"]
    # Remove the lines with these patterns
    lines = response.splitlines()
    lines = [line for line in lines if not any(pattern in line for pattern in kill_patterns)]
    response = "\n".join(lines)
    return response


def enrich_vcard_from_response(vcard: TypedVCard, response: str) -> TypedVCard:
    """
    Parse the LLM response and update the vCard with new information.
    Returns the vCard, updated or not if parsing failed.
    """
    try:
        if "BEGIN:VCARD" in response and "END:VCARD" in response:
            start = response.find("BEGIN:VCARD")
            end = response.find("END:VCARD") + len("END:VCARD")
            vcard_content = response[start:end]
        else:
            logging.warning("LLM response does not contain valid vCard format.")
            return vcard

        logging.debug(f"Contents to merge:\n{vcard_content}")

        new_vcard = vobject.readOne(vcard_content)
        for prop in new_vcard.contents:
            if prop in vcard.contents:
                vcard.contents[prop].extend(new_vcard.contents[prop])
            else:
                vcard.add(prop)
                vcard.contents[prop] = new_vcard.contents[prop]
        return vcard

    except Exception as e:
        logging.error(f"Failed to parse LLM response: {e}")
        logging.debug(f"Response content: {response}")
        return vcard

# --- Command-line Interface ---

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


def main() -> int:
    """Enrich vCards from stdin."""
    args = parse_args()
    setup_logging(args.verbose)
    vcards = ingest_vcards(sys.stdin)
    processed_vcards = process_vcards(vcards, args, enrich)
    output_vcards(processed_vcards)
    return 0

if __name__ == "__main__":
    sys.exit(main())
