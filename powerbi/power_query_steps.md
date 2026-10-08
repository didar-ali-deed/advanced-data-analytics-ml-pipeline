# Power BI Desktop import

1. Run `python main.py --all`. Confirm `data/powerbi/export_manifest.json` reports zero foreign-key violations.
2. In Power BI Desktop select **Get data → Text/CSV**. Open each of `dim_product.csv`, `dim_customer.csv`, `dim_country.csv`, `dim_date.csv`, `fact_sales.csv`, and `forecast_evaluation.csv`. Choose UTF-8 (65001), comma delimiter, then **Transform Data**.
3. Remove automatically inferred **Changed Type** steps before configuring identifiers. Set `line_id`, `invoice_id`, `product_id`, `customer_id`, description and country to **Text**. This preserves leading zeros and UNKNOWN.
4. Set `country_id`, quantity, hour, year, month_number and weekday to **Whole Number**. Set `date` to **Date** and invoice_date to **Date/Time**, using English (United Kingdom) locale when prompted. Exported dates are ISO, not US month/day strings.
5. Set monetary values and model outputs to **Decimal Number**. Preserve source precision during reconciliation; apply currency formatting in the model. Convert `is_sale`, `is_cancellation`, `is_adjustment`, and `ambiguous_duplicate` to **True/False**.
6. Keep all rows. Do not remove repeated invoice IDs, drop UNKNOWN customers, replace cancellation values, or deduplicate lines in Power Query. Cleaning already recorded these decisions and validated the line key.
7. Close & Apply. Create the five single-direction relationships in [data_model.md](data_model.md); disable undesired auto-detected relationships. Mark dim_date as the date table.
8. Create the measures in [dax_measures.md](dax_measures.md). Format money as GBP and ratios as percentages.
9. Build the five pages in [dashboard_design.md](dashboard_design.md). Verify totals against generated SQL outputs before sharing.
10. Save a PBIX locally. To refresh on another machine, update a `DataFolder` Power Query parameter or each CSV source path. No credentials are required for local imports. Desktop creation/refresh has not been automated by this project.

Example parameterized source (create a Text parameter named DataFolder pointing to the local export directory):

```powerquery
let
    Source = Csv.Document(
        File.Contents(DataFolder & "/dim_customer.csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]
    ),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    Types = Table.TransformColumnTypes(Headers, {{"customer_id", type text}})
in
    Types
```

The CSVs can be large; import the fact table once. Avoid loading the transaction CSV into worksheet grids. No external gateway or scheduled refresh service is configured.

