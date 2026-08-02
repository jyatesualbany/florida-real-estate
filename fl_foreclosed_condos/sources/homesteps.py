"""Adapter for HomeSteps -- Freddie Mac's portal for Freddie Mac-owned
(foreclosed) properties currently for sale.

A note on what this actually is: Freddie Mac is a **government-sponsored
enterprise (GSE)** under FHFA conservatorship, not a federal agency
itself -- so unlike HUD Home Store, this isn't strictly a "federal data
source." It's included alongside HUD Home Store because it's the same
kind of thing in practice: an official, publicly-run REO (foreclosed,
now-owned-by-the-institution) listing portal with no ToS scraping
restriction, rather than a private commercial site like Zillow or
realtor.com.

*** Still read this before using it. ***

This adapter was NOT verified against a live response in this session
(outbound access to homesteps.com was unavailable while writing it). Its
actual page structure was not confirmed. Implemented the same
configurable, selector-based way as `realforeclose.py` and
`hud_home_store.py` -- override `selectors` after inspecting a real
response.
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

# Best-effort default; HomeSteps' actual search URL/query params were
# not confirmed live -- pass `search_url` explicitly if this doesn't
# match what you find when you inspect the site yourself.
DEFAULT_SEARCH_URL_TEMPLATE = "https://www.homesteps.com/hstp/Buyer/search?state={state}"

DEFAULT_SELECTORS = {
    "row_selector": "table.propertyList tr, table.searchResults tr, .property-row",
    "case_number_selector": ".listingNumber, .propertyId",
    "parcel_id_selector": ".listingNumber, .propertyId",
    "address_selector": ".propertyAddress, .address",
    "opening_bid_selector": ".listPrice, .price",  # holds list price, not an auction bid
    "sale_date_selector": ".listDate, .onMarketDate",
    "detail_link_selector": "a",
}


class HomeStepsSource(ListingSource):
    name = "homesteps"

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
                "Double-check the search URL is current, and if it still "
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
            source_name="HomeSteps (Freddie Mac)",
            base_url="https://www.homesteps.com",
        )
        for listing in listings:
            if not listing.property_type:
                listing.property_type = "Freddie Mac REO"
        return listings
