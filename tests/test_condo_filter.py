from fl_foreclosed_condos.condo_filter import filter_condos, looks_like_condo, tag_condos
from fl_foreclosed_condos.models import CondoListing


def test_looks_like_condo_from_address():
    listing = CondoListing(address="100 OCEAN DR UNIT 4B, MIAMI BEACH, FL 33139")
    assert looks_like_condo(listing)


def test_looks_like_condo_from_legal_description():
    listing = CondoListing(legal_description="OCEAN TOWERS CONDOMINIUM UNIT 12")
    assert looks_like_condo(listing)


def test_not_condo():
    listing = CondoListing(address="200 MAIN ST, MIAMI, FL 33130")
    assert not looks_like_condo(listing)


def test_filter_condos_only_returns_matches():
    condo = CondoListing(address="1 A ST UNIT 2")
    house = CondoListing(address="2 B ST")

    result = filter_condos([condo, house])

    assert result == [condo]
    assert condo.is_condo is True


def test_tag_condos_keeps_all_rows():
    condo = CondoListing(address="1 A ST UNIT 2")
    house = CondoListing(address="2 B ST")

    result = tag_condos([condo, house])

    assert len(result) == 2
    assert condo.is_condo is True
    assert house.is_condo is False
