"""Shared HTML-table parsing used by both the live and manual-import sources.

Most Florida county foreclosure auction sites run on the RealForeclose /
RealAuction platform, which historically renders results as an HTML table
with one row per case. The exact CSS classes vary by county/deployment,
so every selector below is overridable via config/counties.yaml -- treat
the defaults as a documented starting point, not a guarantee, and confirm
them against the live page in your browser before relying on them.
"""

from typing import List, Optional

from bs4 import BeautifulSoup

from ..models import CondoListing

DEFAULT_SELECTORS = {
    "row_selector": "table.itemgridtable tr, table.grid tr, table.searchResultsTable tr",
    "case_number_selector": ".AN_CaseNumber, .caseNumber",
    "parcel_id_selector": ".AN_ParcelID, .parcelId",
    "address_selector": ".AN_PropertyAddress, .propertyAddress",
    "opening_bid_selector": ".AN_OpeningBid, .openingBid, .finalJudgmentAmount",
    "sale_date_selector": ".AN_AuctionDate, .auctionDate, .saleDate",
    "detail_link_selector": "a",
}


def _text(el) -> str:
    return el.get_text(strip=True) if el else ""


def _resolve_url(href: Optional[str], base_url: str) -> str:
    if not href:
        return base_url
    if href.startswith("http://") or href.startswith("https://"):
        return href
    if not base_url:
        return href
    return base_url.rstrip("/") + "/" + href.lstrip("/")


def parse_auction_rows(
    html: str,
    selectors: Optional[dict],
    county: str,
    source_name: str,
    base_url: str = "",
) -> List[CondoListing]:
    """Parse an auction results page into a list of CondoListing records.

    Rows with neither a case number nor an address are skipped, since
    those are almost always header/spacer rows rather than data rows.
    """
    merged_selectors = {**DEFAULT_SELECTORS, **(selectors or {})}
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select(merged_selectors["row_selector"])

    listings = []
    for row in rows:
        case_number = _text(row.select_one(merged_selectors["case_number_selector"]))
        address = _text(row.select_one(merged_selectors["address_selector"]))
        if not case_number and not address:
            continue

        link = row.select_one(merged_selectors["detail_link_selector"])
        href = link.get("href") if link else None

        listings.append(
            CondoListing(
                address=address,
                county=county,
                case_number=case_number,
                parcel_id=_text(row.select_one(merged_selectors["parcel_id_selector"])),
                opening_bid=_text(row.select_one(merged_selectors["opening_bid_selector"])),
                sale_date=_text(row.select_one(merged_selectors["sale_date_selector"])),
                source_name=source_name,
                source_url=_resolve_url(href, base_url),
            )
        )
    return listings
