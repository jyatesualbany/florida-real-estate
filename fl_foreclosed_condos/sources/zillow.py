"""Adapter for Zillow foreclosure search results.

*** Read this before using it -- more so than any other source here. ***

Zillow's Terms of Use explicitly prohibit automated scraping and data
harvesting, and Zillow actively enforces this with bot-mitigation and has
a history of pursuing legal action against parties that scrape its
listing data at scale. This adapter exists because it was explicitly
requested, is implemented the same "ordinary request, no evasion" way as
every other source in this project, and is expected to fail against
Zillow in most environments -- that failure is the correct, intended
behavior, not a bug to work around.

Do not extend this adapter with stealth techniques (headless-browser
fingerprint spoofing, CAPTCHA solving, IP rotation, etc.) to get past
Zillow's bot protection. If you need Zillow data on an ongoing basis, use
Zillow's official data programs (e.g. Bridge Interactive for MLS
participants) instead of scraping.

In this project's development environment, outbound access to
zillow.com was unavailable, so this adapter's JSON-path assumptions below
were NOT verified against a live response. Zillow has historically
embedded search-page state as JSON in the HTML of its initial
server-rendered response; that structure is undocumented, unversioned,
and changes often. Treat the path used in `parse_html()` as a
best-effort starting point: inspect a real saved response and adjust it
if it doesn't match.
"""

from typing import List, Optional

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

DEFAULT_SEARCH_URL = "https://www.zillow.com/fl/foreclosures/"


class ZillowSource(ListingSource):
    name = "zillow"

    def __init__(
        self,
        search_url: str = DEFAULT_SEARCH_URL,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ):
        self.search_url = search_url
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listings(self) -> List[CondoListing]:
        response = self.session.get(
            self.search_url, headers=DEFAULT_HEADERS, timeout=self.timeout
        )
        if response.status_code in (403, 429):
            raise RuntimeError(
                f"{self.search_url} returned {response.status_code}. "
                "Zillow is blocking this request, almost certainly its "
                "bot-mitigation. This adapter deliberately does not try "
                "to get around that -- save the page from your own "
                "browser and parse it with ZillowSource.parse_html() "
                "instead for occasional personal lookups, or use "
                "Zillow's official data channels for anything more."
            )
        response.raise_for_status()
        return self.parse_html(response.text)

    @staticmethod
    def parse_html(html: str) -> List[CondoListing]:
        data = extract_json_by_script_id(html, "__NEXT_DATA__")
        results = (
            dig(
                data,
                "props",
                "pageProps",
                "searchPageState",
                "cat1",
                "searchResults",
                "listResults",
            )
            if data
            else None
        )

        if not results:
            raise RuntimeError(
                "Could not find recognizable listing data in this page. "
                "This most likely means Zillow served a bot-check/"
                "interstitial page instead of real results, or its page "
                "structure has changed since this adapter was written -- "
                "open the saved HTML in a text editor to check which."
            )

        return [ZillowSource._to_listing(item) for item in results]

    @staticmethod
    def _to_listing(item: dict) -> CondoListing:
        price = item.get("unformattedPrice")
        if price is None:
            price = item.get("price")

        return CondoListing(
            address=item.get("address", "") or "",
            city=item.get("addressCity", "") or "",
            zip_code=str(item.get("addressZipcode", "") or ""),
            opening_bid=str(price) if price is not None else "",
            property_type=item.get("statusType", "") or item.get("homeType", "") or "",
            beds=str(item.get("beds", "") or ""),
            baths=str(item.get("baths", "") or ""),
            square_footage=str(item.get("area", "") or ""),
            source_name="zillow",
            source_url=item.get("detailUrl", "") or "",
        )
