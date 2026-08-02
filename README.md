# florida-real-estate

A small Python agent that collects **foreclosed condo listings in Florida**
and exports them to a single CSV. Its primary, most reliable source is
public county/court foreclosure records. It can optionally also pull from
HUD Home Store and HomeSteps -- official federal/GSE portals for
properties already foreclosed and owned by HUD/Freddie Mac, no ToS
scraping restriction -- and, best-effort, from realtor.com and Zillow
when those sites don't block it (see below -- they usually do).

## How it works

Florida foreclosure sales are public record, administered by each county's
Clerk of Court. Most counties contract with the **RealForeclose /
RealAuction** platform (`<county>.realforeclose.com`) to run their online
auction calendars. This tool is built around that platform, plus a manual
fallback for counties (or moments) where the live site blocks automated
requests. `--realtor-com` and `--zillow` layer in those two commercial
listing sites the same way -- live if reachable, manual-HTML fallback if
not.

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

## HUD Home Store and HomeSteps (official, no ToS restriction)

`--hud-home-store` and `--homesteps` add two more sources, both worth
using before reaching for realtor.com/Zillow:

- **HUD Home Store** lists properties HUD already foreclosed on (via FHA
  insurance claims) and now owns, for sale nationwide. It's run by a
  federal agency, so there's no scraping-restriction Terms of Service to
  worry about the way there is with Zillow/realtor.com.
- **HomeSteps** is the equivalent for Freddie Mac -- technically a
  government-sponsored enterprise (GSE) under FHFA conservatorship, not
  a federal agency itself, but the same idea: an official REO portal,
  not a commercial listing site.
- Both are arguably a *better conceptual fit* than the county auction
  sites for "foreclosed condo for sale": the county sites show upcoming
  auctions (not yet foreclosed), while these show inventory that's
  already been through foreclosure and is currently for sale.
- **Same caveat as everything unverified in this repo**: outbound access
  to both sites was unavailable while building this, so
  `sources/hud_home_store.py` / `sources/homesteps.py` were not checked
  against a live response. They're implemented with the same
  configurable-CSS-selector approach as the county adapter (see
  `DEFAULT_SELECTORS` in each file) -- confirm and adjust selectors
  after inspecting a real page. `--hud-home-store-html` /
  `--homesteps-html` parse a page you save yourself, same as the other
  manual-HTML fallbacks.
- See [`OFFICIAL_CHANNELS.md`](OFFICIAL_CHANNELS.md) for more on why
  these (and a direct public-records request to a county Clerk) are
  generally the better path versus scraping.

```bash
fl-foreclosed-condos --hud-home-store --homesteps --continue-on-error --output out.csv
fl-foreclosed-condos --hud-home-store-html saved_pages/hud.html --homesteps-html saved_pages/homesteps.html --output out.csv
```

## Realtor.com and Zillow (best-effort, likely blocked)

`--realtor-com` and `--zillow` add those two sites as extra sources on
top of the county public records above. **Read this before turning them
on:**

- **Both sites' Terms of Service prohibit automated scraping.** Zillow's
  in particular is explicit about this and Zillow has a history of
  actively enforcing it (bot-mitigation, and legal action against
  parties that scrape at scale). realtor.com's terms similarly prohibit
  automated data harvesting.
- **These adapters make one ordinary HTTP request each** -- the same
  request your browser would make -- and do nothing to evade bot
  detection, solve CAPTCHAs, or rotate IPs. If the site blocks it, that
  is treated as the correct outcome, not a bug: the adapter raises a
  clear error and stops rather than trying to work around the block.
  Don't extend these adapters with stealth/evasion techniques.
- **In this project's development environment, both sites were
  completely unreachable** -- even a live test against `--realtor-com
  --zillow` failed at the network/proxy level before ever reaching
  either site. So neither adapter's parsing logic could be verified
  against a real response; it's written against how each site has
  historically server-rendered search results into a `<script
  id="__NEXT_DATA__">` JSON blob, which is undocumented and can change
  at any time. Try it from your own machine and expect to need to adjust
  the JSON path in `sources/realtor_com.py` / `sources/zillow.py` after
  inspecting a real response.
- **For occasional personal lookups**, use `--realtor-com-html PATH` /
  `--zillow-html PATH` instead: save the results page from your own
  logged-in browser and it's parsed with the identical logic, no
  automated request involved.
- **For anything beyond that**, use each site's official data channels
  (realtor.com's RDC API / data licensing program; Zillow's Bridge
  Interactive for MLS participants) rather than scraping. See
  [`OFFICIAL_CHANNELS.md`](OFFICIAL_CHANNELS.md) for these plus, more
  importantly, how to get Florida foreclosure data in bulk directly from
  county Clerks via a public records request -- often a better option
  than any of the scraping sources in this repo.

```bash
# Live (likely to fail -- see above):
fl-foreclosed-condos --realtor-com --zillow --continue-on-error --output out.csv

# From a page you saved yourself:
fl-foreclosed-condos --realtor-com-html saved_pages/realtor.html --zillow-html saved_pages/zillow.html --output out.csv
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
- **realtor.com and Zillow are optional, secondary sources with real
  ToS restrictions** -- see the dedicated section above before using
  `--realtor-com` / `--zillow`. County public records remain the primary,
  most reliable source this tool is built around.

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

`--counties` and `--manual-html` are repeatable, and any combination of
`--counties`, `--manual-html`, `--hud-home-store`, `--hud-home-store-html`,
`--homesteps`, `--homesteps-html`, `--realtor-com`, `--realtor-com-html`,
`--zillow`, and `--zillow-html` can be used together in one run (see the
sections above on each source before turning them on). Add
`--continue-on-error` to have a failing source get skipped (with an error
printed to stderr) instead of aborting the whole run, and
`--include-all-property-types` to keep every row instead of condos only.

### Output CSV columns

`address, city, county, zip_code, case_number, parcel_id, sale_date,
opening_bid, property_type, legal_description, beds, baths,
square_footage, year_built, hoa_info, is_condo, source_name, source_url`

Any field a source can't supply is left blank rather than omitted, so
every row has the same columns. Note: `opening_bid` means what it says
for the county auction sources, but for HUD Home Store, HomeSteps,
realtor.com, and Zillow -- which don't have "bids" -- that same column
holds the listing's asking/list price instead.

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
