# Data sources and licensing

| Item | Verified source information |
|---|---|
| Dataset | Online Retail II |
| Provider | UCI Machine Learning Repository |
| Creator | Daqing Chen |
| Citation | Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning Repository. DOI: 10.24432/C5CG6D |
| Documentation | https://archive.ics.uci.edu/dataset/502/online%2Bretail%2Bii |
| Direct download | https://archive.ics.uci.edu/static/public/502/online%2Bretail%2Bii.zip |
| Dataset license | CC BY 4.0: https://creativecommons.org/licenses/by/4.0/ |
| Documentation checked | 2026-10-08 |
| Actual retrieval timestamp | Written in UTC to `data/raw/provenance.json` by stage 01 |
| Record coverage | UK-based online retailer; December 2009 through December 2011 |
| Source files | `online_retail_II.xlsx`, two sheets, 1,067,371 source rows |

Acquisition is credential-free: `python main.py --stage 1`. Stage 01 uses bounded HTTP timeouts, retry/backoff, progress logging, atomic download publication, ZIP preflight validation and extraction-size limits. Archive SHA-256 and HTTP metadata are recorded. The publisher does not advertise a checksum here; the initial local digest provides subsequent integrity checks, not independently authenticated content validation. An optional expected SHA-256 can be configured.

Original archive and workbook bytes remain in `data/raw/` and are never changed by cleaning. Existing files are verified before reuse. If source access fails, the stage fails and reports the real URL; it never creates substitute business records. Use an approved network/proxy, then rerun. An externally downloaded archive without provenance is deliberately not silently trusted.

The sheets overlap on 2010-12-01 through 2010-12-09. Exact cross-sheet copies are matched on all eight original business fields plus occurrence number within each sheet. Keep the maximum occurrence count across sheets, and quarantine extra overlap copies with lineage. This is a documented analytical reconciliation assumption, not a publisher-provided line identity. Within-sheet duplicate lines and nonidentical overlap variants remain; report sensitivity separately.

Source limitations: no authoritative line ID, missing customers/descriptions, cancellations and non-sale adjustments, service/product-code mixtures, mutable descriptions, undocumented timestamp timezone, a partial final day/month, and no inventory/cost/marketing data. Missing calendar dates mean no recorded transactions, not proven store closure. The target is derived recorded gross sales, not an existing label, latent demand, or profit. All relational tables are normalized derivatives of this workbook, not three independently sourced datasets.

Code uses the MIT license. Source data and redistributed data-derived materials require attribution to Chen/UCI under CC BY 4.0; MIT does not relicense the dataset.

