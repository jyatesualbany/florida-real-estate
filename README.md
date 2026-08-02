# florida-real-estate

A small Python agent that collects **foreclosed condo listings in Florida**
from public county/court records and exports them to a single CSV.

## How it works

Florida foreclosure sales are public record, administered by each county's
Clerk of Court. Most counties contract with the **RealForeclose /
RealAuction** platform (`<county>.realforeclose.com`) to run their online
auction calendars. This tool is built around that platform, plus a manual
fallback for counties (or moments) where the live site blocks automated
requests.

```
County auction page (live or saved HTML)
        |
        v
  html_table_parser  --------> CondoListing records (one per case)
        |
        v
  condo_filter  (keeps rows whose address/legal description look like a condo)
        |
        v
  [optional] ArcGIS enrichment  (fills in year_built / sqft / etc. from the
             county Property Appraiser's public parcel data, when available)
        |
        v
  csv_export  ---------------> florida_foreclosed_condos.csv
```

## Important limitations (read this first)

- **Auction records rarely include beds/baths/sqft/year built/HOA
  info.** The Clerk of Court's sale record has case number, parcel ID,
  address, opening bid/judgment amount, and sale date -- that's it. Those
  extra fields come from the county Property Appraiser instead, which is
  why there's a separate, optional enrichment step (see below). Expect
  `beds`, `baths`, and `hoa_info` to be blank for most rows even with
  enrichment turned on -- HOA details in particular are almost never in
  public parcel data.
- **Some county sites block automated requests.** RealForeclose-network
  sites (and many other government/vendor sites) sit behind bot
  mitigation (a WAF) that can return `403 Forbidden` to non-browser
  traffic, especially from cloud/data-center IPs. If `--counties` hits
  this, use `--manual-html` instead: open the results page in your own
  browser, save it, and parse the saved file with the exact same logic.
- **Selectors are best-effort defaults, not verified against every
  live site.** `config/counties.yaml` lists counties believed to run on
  RealForeclose, with default CSS selectors matching that platform's
  common markup. Before trusting output for a given county, open its
  live page, check the selectors still match (browser devtools > right
  click a value > Inspect), and override them per-county in the YAML if
  not.
- **Condo detection is a heuristic**, not a legal determination. It
  flags rows whose address or legal description contains things like
  "UNIT", "CONDOMINIUM", "APT", or "PH-<number>". Review the output
  before treating it as authoritative, and use `--include-all-property-types`
  if you'd rather see everything with the `is_condo` column left for you
  to judge.
- **Respect each site's Terms of Service and `robots.txt`**, and keep
  request rates low. This tool does not do anything to evade bot
  detection -- when a site blocks it, the intended response is to fall
  back to the manual-HTML workflow, not to try to get around the block.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

This installs the `fl-foreclosed-condos` console script and the
`fl_foreclosed_condos` package (see `pyproject.toml` for dependencies).

## Usage

List the counties this tool currently knows about:

```bash
fl-foreclosed-condos --list-counties
```

Fetch live from one or more counties:

```bash
fl-foreclosed-condos --counties miami-dade broward --output florida_foreclosed_condos.csv
```

If a county's site blocks the request, save its results page from your
browser and parse that instead:

```bash
fl-foreclosed-condos --manual-html miami-dade=saved_pages/miami_dade.html --output florida_foreclosed_condos.csv
```

Both flags are repeatable and can be combined in a single run. Add
`--continue-on-error` to have a failing county get skipped (with an error
printed to stderr) instead of aborting the whole run, and
`--include-all-property-types` to keep every row instead of condos only.

### Output CSV columns

`address, city, county, zip_code, case_number, parcel_id, sale_date,
opening_bid, property_type, legal_description, beds, baths,
square_footage, year_built, hoa_info, is_condo, source_name, source_url`

Any field a source can't supply is left blank rather than omitted, so
every row has the same columns.

## Enriching with property details (optional)

`fl_foreclosed_condos/sources/enrichment/arcgis.py` provides
`ArcGISParcelEnricher`, which looks up a parcel ID against a county
Property Appraiser's public ArcGIS REST parcel layer (a normal JSON API,
generally not subject to the bot-blocking the auction sites have) and
fills in whichever of `year_built` / `square_footage` / `beds` / `baths`
/ `hoa_info` that layer happens to expose.

To use it for a county:

1. Find that county's ArcGIS REST Services Directory (search
   `"<county> property appraiser arcgis rest services"`, or browse
   `https://<their-gis-host>/arcgis/rest/services` for the parcel layer).
2. Note the layer's `/query` endpoint URL and its field names.
3. Build a field map and enrich after fetching listings:

```python
from fl_foreclosed_condos.sources.enrichment import ArcGISParcelEnricher

enricher = ArcGISParcelEnricher(
    query_url="https://gis.example-county.gov/arcgis/rest/services/Parcels/MapServer/0/query",
    field_map={
        "year_built": "YR_BLT",
        "square_footage": "TOT_LVG_AREA",
    },
    parcel_field="PARCELID",
)
listings = enricher.enrich_all(listings)
```

This isn't wired into the CLI (the field map is too county-specific to
default sensibly), but the two pieces compose easily in a short script.

## Adding a county

Add an entry to `fl_foreclosed_condos/config/counties.yaml` under
`counties:` with a `display_name`, `platform` (currently only
`realforeclose` is implemented), and its `subdomain`. Override
`selectors` per-county if that county's markup differs from the shared
defaults at the bottom of the file.

To support a platform other than RealForeclose, add a new adapter under
`fl_foreclosed_condos/sources/` implementing `ListingSource.fetch_listings`,
and register a builder for it in `registry.py`'s `_SOURCE_BUILDERS`.

## Development

```bash
pip install -e ".[dev]"  # or: pip install -r requirements-dev.txt
pytest
```

Tests run entirely offline against a fixture HTML page in
`tests/fixtures/` -- no network access needed.
