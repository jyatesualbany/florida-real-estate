from pathlib import Path

from fl_foreclosed_condos.condo_filter import looks_like_condo
from fl_foreclosed_condos.sources.hud_home_store import HudHomeStoreSource

FIXTURE = Path(__file__).parent / "fixtures" / "sample_hud_home_store_page.html"


def test_parse_html_extracts_expected_fields():
    html = FIXTURE.read_text(encoding="utf-8")

    listings = HudHomeStoreSource().parse_html(html)

    assert len(listings) == 2
    condo = listings[0]
    assert condo.case_number == "092-123456"
    assert condo.parcel_id == "HUD-1001"
    assert "UNIT 3C" in condo.address
    assert condo.opening_bid == "$165,000.00"
    assert condo.sale_date == "08/01/2026"
    assert condo.property_type == "HUD REO"
    assert condo.source_name == "HUD Home Store"
    assert looks_like_condo(condo)

    non_condo = listings[1]
    assert not looks_like_condo(non_condo)
