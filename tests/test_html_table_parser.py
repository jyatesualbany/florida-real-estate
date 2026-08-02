from pathlib import Path

from fl_foreclosed_condos.sources.html_table_parser import parse_auction_rows
from fl_foreclosed_condos.sources.manual_html import ManualHtmlSource

FIXTURE = Path(__file__).parent / "fixtures" / "sample_auction_page.html"


def test_parse_auction_rows_extracts_expected_fields():
    html = FIXTURE.read_text(encoding="utf-8")

    listings = parse_auction_rows(
        html,
        selectors=None,
        county="Miami-Dade County",
        source_name="Miami-Dade Clerk (RealForeclose)",
        base_url="https://miamidade.realforeclose.com",
    )

    assert len(listings) == 2

    first = listings[0]
    assert first.case_number == "2025-CA-001234"
    assert first.parcel_id == "12-34-56-789"
    assert "UNIT 4B" in first.address
    assert first.opening_bid == "$185,000.00"
    assert first.sale_date == "09/15/2026"
    assert first.source_url == "https://miamidade.realforeclose.com/index.cfm?zaction=AUCTION&Zmethod=DETAIL&AI=1001"


def test_manual_html_source_uses_same_parser():
    source = ManualHtmlSource(
        county="Miami-Dade County",
        html_path=str(FIXTURE),
        base_url="https://miamidade.realforeclose.com",
    )

    listings = source.fetch_listings()

    assert len(listings) == 2
    assert listings[0].source_name == "Miami-Dade County (manual HTML import)"
