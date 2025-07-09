import sys
from typing import TextIO, Protocol, Any, cast
import logging
import vobject


def setup_logging(verbose: bool = False) -> None:
    """Configure logging to output INFO level messages to stderr."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s %(levelname)s: %(message)s", stream=sys.stderr
    )


class TypedVCard(Protocol):
    fn: Any
    n: Any
    contents: dict[str, list[Any]]
    email: Any
    org: Any
    url: Any

    def add(self, name: str) -> Any: ...
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