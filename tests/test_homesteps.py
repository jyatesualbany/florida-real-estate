from pathlib import Path

from fl_foreclosed_condos.condo_filter import looks_like_condo
from fl_foreclosed_condos.sources.homesteps import HomeStepsSource

FIXTURE = Path(__file__).parent / "fixtures" / "sample_homesteps_page.html"


def test_parse_html_extracts_expected_fields():
    html = FIXTURE.read_text(encoding="utf-8")

    listings = HomeStepsSource().parse_html(html)

    assert len(listings) == 2
    condo = listings[0]
    assert condo.case_number == "FM-2001"
    assert "UNIT 8" in condo.address
    assert condo.opening_bid == "$275,000.00"
    assert condo.sale_date == "08/03/2026"
    assert condo.property_type == "Freddie Mac REO"
    assert condo.source_name == "HomeSteps (Freddie Mac)"
    assert looks_like_condo(condo)

    non_condo = listings[1]
    assert not looks_like_condo(non_condo)
