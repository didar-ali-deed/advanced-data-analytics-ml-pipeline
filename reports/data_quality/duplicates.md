# Duplicate review

{'rows': 1067371, 'exact_business_row_repeats': 34335, 'repeated_invoice_rows': 1013743, 'duplicate_line_ids': 0, 'policy': 'Retain ambiguous repeated business lines; source row is the unique key.', 'near_repeat_rows': 67250}

Invoice IDs are one-to-many, not line primary keys. Identical lines may represent repeated product entries; without an authoritative line ID there is no evidence to delete within-sheet repeats. Stage 07 separately reconciles exact cross-sheet copies in the overlapping source date windows, retaining maximum per-sheet multiplicity and quarantining extra copies. Near-repeat groups ignore description and timestamp and are review candidates only. A separate sensitivity query measures the effect of deduplicating business rows.