"""Heuristics for deciding whether a foreclosure listing is a condo unit.

Public foreclosure auction records rarely carry a clean "property type"
field. The legal description, and sometimes the address itself, is the
most reliable signal (e.g. "UNIT 4B", "A CONDOMINIUM", "PH-12"). These
heuristics are deliberately conservative-but-inclusive: they're meant to
narrow a large auction list down to a "likely condo" subset for a human
to review, not to be a legal determination of property type.
"""

import re

from .models import CondoListing

_CONDO_PATTERNS = [
    r"\bcondo(?:minium)?s?\b",
    r"\bunit\s*#?\s*[\w-]+",
    r"\bapt\.?\s*#?\s*[\w-]+",
    r"\bph\s*[-#]?\s*\d+\b",  # penthouse
    r"\bbldg\.?\s*[\w-]+",
]

_CONDO_RE = re.compile("|".join(_CONDO_PATTERNS), re.IGNORECASE)


def looks_like_condo(listing: CondoListing) -> bool:
    """Return True if any available field suggests this is a condo unit."""
    haystack = " ".join(
        part
        for part in (
            listing.property_type,
            listing.legal_description,
            listing.address,
        )
        if part
    )
    return bool(_CONDO_RE.search(haystack))


def filter_condos(listings):
    """Return only the listings that look like condos, with is_condo set."""
    result = []
    for listing in listings:
        listing.is_condo = looks_like_condo(listing)
        if listing.is_condo:
            result.append(listing)
    return result


def tag_condos(listings):
    """Set is_condo on every listing (in place) without dropping any rows."""
    for listing in listings:
        listing.is_condo = looks_like_condo(listing)
    return listings
