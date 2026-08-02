"""Adapter for HUD Home Store -- HUD's official portal for HUD-owned
(FHA-foreclosed) properties currently for sale.

Unlike the county auction sites in this project (which show *upcoming*
sales -- properties not yet foreclosed) or Zillow/realtor.com (private
companies whose Terms of Service prohibit scraping), HUD Home Store
lists properties HUD has already foreclosed on and now owns, for sale
nationwide. That's a closer match to "foreclosed condo for sale" than
either of those, and it's run by a federal agency rather than a
commercial site with scraping restrictions in its terms -- see
`OFFICIAL_CHANNELS.md` for more on why this is a better-fit source.

*** Still read this before using it. ***

This adapter was NOT verified against a live response in this session
(outbound access to hudhomestore.gov was unavailable while writing it).
Its actual page structure -- plain HTML table, or a modern JS app with
data loaded separately -- was not confirmed. It's implemented the same
configurable, selector-based way as `realforeclose.py` since that's the
safer assumption for a government site whose front-end framework isn't
known; override `selectors` (or switch to the embedded-JSON approach
used by `realtor_com.py` / `zillow.py`, if that turns out to fit better)
after inspecting a real response.
"""

from typing import List, Optional

import requests

from ..models import CondoListing
from .base import ListingSource
from .html_table_parser import parse_auction_rows

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Best-effort default; HUD Home Store's actual search URL/query params
# were not confirmed live -- pass `search_url` explicitly if this
# doesn't match what you find when you inspect the site yourself.
DEFAULT_SEARCH_URL_TEMPLATE = "https://www.hudhomestore.gov/Home/Index?State={state}"

DEFAULT_SELECTORS = {
    "row_selector": "table.propertyList tr, table.searchResults tr, .property-row",
    "case_number_selector": ".caseNumber, .fhaCaseNumber",
    "parcel_id_selector": ".propertyId, .listingId",
    "address_selector": ".propertyAddress, .address",
    "opening_bid_selector": ".listPrice, .price",  # holds list price, not an auction bid
    "sale_date_selector": ".listDate, .onMarketDate",
    "detail_link_selector": "a",
}


class HudHomeStoreSource(ListingSource):
    name = "hud-home-store"

    def __init__(
        self,
        state: str = "FL",
        search_url: Optional[str] = None,
        selectors: Optional[dict] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ):
        self.state = state
        self.search_url = search_url or DEFAULT_SEARCH_URL_TEMPLATE.format(state=state)
        self.selectors = {**DEFAULT_SELECTORS, **(selectors or {})}
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listings(self) -> List[CondoListing]:
        response = self.session.get(
            self.search_url, headers=DEFAULT_HEADERS, timeout=self.timeout
        )
        if response.status_code in (403, 429):
            raise RuntimeError(
                f"{self.search_url} returned {response.status_code}. "
                "That's unexpected for a public federal listings site -- "
                "double-check the search URL is current, and if it still "
                "fails, save the page from your own browser and parse it "
                "with parse_html() instead."
            )
        response.raise_for_status()
        return self.parse_html(response.text)

    def parse_html(self, html: str) -> List[CondoListing]:
        listings = parse_auction_rows(
            html,
            self.selectors,
            county="",
            source_name="HUD Home Store",
            base_url="https://www.hudhomestore.gov",
        )
        for listing in listings:
            if not listing.property_type:
                listing.property_type = "HUD REO"
        return listings
