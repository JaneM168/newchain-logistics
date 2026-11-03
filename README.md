# Newchain logistics: commodity networks

Build stage-constrained nearest-neighbor networks from the CCOF directory export.

## Run

Python 3.12 is recommended. From the repository root:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python logistics/commodity_graph.py -k 5
.venv/bin/python logistics/render_commodity_graph.py
.venv/bin/python -m unittest discover -s logistics -v
```

Open [the interactive visualization](visualizations/network.html) in a browser. Select coffee or pecan, switch between stage and geographic views, search business names and select a node for details. The HTML is self-contained. [PNG](visualizations/commodity_networks.png) and [SVG](visualizations/commodity_networks.svg) exports are also included. Regenerate with `-k` to choose the number of next-stage neighbors; `--input` and `--out` override the input CSV and interactive/data output directory. The static renderer reads the default `visualizations` directory.

## Model

- Coffee: **crop grower (green) → processing / green coffee (amber) → roasted coffee (brown) → general coffee products/services (purple)**.
- Pecan: **crop grower (green) → pecan products/services (purple)**.

Every business URL is one node. Businesses with multiple roles appear in multiple stage columns but retain one ID. For each source role, connect to up to K other located businesses in the immediately following stage. Self-links and stage skipping are excluded. Missing stages remain empty. Links are candidate spatial relationships, not observed transactions. Generic Coffee products/services is a requested modeling stage, not evidence of downstream position.

Distances are haversine kilometers between **approximate city representative points**, not verified farms, street geocodes or driving distances. Coordinates come from GeoNames via geonamescache 3.0.1, using US city/state matches and the bundled minimum-population-500 dataset. Ambiguous and missing locations remain unresolved. Businesses in the same city can have zero distance; ties sort by URL. There is no maximum-distance cutoff, so a connected component is not necessarily a local cluster. Attribution: [GeoNames](https://www.geonames.org/), CC BY.

## Source schema and roles

The CSV has two row widths. The 18-field rows contain the first 11 header fields followed by acres, chapter, location, certification, crops, products/services and sales methods. Its header omits acres and mislabels the trailing fields. The loader normalizes these positions explicitly without editing the source. The eight 17-field data rows have uncertain commodity-category provenance; no commodity roles are inferred from them. Relevant ambiguous labels enter the review export.

Exact semicolon-delimited labels determine roles:

| Role | Source field and label |
| --- | --- |
| Coffee grower | Crops: Coffee |
| Processing / green coffee | Products/services: Coffee Processing or Coffee (Green) |
| Roasted | Products/services: Coffee (Roasted) |
| General coffee | Products/services: Coffee |
| Pecan grower | Crops: Pecan or Pecans |
| Pecan product/service | Products/services: Pecan or Pecans |

Coffee drinks, pods and decaffeinated coffee alone do not establish these roles. A business name or generic Crops certification does not prove it grows a specific commodity. Handler nodes are businesses, not farms. Directory addresses may be offices or mailing addresses rather than production sites.

## Current coverage at K=5

Coffee: 26 businesses, 24 city-located, 94 stage links. Role counts overlap: 1 grower, 5 processing/green, 16 roasted and 11 general coffee. Two additional coffee-related businesses fall outside the requested stage labels and appear in the review CSV. The graph contains one 24-business connected component plus two isolated businesses when direction is ignored.

Pecan: 6 products/services businesses, 4 city-located and no explicit pecan crop records. No grower-to-product links are fabricated; all six are isolated. All coffee and pecan businesses selected from this export have California addresses. That does not establish where their commodities were grown or comprehensive California coverage.

Outputs include per-commodity JSON, node/edge/review CSVs, combined graphs.json and the interactive HTML. JSON includes missing-stage and unlocated-source gaps. The algorithm is quadratic and appropriate for this small export; use a spatial index for larger datasets.

## Next data needs

Verify physical production sites, geocode street addresses with match provenance, and add travel-time or distance cutoffs for local logistics clusters. Expand beyond organic via producer directories, cooperatives, food hubs and extension networks, deduplicating sites and preserving provenance. Sales data is not included: join future sales by stable business/site ID, time period, commodity, volume, units, destination and temperature needs. These coffee and pecan networks alone do not establish demand for refrigeration or quantify logistics impact.

The existing scraper is unchanged. Its CLI can be inspected with `python ccof_scraper.py --help`; live scraping is not validated. Follow its terms/robots and identifying-contact guidance before collecting new records.
