"""Write CondoListing records to a CSV file."""

import csv

from .models import CondoListing


def write_csv(listings, output_path: str) -> int:
    """Write listings to output_path, returning the number of rows written."""
    fieldnames = CondoListing.csv_fieldnames()
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        count = 0
        for listing in listings:
            writer.writerow(listing.to_row())
            count += 1
    return count
