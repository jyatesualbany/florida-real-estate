"""Data model for a single foreclosure listing."""

from dataclasses import dataclass, fields


@dataclass
class CondoListing:
    """Normalized record for one foreclosure listing.

    Fields map directly to CSV columns. Any field a given source can't
    supply is left as an empty string rather than omitted, so every row
    in the output CSV has a consistent shape.
    """

    address: str = ""
    city: str = ""
    county: str = ""
    zip_code: str = ""
    case_number: str = ""
    parcel_id: str = ""
    sale_date: str = ""
    opening_bid: str = ""
    property_type: str = ""
    legal_description: str = ""
    beds: str = ""
    baths: str = ""
    square_footage: str = ""
    year_built: str = ""
    hoa_info: str = ""
    is_condo: bool = False
    source_name: str = ""
    source_url: str = ""

    @staticmethod
    def csv_fieldnames() -> list:
        return [f.name for f in fields(CondoListing)]

    def to_row(self) -> dict:
        return {f.name: getattr(self, f.name) for f in fields(self)}
