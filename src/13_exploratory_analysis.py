"""Stage 13: distributions, interactions, temporal dependence and customer summaries."""

import pandas as pd

from utils.data_loader import read_frame, save_frame, write_json
from utils.database import connect
from utils.runner import stage_cli


def run(ctx):
    """Profile analytical grains instead of mixing transaction and calendar denominators."""
    daily = read_frame(ctx.path("data", "processed", "daily.parquet"))
    with connect(ctx.path("data", "processed", "retail.sqlite")) as con:
        invoices = pd.read_sql_query(
            "SELECT i.*, c.country FROM v_invoices i JOIN dim_country c USING(country_id)", con
        )
        customers = pd.read_sql_query(
            """
            SELECT i.customer_id, COUNT(*) AS orders, AVG(i.gross_sales) AS average_order,
                   SUM(i.gross_sales) AS gross_sales, COUNT(DISTINCT c.country) AS countries,
                   MIN(c.country) AS country, MAX(i.cancellation_value > 0) AS ever_cancelled
            FROM v_invoices i JOIN dim_country c USING(country_id)
            WHERE i.customer_id <> 'UNKNOWN' AND i.gross_sales > 0 GROUP BY i.customer_id
        """,
            con,
        )
    positive = invoices.loc[invoices["gross_sales"] > 0]
    numeric = positive[["gross_sales", "sale_lines", "sale_units"]]
    segment = (
        positive.groupby("country")["gross_sales"]
        .agg(["size", "mean", "median", "std", "skew"])
        .reset_index()
    )
    daily["weekday"] = daily["date"].dt.dayofweek
    daily["month_number"] = daily["date"].dt.month
    interaction = (
        daily.groupby(["month_number", "weekday"])["gross_sales"]
        .agg(["mean", "size"])
        .reset_index()
    )
    return [
        save_frame(invoices, ctx.path("data", "processed", "invoices.parquet")),
        save_frame(customers, ctx.path("data", "processed", "customers_eda.parquet")),
        save_frame(segment, ctx.path("reports", "exploratory", "invoice_segments.csv")),
        save_frame(interaction, ctx.path("reports", "exploratory", "seasonality.csv")),
        write_json(
            {
                "invoice_summary": numeric.describe(percentiles=[0.01, 0.5, 0.9, 0.99]).to_dict(),
                "skewness": numeric.skew().to_dict(),
                "kurtosis": numeric.kurt().to_dict(),
                "pearson": numeric.corr(method="pearson").to_dict(),
                "spearman": numeric.corr(method="spearman").to_dict(),
                "daily_autocorrelation": {
                    str(lag): daily["gross_sales"].autocorr(lag) for lag in [1, 7, 14, 28]
                },
                "grain": "Invoice groups by invoice/customer/country; serial calendar dependence is retained.",
                "mean_daily_gross_sales": daily["gross_sales"].mean(),
                "zero_sales_days": int(daily["gross_sales"].eq(0).sum()),
            },
            ctx.path("reports", "exploratory", "eda.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(13)
