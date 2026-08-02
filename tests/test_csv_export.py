import csv

from fl_foreclosed_condos.csv_export import write_csv
from fl_foreclosed_condos.models import CondoListing


def test_write_csv_round_trip(tmp_path):
    listings = [
        CondoListing(address="1 A ST UNIT 2", county="Test County", is_condo=True),
        CondoListing(address="2 B ST", county="Test County", is_condo=False),
    ]
    output_path = tmp_path / "out.csv"

    count = write_csv(listings, str(output_path))
    assert count == 2

    with open(output_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["address"] == "1 A ST UNIT 2"
    assert rows[0]["is_condo"] == "True"
    assert set(rows[0].keys()) == set(CondoListing.csv_fieldnames())
