# Coffee processing review — November 4, 2026

All three explicit Coffee Processing listings in the current export were reviewed. Current official-site verification is blocked by the cloud network allowlist. These are unresolved operations, not confirmed green processors or roasters.

| Business | Explicit product state in export | Actual processing operation |
| --- | --- | --- |
| Coffee Works, LLC | Roasted coffee | Unknown |
| Eberine Enterprises, Inc. / Euro Coffee | Coffee, decaffeinated coffee, pods; green/roasted not specified | Unknown |
| F. Gavina & Sons., Inc. | Roasted coffee, pods | Unknown |

A roasted product listing does not prove that the business performs roasting in-house. Likewise, decaffeination and pods do not reveal the process represented by a generic Coffee Processing label. Green coffee denotes an unroasted product; it does not establish cherry processing or green-bean production.

The model now separates explicit Coffee (Green) product businesses from an unsequenced gray processing_unspecified lane. Only explicit product labels determine green/roasted product stages. Unknown processing creates no stage-based edges, although a business can still participate through another explicitly supported product role. The general Coffee category remains the requested modeling category and does not prove downstream market position.

Sources: existing ccof_members.csv, member URLs in assessments.csv and its SHA-256 snapshot identifier. Website probes of ccof.org, www.coffeeworks.com and www.eurocoffee.com encountered proxy CONNECT 403 policy denials. No website content was reviewed and no direct confirmation was obtained. The environment draft adds ccof.org, coffeeworks.com and eurocoffee.com while preserving prior allowed domains; it was not published or applied.

After access is active, inspect each directory profile and official website for named input form (cherries, parchment, green beans or roasted beans), operations (pulping, fermentation, drying, hulling, roasting, grinding, extraction, decaffeination or packaging), output form and supporting statement/date. Keep the operation unknown if the source remains ambiguous. Gavina's official site must be identified from an authoritative directory/company source rather than guessed.
