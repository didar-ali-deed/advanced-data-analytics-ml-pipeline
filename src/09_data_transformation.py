"""Stage 09: derive explicit revenue metrics and reporting aggregates."""

from utils.data_loader import read_frame, save_frame, write_json
from utils.preprocessing import transform
from utils.runner import stage_cli


def run(ctx):
    """Create line measures, a complete daily calendar, and pivot/unpivot examples."""
    frame = read_frame(ctx.path("data", "interim", "standardized.parquet"))
    lines, daily = transform(frame)
    monthly = lines.pivot_table(
        index="month", columns="country", values="gross_sales", aggfunc="sum", fill_value=0
    ).reset_index()
    long = monthly.melt(id_vars="month", var_name="country", value_name="gross_sales")
    return [
        save_frame(lines, ctx.path("data", "processed", "lines.parquet")),
        save_frame(daily, ctx.path("data", "processed", "daily.parquet")),
        save_frame(monthly, ctx.path("data", "processed", "monthly_country_wide.parquet")),
        save_frame(long, ctx.path("data", "processed", "monthly_country_long.parquet")),
        write_json(
            {
                "gross_sales": "Positive quantity and price, non-cancellation; includes service codes.",
                "net_value": "Signed quantity x price; not audited net revenue or profit.",
                "calendar": "No-record dates have zero observed sales, not asserted zero latent demand.",
                "final_day": "Last source day may be incomplete; omitted from model training/evaluation.",
            },
            ctx.path("reports", "data_quality", "metric_definitions.json"),
        ),
    ]


if __name__ == "__main__":
    stage_cli(9)
