import sys
import argparse
from typing import TextIO, Protocol, Optional, cast, Literal, Callable
import logging
import vobject

def setup_logging(verbose: bool = False) -> None:
    """Configure logging to output INFO level messages to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stderr
    )


class VCardLine(Protocol):
    name: str                            # e.g. "EMAIL"
    value: str                           # e.g. "john@example.com"
    params: dict[str, list[str]]         # e.g. {"TYPE": ["work"]}
    group: Optional[str]                 # e.g. "item1" for item1.EMAIL
    singletonparams: dict[str, str]      # legacy support

    def serialize(self) -> str: ...


class TypedVCard(Protocol):
    """Represents a vCard object.

    A valid VCARD **must have** exactly one `fn` and one `n` field.
    For the rest, canonical access is through the `contents` dictionary.
    A card can have 0 or more: email, org, title, url, ... fields.
    The corresponding attribute defined below is a shortcut to the first occurrence of the field.
        vcard.email.value               # string value
        vcard.email.params.get("TYPE")  # e.g. ['WORK']
    """
    name: Literal["VCARD"]
    fn: VCardLine
    n: VCardLine
    contents: dict[str, list[VCardLine]]
    email: VCardLine
    org: VCardLine
    title: VCardLine
    url: VCardLine

    def add(self, name: str) -> VCardLine: ...
    def serialize(self) -> str: ...


def ingest_vcards(stdin: TextIO) -> list[TypedVCard]:
    """
    Read VCF data from stdin and return a list of vCard objects.
    """
    vcf_text = stdin.read()
    if not vcf_text.strip():
        logging.error("No VCF data provided on stdin")
        return []
    vcards = cast(list[TypedVCard], list(vobject.readComponents(vcf_text)))    # type: ignore
    logging.info(f"Read {len(vcards)} vCard(s)")
    return vcards


def get_vcard_identifier(vcard: TypedVCard) -> str:
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


def process_vcards(
    vcards: list[TypedVCard],
    args: argparse.Namespace,
    processor_func: Callable[[TypedVCard, argparse.Namespace], TypedVCard]
) -> list[TypedVCard]:
    """
    Generic function to process a list of vCard objects.

    Args:
        vcards: List of vCards to process
        args: Command-line arguments with limit support
        processor_func: Function that processes a single vCard (clean, enrich, etc.)

    Returns:
        List of processed TypedVCard objects.
        Never drops a card: if processing fails, returns the original.
    """
    if not vcards:
        logging.warning("No valid vCards found in input")
        return []

    cards_to_process = vcards[: args.limit] if args.limit else vcards
    if args.limit:
        logging.info(f"Processing limited to first {len(cards_to_process)} cards")

    processed_cards: list[TypedVCard] = []
    processed_count = 0
    
    for vcard in cards_to_process:
        result = None
        try:
            result = processor_func(vcard, args)
            if not result:
                raise RuntimeError("Processor function returned no result for a vCard")
        except Exception as e:
            identifier = get_vcard_identifier(vcard)
            logging.error(f"Error processing vCard '{identifier}': {e}. Passing original.")
            result = vcard
        finally:
            processed_cards.append(result or vcard)
            processed_count += 1

    logging.info(f"Processing complete: {processed_count} processed")
    return processed_cards


def output_vcards(vcards: list[TypedVCard]) -> None:
    """
    Output a list of vCards to stdout in VCF format.
    
    Args:
        vcards: List of vCards to output
    """
    for vcard in vcards:
        output = vcard.serialize()
        print(output.rstrip("\n") + "\n\n", end="")