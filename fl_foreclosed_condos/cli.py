"""CLI entry point for collecting Florida foreclosed condo listings.

Examples:
    python -m fl_foreclosed_condos.cli --list-counties

    python -m fl_foreclosed_condos.cli \\
        --counties miami-dade broward \\
        --output florida_foreclosed_condos.csv

    python -m fl_foreclosed_condos.cli \\
        --manual-html miami-dade=saved_pages/miami_dade_results.html \\
        --output florida_foreclosed_condos.csv

    python -m fl_foreclosed_condos.cli \\
        --counties miami-dade --realtor-com --zillow \\
        --continue-on-error --output florida_foreclosed_condos.csv
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from .condo_filter import filter_condos, tag_condos
from .csv_export import write_csv
from .registry import build_source, known_counties, load_config
from .sources.manual_html import ManualHtmlSource
from .sources.realtor_com import RealtorComSource
from .sources.zillow import ZillowSource


def _split_manual_html_arg(raw: str) -> Tuple[str, str]:
    if "=" not in raw:
        raise argparse.ArgumentTypeError(f"--manual-html expects COUNTY=PATH, got '{raw}'")
    county, path = raw.split("=", 1)
    return county, path


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Collect Florida foreclosed condo listings from public county "
            "records into a CSV."
        )
    )
    parser.add_argument(
        "--counties",
        nargs="+",
        default=[],
        metavar="COUNTY",
        help=(
            "County keys to fetch live (see --list-counties). Requires "
            "network access to <county>.realforeclose.com and may be "
            "blocked by that site's bot protection -- see --manual-html."
        ),
    )
    parser.add_argument(
        "--manual-html",
        nargs="+",
        default=[],
        metavar="COUNTY=PATH",
        help=(
            "Parse a locally saved auction results page instead of "
            "fetching live, e.g. miami-dade=saved.html. Repeatable."
        ),
    )
    parser.add_argument(
        "--realtor-com",
        action="store_true",
        help=(
            "Also search realtor.com live for FL condo foreclosures. "
            "realtor.com's Terms of Use prohibit automated scraping and "
            "the site runs bot-mitigation this tool does not try to "
            "evade -- expect this to often fail. See README. Use "
            "--realtor-com-html to parse a page saved from your browser "
            "instead."
        ),
    )
    parser.add_argument(
        "--realtor-com-html",
        metavar="PATH",
        help="Parse a realtor.com results page saved from your browser instead of fetching live.",
    )
    parser.add_argument(
        "--zillow",
        action="store_true",
        help=(
            "Also search Zillow live for FL foreclosures. Zillow's Terms "
            "of Use explicitly prohibit scraping and the site actively "
            "enforces this -- this tool does not attempt to evade its "
            "bot protection, so expect this to often fail. See README. "
            "Use --zillow-html to parse a page saved from your browser "
            "instead."
        ),
    )
    parser.add_argument(
        "--zillow-html",
        metavar="PATH",
        help="Parse a Zillow results page saved from your browser instead of fetching live.",
    )
    parser.add_argument(
        "--output",
        default="florida_foreclosed_condos.csv",
        help="Output CSV path (default: florida_foreclosed_condos.csv)",
    )
    parser.add_argument(
        "--include-all-property-types",
        action="store_true",
        help=(
            "Include every fetched listing in the output, not just ones "
            "that look like condos. The is_condo column is still set "
            "either way."
        ),
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help=(
            "If a source fails (e.g. blocked, network error), skip it and "
            "continue instead of aborting the whole run."
        ),
    )
    parser.add_argument(
        "--list-counties",
        action="store_true",
        help="Print the known county keys from config/counties.yaml and exit.",
    )
    return parser


def run(argv: Optional[List[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    config = load_config()

    if args.list_counties:
        for county in known_counties(config):
            print(county)
        return 0

    if not any(
        [
            args.counties,
            args.manual_html,
            args.realtor_com,
            args.realtor_com_html,
            args.zillow,
            args.zillow_html,
        ]
    ):
        parser.error(
            "Specify at least one source: --counties, --manual-html, "
            "--realtor-com, --realtor-com-html, --zillow, or "
            "--zillow-html (or use --list-counties)."
        )

    listings = []
    had_errors = False

    for county_key in args.counties:
        try:
            source = build_source(county_key, config)
            fetched = source.fetch_listings()
            print(f"[{county_key}] fetched {len(fetched)} listings", file=sys.stderr)
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[{county_key}] ERROR: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    for raw in args.manual_html:
        county_key, path = _split_manual_html_arg(raw)
        try:
            source = ManualHtmlSource(county=county_key, html_path=path)
            fetched = source.fetch_listings()
            print(f"[{county_key}] parsed {len(fetched)} listings from {path}", file=sys.stderr)
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[{county_key}] ERROR parsing {path}: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    if args.realtor_com:
        try:
            fetched = RealtorComSource().fetch_listings()
            print(f"[realtor.com] fetched {len(fetched)} listings", file=sys.stderr)
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[realtor.com] ERROR: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    if args.realtor_com_html:
        try:
            html = Path(args.realtor_com_html).read_text(encoding="utf-8", errors="replace")
            fetched = RealtorComSource.parse_html(html)
            print(
                f"[realtor.com] parsed {len(fetched)} listings from {args.realtor_com_html}",
                file=sys.stderr,
            )
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[realtor.com] ERROR parsing {args.realtor_com_html}: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    if args.zillow:
        try:
            fetched = ZillowSource().fetch_listings()
            print(f"[zillow] fetched {len(fetched)} listings", file=sys.stderr)
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[zillow] ERROR: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    if args.zillow_html:
        try:
            html = Path(args.zillow_html).read_text(encoding="utf-8", errors="replace")
            fetched = ZillowSource.parse_html(html)
            print(
                f"[zillow] parsed {len(fetched)} listings from {args.zillow_html}",
                file=sys.stderr,
            )
            listings.extend(fetched)
        except Exception as exc:  # noqa: BLE001 - report and keep going or abort
            had_errors = True
            print(f"[zillow] ERROR parsing {args.zillow_html}: {exc}", file=sys.stderr)
            if not args.continue_on_error:
                return 1

    if args.include_all_property_types:
        output_listings = tag_condos(listings)
    else:
        output_listings = filter_condos(listings)

    count = write_csv(output_listings, args.output)
    print(f"Wrote {count} listings to {args.output}", file=sys.stderr)

    return 1 if had_errors else 0


if __name__ == "__main__":
    sys.exit(run())
