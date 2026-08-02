"""Loads config/counties.yaml and builds the right source adapter per county."""

from pathlib import Path
from typing import Optional

import yaml

from .sources.base import ListingSource
from .sources.realforeclose import RealForecloseSource

CONFIG_PATH = Path(__file__).resolve().parent / "config" / "counties.yaml"

_SOURCE_BUILDERS = {}


def _build_realforeclose(county_key: str, entry: dict, selectors: dict) -> RealForecloseSource:
    return RealForecloseSource(
        county=entry.get("display_name", county_key),
        subdomain=entry["subdomain"],
        selectors=selectors,
    )


_SOURCE_BUILDERS["realforeclose"] = _build_realforeclose


def load_config(path: Optional[str] = None) -> dict:
    config_path = Path(path) if path else CONFIG_PATH
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def known_counties(config: Optional[dict] = None) -> list:
    config = config if config is not None else load_config()
    return sorted(config.get("counties", {}).keys())


def build_source(county_key: str, config: Optional[dict] = None) -> ListingSource:
    """Build the live source adapter configured for a given county key."""
    config = config if config is not None else load_config()
    counties = config.get("counties", {})
    if county_key not in counties:
        raise KeyError(
            f"Unknown county '{county_key}'. Known counties: "
            f"{', '.join(sorted(counties)) or '(none configured)'}"
        )

    entry = counties[county_key]
    platform = entry.get("platform")
    builder = _SOURCE_BUILDERS.get(platform)
    if builder is None:
        raise NotImplementedError(
            f"No source adapter implemented for platform '{platform}' "
            f"(county '{county_key}')"
        )

    selectors = {**config.get("selectors", {}), **entry.get("selectors", {})}
    return builder(county_key, entry, selectors)
