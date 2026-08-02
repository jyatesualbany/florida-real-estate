from pathlib import Path

import pytest

from fl_foreclosed_condos.condo_filter import looks_like_condo
from fl_foreclosed_condos.sources.zillow import ZillowSource

FIXTURE = Path(__file__).parent / "fixtures" / "sample_zillow_page.html"
BOT_CHECK_FIXTURE = Path(__file__).parent / "fixtures" / "sample_bot_check_page.html"


def test_parse_html_extracts_expected_fields():
    html = FIXTURE.read_text(encoding="utf-8")

    listings = ZillowSource.parse_html(html)

    assert len(listings) == 2
    condo = listings[0]
    assert condo.address == "123 Gulf Blvd Unit 5, Clearwater, FL 33767"
    assert condo.city == "Clearwater"
    assert condo.zip_code == "33767"
    assert condo.opening_bid == "210000"
    assert condo.beds == "1"
    assert condo.baths == "1"
    assert condo.square_footage == "850"
    assert condo.property_type == "CONDO"
    assert condo.source_name == "zillow"
    assert looks_like_condo(condo)

    non_condo = listings[1]
    assert not looks_like_condo(non_condo)


def test_parse_html_raises_on_missing_search_results():
    html = BOT_CHECK_FIXTURE.read_text(encoding="utf-8")

    with pytest.raises(RuntimeError):
        ZillowSource.parse_html(html)
