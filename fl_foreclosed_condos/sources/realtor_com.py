"""Adapter for realtor.com foreclosure search results.

*** Read this before using it. ***

realtor.com's Terms of Use prohibit automated scraping / data harvesting
from the site. This adapter makes a single, ordinary HTTP GET -- the same
request a browser would make -- with no attempt to evade bot detection,
CAPTCHAs, or rate limits, and no headless-browser fingerprint spoofing.
If realtor.com blocks it, that is the correct, intended outcome, not a
bug to route around: fall back to `parse_html()` against a page saved
from your own browser for occasional personal lookups, or use
realtor.com's official data channels (their RDC API / data licensing
program) for anything beyond that.

In this project's development environment, outbound access to
realtor.com was unavailable, so this adapter's JSON-path assumptions
below were NOT verified against a live response. realtor.com's search
pages have historically server-rendered their initial results into a
`<script id="__NEXT_DATA__">` JSON blob for client-side hydration -- that
structure is undocumented, unversioned, and can change at any time.
Treat the path used in `parse_html()` as a best-effort starting point:
inspect a real saved response and adjust it if it doesn't match.
"""

from typing import List, Optional
from urllib.parse import quote

import requests

from ..models import CondoListing
from .base import ListingSource
from .embedded_json import dig, extract_json_by_script_id

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Best-effort default search URL for FL condo foreclosures; realtor.com's
# URL scheme for filtered searches has changed over the years and was not
# confirmed live -- pass `search_url` explicitly if this doesn't match.
DEFAULT_SEARCH_URL_TEMPLATE = (
    "https://www.realtor.com/realestateandhomes-search/{location}"
    "/type-condo/show-foreclosure"
)


class RealtorComSource(ListingSource):
    name = "realtor.com"

    def __init__(
        self,
        location: str = "Florida",
        search_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ):
        self.location = location
        self.search_url = search_url or DEFAULT_SEARCH_URL_TEMPLATE.format(
            location=quote(location)
        )
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listings(self) -> List[CondoListing]:
        response = self.session.get(
            self.search_url, headers=DEFAULT_HEADERS, timeout=self.timeout
        )
        if response.status_code in (403, 429):
            raise RuntimeError(
                f"{self.search_url} returned {response.status_code}. "
                "realtor.com is likely blocking this as an automated "
                "request. This adapter does not attempt to evade bot "
                "detection -- save the page from your own browser and "
                "parse it with RealtorComSource.parse_html() instead, or "
                "use realtor.com's official data channels for anything "
                "beyond occasional personal lookups."
            )
        response.raise_for_status()
        return self.parse_html(response.text)

    @staticmethod
    def parse_html(html: str) -> List[CondoListing]:
        data = extract_json_by_script_id(html, "__NEXT_DATA__")
        if data is None:
            raise RuntimeError(
                "Could not find the expected __NEXT_DATA__ JSON block in "
                "this page. Either realtor.com's page structure has "
                "changed since this adapter was written, or this is a "
                "bot-check/interstitial page rather than real search "
                "results -- open the saved HTML in a text editor to check "
                "which."
            )

        results = (
            dig(data, "props", "pageProps", "searchResults", "home_search", "results")
            or dig(data, "props", "pageProps", "properties")
            or []
        )

        return [RealtorComSource._to_listing(item) for item in results]

    @staticmethod
    def _to_listing(item: dict) -> CondoListing:
        location = item.get("location") or {}
        address = location.get("address") or {}
        description = item.get("description") or {}
        price = item.get("list_price")

        return CondoListing(
            address=address.get("line", "") or "",
            city=address.get("city", "") or "",
            county=address.get("county", "") or "",
            zip_code=address.get("postal_code", "") or "",
            opening_bid=str(price) if price is not None else "",
            property_type=description.get("type", "") or "",
            beds=str(description.get("beds", "") or ""),
            baths=str(description.get("baths", "") or ""),
            square_footage=str(description.get("sqft", "") or ""),
            year_built=str(description.get("year_built", "") or ""),
            source_name="realtor.com",
            source_url=item.get("href") or item.get("permalink") or "",
        )
