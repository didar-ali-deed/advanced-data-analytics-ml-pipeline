"""Stage 15: publication-quality retail charts with computed interpretations."""

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from utils.data_loader import read_frame, read_json
from utils.runner import stage_cli
from utils.visualization import Charts, bar_figure


def run(ctx):
    """Draw meaningful distribution, temporal, categorical and cohort figures."""
    charts = Charts(ctx, 15)
    daily = read_frame(ctx.path("data", "processed", "daily.parquet"))
    invoices = read_frame(ctx.path("data", "processed", "invoices.parquet"))
    positive = invoices.loc[invoices.gross_sales > 0].copy()
    positive["log_sales"] = np.log10(positive["gross_sales"])
    sample = positive.sample(min(5000, len(positive)), random_state=ctx.config["seed"])

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(positive, x="log_sales", bins=50, kde=True, ax=ax)
    ax.set(xlabel="Invoice gross sales (log10 GBP)", ylabel="Invoice groups")
    charts.save(
        fig,
        "distributions",
        "invoice_distribution",
        "Distribution of positive invoice values",
        "How large are recorded baskets?",
        f"Median invoice-group value is GBP {positive.gross_sales.median():,.2f}; "
        f"99th percentile is GBP {positive.gross_sales.quantile(0.99):,.2f}.",
    )

    top = positive.country.value_counts().head(6).index
    fig, ax = plt.subplots(figsize=(11, 5))
    sns.boxplot(
        data=positive[positive.country.isin(top)],
        x="country",
        y="log_sales",
        order=top,
        color="#147D92",
        showfliers=False,
        ax=ax,
    )
    ax.set(xlabel="Country", ylabel="Invoice gross sales (log10 GBP)")
    charts.save(
        fig,
        "categories",
        "country_baskets",
        "Basket distributions in six frequent markets",
        "How do basket sizes vary by market?",
        "Boxes show within-market dispersion; hidden plotted fliers remain in all calculations.",
    )

    fig, ax = plt.subplots(figsize=(11, 5))
    sns.violinplot(
        data=sample[sample.country.isin(top[:4])],
        x="country",
        y="log_sales",
        order=top[:4],
        inner="quart",
        cut=0,
        color="#147D92",
        ax=ax,
    )
    ax.set(xlabel="Country", ylabel="Invoice gross sales (log10 GBP)")
    charts.save(
        fig,
        "distributions",
        "basket_violin",
        "Sampled basket-value density by market",
        "Are market distributions similarly shaped?",
        f"Density uses a seeded sample of {len(sample):,} positive invoice groups.",
    )

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(daily.date, daily.gross_sales, alpha=0.35, label="Daily", color="#147D92")
    ax.plot(daily.date, daily.rolling_7_sales, label="Trailing 7-day mean", color="#E19B42")
    ax.set(xlabel="Source-local date", ylabel="Observed gross sales (GBP)")
    ax.legend()
    charts.save(
        fig,
        "time_series",
        "daily_sales",
        "Daily recorded sales and trailing trend",
        "How volatile are daily sales?",
        f"Daily gross sales range from GBP {daily.gross_sales.min():,.0f} "
        f"to GBP {daily.gross_sales.max():,.0f}; final source day may be partial.",
    )

    monthly = read_frame(ctx.path("reports", "exploratory", "sql", "monthly.csv"))
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(monthly.month, monthly.gross_sales, label="Gross sales", color="#147D92")
    ax.bar(monthly.month, -monthly.cancellation_value, label="Cancellation value", color="#C45B60")
    ax.tick_params(axis="x", rotation=60)
    ax.set(xlabel="Month (last month incomplete)", ylabel="Value (GBP)")
    ax.legend()
    charts.save(
        fig,
        "time_series",
        "monthly_sales",
        "Monthly gross sales and cancellation value",
        "How do sales and cancellation values evolve?",
        f"{int((monthly.complete_month == 0).sum())} monthly period(s) are incomplete.",
    )

    countries = read_frame(ctx.path("reports", "exploratory", "sql", "country.csv"))
    charts.save(
        bar_figure(
            countries.head(10).set_index("country").gross_sales, "Gross sales (GBP)", "Country"
        ),
        "categories",
        "country_sales",
        "Top ten countries by gross sales",
        "Which markets dominate?",
        f"{countries.iloc[0].country} contributes {countries.iloc[0]['share']:.1%}.",
    )

    products = read_frame(ctx.path("reports", "exploratory", "sql", "contributions.csv"))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(np.arange(1, len(products) + 1), products.cumulative_share * 100, color="#147D92")
    ax.axhline(80, color="#E19B42", linestyle="--", label="80% reference")
    ax.set(xlabel="Product codes ranked by gross sales", ylabel="Cumulative gross sales (%)")
    ax.legend()
    charts.save(
        fig,
        "categories",
        "product_concentration",
        "Product-code contribution curve",
        "How concentrated is the assortment?",
        f"The leading 20 codes contribute {products.head(20).sales_share.sum():.1%} of gross sales.",
    )

    fig, ax = plt.subplots(figsize=(7, 6))
    numeric = positive[["gross_sales", "sale_lines", "sale_units"]]
    sns.heatmap(
        numeric.corr(method="spearman"), annot=True, vmin=-1, vmax=1, center=0, cmap="vlag", ax=ax
    )
    charts.save(
        fig,
        "correlations",
        "invoice_correlations",
        "Spearman association across invoice measures",
        "How do basket value, units and lines relate?",
        "Invoice-derived measures share mathematical components; associations are not causal.",
    )

    fig, ax = plt.subplots(figsize=(9, 5))
    sns.scatterplot(data=sample, x="sale_units", y="gross_sales", alpha=0.3, s=12, ax=ax)
    ax.set(
        xscale="log",
        yscale="log",
        xlabel="Units per invoice group (log scale)",
        ylabel="Gross sales per invoice group (GBP, log scale)",
    )
    charts.save(
        fig,
        "relationships",
        "units_value",
        "Units and value in sampled invoices",
        "Do large baskets always have high value?",
        "Log axes retain wholesale extremes and show variation in unit price and assortment.",
    )

    pairs = sample[["gross_sales", "sale_lines", "sale_units"]].head(600).copy()
    pairs = np.log1p(pairs).rename(columns=lambda c: "log1p " + c)
    grid = sns.pairplot(pairs, corner=True, diag_kind="hist", plot_kws={"alpha": 0.3, "s": 10})
    charts.save(
        grid.figure,
        "relationships",
        "invoice_pairplot",
        "Sampled invoice relationships",
        "What multivariate patterns deserve investigation?",
        "600 seeded sampled invoices; all three measures use log1p transformations.",
    )

    cohorts = read_frame(ctx.path("reports", "exploratory", "sql", "cohorts.csv"))
    heat = cohorts.pivot(index="cohort", columns="months_since_first", values="observed_retention")
    fig, ax = plt.subplots(figsize=(13, 8))
    sns.heatmap(
        heat * 100,
        mask=heat.isna(),
        cmap="Blues",
        vmin=0,
        vmax=100,
        cbar_kws={"label": "Cohort customers buying (%)"},
        ax=ax,
    )
    ax.set(xlabel="Months since first observed purchase", ylabel="First observed purchase month")
    charts.save(
        fig,
        "dashboards",
        "cohort_retention",
        "Observed customer purchase retention",
        "How do cohorts return over time?",
        "Blank future cells are unobserved. First cohort is left-censored; final month is incomplete.",
    )

    weekdays = read_frame(ctx.path("reports", "exploratory", "sql", "weekday.csv"))
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(
        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        weekdays.average_daily_sales,
        color="#147D92",
    )
    ax.set(xlabel="Weekday", ylabel="Mean recorded gross sales per calendar day (GBP)")
    charts.save(
        fig,
        "time_series",
        "weekday_sales",
        "Weekly sales pattern using all calendar days",
        "Which weekdays carry more recorded sales?",
        "Means include zero-record dates; no-record days do not prove absence of demand.",
    )

    wide = read_frame(ctx.path("data", "processed", "monthly_country_wide.parquet")).set_index(
        "month"
    )
    leaders = wide.sum().nlargest(4).index
    stack = wide[leaders].copy()
    stack["Other countries"] = wide.drop(columns=leaders).sum(axis=1)
    fig, ax = plt.subplots(figsize=(12, 5))
    stack.div(stack.sum(axis=1), axis=0).mul(100).plot.bar(stacked=True, ax=ax, width=0.85)
    ax.set(xlabel="Month", ylabel="Monthly gross sales contribution (%)")
    ax.legend(bbox_to_anchor=(1.01, 1), loc="upper left")
    charts.save(
        fig,
        "categories",
        "market_mix",
        "Market contribution over time",
        "Does the geographic sales mix change?",
        "Each column uses that month's gross sales denominator; final month is partial.",
    )

    stat = read_json(ctx.path("reports", "statistical", "statistics.json"))
    center, interval = stat["mean_difference_gbp"], stat["mean_difference_ci95_gbp"]
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.errorbar(
        center,
        0,
        xerr=[[max(0, center - interval[0])], [max(0, interval[1] - center)]],
        fmt="o",
        color="#147D92",
        capsize=8,
    )
    ax.axvline(0, color="gray", linestyle="--")
    ax.set(
        xlabel="UK minus other: mean customer-level invoice value (GBP)", yticks=[], ylim=(-1, 1)
    )
    charts.save(
        fig,
        "relationships",
        "customer_difference_ci",
        "Customer-level difference with 95% bootstrap CI",
        "What is the uncertainty around the geographic contrast?",
        f"Difference GBP {center:,.2f}; interval [{interval[0]:,.2f}, {interval[1]:,.2f}]. "
        "Observational association, not a geographic treatment effect.",
    )
    return charts.finish()


if __name__ == "__main__":
    stage_cli(15)
