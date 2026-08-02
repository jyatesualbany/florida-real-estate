import csv
from pathlib import Path

from fl_foreclosed_condos.cli import run

FIXTURE = Path(__file__).parent / "fixtures" / "sample_auction_page.html"
REALTOR_COM_FIXTURE = Path(__file__).parent / "fixtures" / "sample_realtor_com_page.html"
ZILLOW_FIXTURE = Path(__file__).parent / "fixtures" / "sample_zillow_page.html"


def test_cli_manual_html_condos_only(tmp_path):
    output_path = tmp_path / "out.csv"

    exit_code = run(
        [
            "--manual-html",
            f"miami-dade={FIXTURE}",
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0

    with open(output_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1  # only the condo unit row is kept by default
    assert "UNIT 4B" in rows[0]["address"]


def test_cli_manual_html_include_all_property_types(tmp_path):
    output_path = tmp_path / "out.csv"

    exit_code = run(
        [
            "--manual-html",
            f"miami-dade={FIXTURE}",
            "--output",
            str(output_path),
            "--include-all-property-types",
        ]
    )

    assert exit_code == 0

    with open(output_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2


def test_cli_realtor_com_and_zillow_html_combine_with_counties(tmp_path):
    output_path = tmp_path / "out.csv"

    exit_code = run(
        [
            "--manual-html",
            f"miami-dade={FIXTURE}",
            "--realtor-com-html",
            str(REALTOR_COM_FIXTURE),
            "--zillow-html",
            str(ZILLOW_FIXTURE),
            "--output",
            str(output_path),
        ]
    )

    assert exit_code == 0

    with open(output_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # One condo from each of the three sources; the non-condo rows in the
    # realtor.com/Zillow fixtures are filtered out by default.
    sources = {row["source_name"] for row in rows}
    assert len(rows) == 3
    assert "realtor.com" in sources
    assert "zillow" in sources


def test_cli_list_counties(capsys):
    exit_code = run(["--list-counties"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "miami-dade" in output
