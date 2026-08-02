"""Live adapter for the RealForeclose / RealAuction network of FL county sites.

Many Florida county clerks contract with RealAuction to run their online
foreclosure sale calendars at <county>.realforeclose.com. These sites are
public record, but a number of them sit behind bot-mitigation (WAF) that
returns 403 to requests that don't look like a real browser session --
this is common on government and vendor-hosted sites and isn't specific
to this tool. If you hit that, use ManualHtmlSource instead: save the
rendered results page from your own logged-in browser and parse it
locally with the exact same selector logic.
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

DEFAULT_PATH = "/index.cfm?zaction=AUCTION&Zmethod=PREVIEW"


class RealForecloseSource(ListingSource):
    name = "realforeclose"

    def __init__(
        self,
        county: str,
        subdomain: str,
        path: str = DEFAULT_PATH,
        selectors: Optional[dict] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ):
        self.county = county
        self.subdomain = subdomain
        self.base_url = f"https://{subdomain}.realforeclose.com"
        self.path = path
        self.selectors = selectors or {}
        self.session = session or requests.Session()
        self.timeout = timeout

    def fetch_listings(self) -> List[CondoListing]:
        url = self.base_url + self.path
        response = self.session.get(url, headers=DEFAULT_HEADERS, timeout=self.timeout)

        if response.status_code == 403:
            raise RuntimeError(
                f"{url} returned 403 Forbidden. This site is likely blocking "
                "automated requests (common for county/vendor sites behind a "
                "WAF). Save the rendered results page from your own browser "
                "and parse it with ManualHtmlSource instead."
            )
        response.raise_for_status()

        return parse_auction_rows(
            response.text,
            self.selectors,
            county=self.county,
            source_name=f"{self.county} Clerk (RealForeclose)",
            base_url=self.base_url,
        )
