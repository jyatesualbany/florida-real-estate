"""Fallback adapter: parse a locally saved auction results page.

Use this when a county's live site blocks automated requests (see
RealForeclose docstring). Workflow: log in to the county site in your own
browser, run the search/date range you want, save the results page (or
copy the page source into a .html file), then point this source at that
file. It reuses the exact same table-parsing logic as the live adapter.
"""

from pathlib import Path
from typing import List, Optional

from ..models import CondoListing
from .base import ListingSource
from .html_table_parser import parse_auction_rows


class ManualHtmlSource(ListingSource):
    name = "manual-html"

    def __init__(
        self,
        county: str,
        html_path: str,
        selectors: Optional[dict] = None,
        source_name: Optional[str] = None,
        base_url: str = "",
    ):
        self.county = county
        self.html_path = html_path
        self.selectors = selectors or {}
        self.source_name = source_name or f"{county} (manual HTML import)"
        self.base_url = base_url

    def fetch_listings(self) -> List[CondoListing]:
        html = Path(self.html_path).read_text(encoding="utf-8", errors="replace")
        return parse_auction_rows(
            html,
            self.selectors,
            county=self.county,
            source_name=self.source_name,
            base_url=self.base_url,
        )
