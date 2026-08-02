from pathlib import Path

import pytest

from fl_foreclosed_condos.condo_filter import looks_like_condo
from fl_foreclosed_condos.sources.realtor_com import RealtorComSource

FIXTURE = Path(__file__).parent / "fixtures" / "sample_realtor_com_page.html"
BOT_CHECK_FIXTURE = Path(__file__).parent / "fixtures" / "sample_bot_check_page.html"


def test_parse_html_extracts_expected_fields():
    html = FIXTURE.read_text(encoding="utf-8")

    listings = RealtorComSource.parse_html(html)

    assert len(listings) == 2
    condo = listings[0]
    assert condo.address == "500 BRICKELL AVE UNIT 2100"
    assert condo.city == "MIAMI"
    assert condo.county == "Miami-Dade"
    assert condo.zip_code == "33131"
    assert condo.opening_bid == "350000"
    assert condo.beds == "2"
    assert condo.baths == "2"
    assert condo.square_footage == "1200"
    assert condo.year_built == "2005"
    assert condo.source_name == "realtor.com"
    assert looks_like_condo(condo)

    non_condo = listings[1]
    assert not looks_like_condo(non_condo)


def test_parse_html_raises_on_missing_next_data():
    html = BOT_CHECK_FIXTURE.read_text(encoding="utf-8")

    with pytest.raises(RuntimeError):
        RealtorComSource.parse_html(html)
