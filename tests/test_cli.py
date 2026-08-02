import csv
from pathlib import Path

from fl_foreclosed_condos.cli import run

FIXTURE = Path(__file__).parent / "fixtures" / "sample_auction_page.html"


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


def test_cli_list_counties(capsys):
    exit_code = run(["--list-counties"])

    assert exit_code == 0
    output = capsys.readouterr().out
    assert "miami-dade" in output
