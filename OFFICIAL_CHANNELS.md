# Official / legitimate channels for foreclosure and listing data

Foreclosure sale data is Florida public record. That means, unlike Zillow
or realtor.com, there's a real, sanctioned way to get it in bulk that
doesn't involve scraping the auction vendor's web page at all -- it's
usually faster and more complete too. This doc lays out those channels.
Nothing below was verified against a live site in this session (outbound
web access was unavailable while writing it -- see the main README's
"Important limitations" section for why); treat URLs and specifics here
as a starting point to confirm, not a guarantee.

## 1. Public records requests under Florida's Public Records Law

Foreclosure case records -- filings, sale results, lis pendens -- are
court records maintained by each county's **Clerk of the Circuit Court &
Comptroller**, and are public record under **Chapter 119, Florida
Statutes**. Practically, this means:

- You can ask a Clerk's office directly for an electronic export (CSV/
  Excel) of foreclosure sale data for a date range, instead of scraping
  the HTML rendering of that same data on their auction vendor's site.
- Look for a **"Public Records Request"** page or a **"Custodian of
  Public Records"** contact on the Clerk's *own* site -- that's a
  different domain from the auction vendor subdomain this project's
  `config/counties.yaml` uses (e.g. the Clerk's site is typically
  something like `<county>clerk.org` / `<county>clerk.gov`, separate
  from `<county>.realforeclose.com`).
- Under F.S. 119.07(4), a Clerk can charge a "special service charge"
  for requests that need extensive IT/programming time, but a
  straightforward date-range export is often low-cost or free.
- Frame the request specifically: e.g. "an electronic export of
  foreclosure final judgment / sale records for [date range], including
  case number, parcel ID, property address, and sale/opening bid
  amount." Clerks respond better to a concrete ask than "all your data."

## 2. Auction platform vendors may offer direct data access

Most Florida county clerks contract their foreclosure auctions out to a
vendor rather than running the calendar themselves:

- **RealAuction** (the `realforeclose.com` network) runs auctions for
  the majority of counties this project's config targets.
- **LienHub** (Grant Street / SRI) and **Bid4Assets** run auctions or tax
  deed sales for some counties instead.

These vendors sometimes offer subscriber, bulk-export, or API access for
licensed users (title companies, investors) separate from the public
search page. Worth asking the Clerk's office (or the vendor directly)
whether that option exists for your use case, rather than scraping the
public page. This is exactly the kind of access this project's adapters
should switch to first, if it's available -- reading a clean CSV/JSON
export is simpler and more reliable than parsing HTML selectors that can
change without notice (see `sources/realforeclose.py`'s adapter, which
this would replace or supplement per county).

## 3. Statewide resource for finding the right office

**Florida Court Clerks & Comptrollers (FCCC)**, the statewide association
of Clerks of Court, is a reasonable starting point for finding the right
department/contact at a specific county's office if their own site isn't
clear about who handles public records requests.

## 4. Some counties publish sale lists directly, no vendor involved

A number of Clerks post a downloadable foreclosure sales list (PDF or
CSV) directly on their own site under something like "Reports,"
"Foreclosure Sales," or "Sale Lists" -- separate from the interactive
RealForeclose-style auction calendar and much easier to parse or import
directly (no HTML scraping needed at all). Check for this before
assuming the vendor's page is the only option for a given county.

## 5. Suggested starting point: highest-volume counties

If you're going to make a handful of records requests to start, these are
Florida's largest counties by population/foreclosure volume and a
reasonable place to begin: Miami-Dade, Broward, Palm Beach, Hillsborough,
Orange, Pinellas, Duval, and Lee. (Already present in
`config/counties.yaml` as the RealForeclose-based live/manual sources.)

## 6. HUD Home Store and HomeSteps -- already implemented in this repo

These two are already wired in as `--hud-home-store` / `--homesteps`
(see `sources/hud_home_store.py` / `sources/homesteps.py`):

- **HUD Home Store** -- HUD's official portal for HUD-owned properties
  (foreclosed via FHA insurance claims), for sale nationwide. Run by a
  federal agency, so no scraping-restriction ToS to work around.
- **HomeSteps** -- the equivalent for Freddie Mac. Not literally federal
  (Freddie Mac is a GSE under FHFA conservatorship), but the same idea:
  an official REO portal rather than a private commercial listing site.

Both are arguably a better fit for "foreclosed condo for sale" than the
county auction calendars -- those show *upcoming* auctions of
not-yet-foreclosed properties, while HUD Home Store/HomeSteps show
inventory that's already been through foreclosure and is currently for
sale. Same disclaimer as the rest of this project applies: their page
structure wasn't confirmed live, so treat the current selectors as a
starting point to verify.

## 7. Zillow and realtor.com: the only real "official" options

For completeness, since this project also has best-effort adapters for
these two sites (see `sources/realtor_com.py` / `sources/zillow.py`):

- **Zillow's Bridge Interactive** is their actual data feed, but it's
  gated to MLS/broker industry participants -- not self-serve for an
  individual project.
- **realtor.com's RDC API / data licensing program** is similarly a
  business relationship, not a signup form.
- Third-party "Zillow/realtor.com API" products (e.g. on RapidAPI) are
  almost always unofficial scrapers themselves -- using one doesn't
  remove the ToS problem, it just outsources it.

In practice, for this project, county public records (channels 1-4
above) are the legitimate, no-compromise path to bulk data. Treat
realtor.com/Zillow as occasional, manual-fallback sources only.

## Extending this project once you have a real data channel

If a county provides a bulk CSV/JSON export or API, the cleanest way to
use it here is a new small adapter under `fl_foreclosed_condos/sources/`
that reads that export format directly and returns `CondoListing`
records -- no HTML parsing, no CSS selectors to keep in sync with a
vendor's page. Register it the same way `RealForecloseSource` is
registered in `registry.py`.
