"""Best-effort property-detail enrichment via a county's public ArcGIS layer.

Foreclosure auction records (case number, parcel ID, opening bid, sale
date) almost never include beds/baths/square footage/year built/HOA info
-- that data lives with the county Property Appraiser, not the Clerk of
Court. Many FL property appraisers publish their parcel layer as a public
Esri ArcGIS REST FeatureServer/MapServer, which is a normal JSON API (not
scraping) and generally not bot-blocked the way the auction sites are.

To use this for a county:
1. Find that county's ArcGIS REST Services Directory (search
   "<county> property appraiser arcgis rest services", or browse
   https://<their-gis-host>/arcgis/rest/services and locate the parcel
   layer).
2. Open that layer and note its field names (the directory page lists
   them), then note the /query endpoint URL, e.g.
   https://gis.example-county.gov/arcgis/rest/services/Parcels/MapServer/0/query
3. Build a field_map from our field names to theirs, e.g.
   {"year_built": "YR_BLT", "square_footage": "TOT_LVG_AREA"}.

Expect year_built and square_footage to be the fields most often present.
Beds/baths are inconsistently modeled across counties, and HOA info is
essentially never in public parcel data -- those will often stay blank.
"""

from typing import Iterable, List, Optional

import requests

from ...models import CondoListing


def _escape_sql_literal(value: str) -> str:
    return value.replace("'", "''")


class ArcGISParcelEnricher:
    name = "arcgis-parcel"

    def __init__(
        self,
        query_url: str,
        field_map: dict,
        parcel_field: str = "PARCELID",
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ):
        self.query_url = query_url
        self.field_map = field_map
        self.parcel_field = parcel_field
        self.session = session or requests.Session()
        self.timeout = timeout

    def _lookup(self, parcel_id: str) -> dict:
        params = {
            "where": f"{self.parcel_field}='{_escape_sql_literal(parcel_id)}'",
            "outFields": ",".join(self.field_map.values()) or "*",
            "f": "json",
            "returnGeometry": "false",
        }
        response = self.session.get(self.query_url, params=params, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        features = data.get("features") or []
        return features[0].get("attributes", {}) if features else {}

    def enrich(self, listing: CondoListing) -> CondoListing:
        if not listing.parcel_id:
            return listing
        try:
            attrs = self._lookup(listing.parcel_id)
        except (requests.RequestException, ValueError):
            return listing

        for our_field, their_field in self.field_map.items():
            value = attrs.get(their_field)
            if value not in (None, ""):
                setattr(listing, our_field, str(value))
        return listing

    def enrich_all(self, listings: Iterable[CondoListing]) -> List[CondoListing]:
        return [self.enrich(listing) for listing in listings]
