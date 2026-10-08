"""Business question metadata paired with executed SQL outputs."""

import re

QUESTIONS = {
    "quality": (
        "How complete and repetitive are accepted records?",
        "Quantify confidence in downstream metrics.",
        "Prioritize identifier capture and duplicate review.",
    ),
    "duplicate_sensitivity": (
        "How much does ambiguous deduplication change gross sales?",
        "Bound sensitivity to repeated business lines.",
        "Resolve source-line identity before deleting repeats.",
    ),
    "adjustments": (
        "How much signed value comes from non-cancellation adjustments?",
        "Separate inventory-like adjustments from sale performance.",
        "Review adjustment workflows with finance.",
    ),
    "overview": (
        "What are total sales, cancellations, orders and known buyers?",
        "Establish an executive baseline.",
        "Use the defined KPI denominators consistently.",
    ),
    "monthly": (
        "How do recorded sales vary across months?",
        "Support historical capacity planning.",
        "Compare complete periods before changing capacity.",
    ),
    "country": (
        "Which countries contribute the most gross sales?",
        "Identify concentration and market exposure.",
        "Prioritize operational support for major markets.",
    ),
    "products": (
        "Which product codes lead gross sales and units?",
        "Identify high-contribution assortment.",
        "Review availability for leading codes; separate service codes.",
    ),
    "cancellation_country": (
        "Where is cancellation value concentrated?",
        "Find markets for cancellation review.",
        "Investigate high-value exceptions without assuming return causes.",
    ),
    "anonymous": (
        "What share of sales has no identified customer?",
        "Assess bias in customer analytics.",
        "Improve identifier capture while retaining anonymous sales totals.",
    ),
    "baskets": (
        "How do average invoice sizes differ across countries?",
        "Inform fulfillment capacity.",
        "Review basket distributions and wholesale mix before intervention.",
    ),
    "weekday": (
        "Which weekdays have higher observed sales?",
        "Plan recurring staffing patterns.",
        "Use calendar-day averages, including days with no records.",
    ),
    "hourly": (
        "When during source-local hours are sales recorded?",
        "Describe intraday workload.",
        "Validate timezone and operating hours before scheduling changes.",
    ),
    "prices": (
        "Which product codes show the most price variation?",
        "Find pricing or metadata review candidates.",
        "Check discounts, descriptions and unit definitions.",
    ),
    "growth": (
        "How do sales change month over month?",
        "Track comparable-period momentum.",
        "Investigate large changes in complete months.",
    ),
    "yoy": (
        "How do complete months compare with the previous year?",
        "Reduce seasonal confounding in growth review.",
        "Investigate product and customer mix behind changes.",
    ),
    "rolling": (
        "What do seven-day trends and running sales show?",
        "Smooth daily operational volatility.",
        "Use trailing trends with the original daily series.",
    ),
    "concentration": (
        "How concentrated are known-customer sales?",
        "Assess dependence on a few accounts.",
        "Monitor continuity for high-contribution customers.",
    ),
    "repeat": (
        "How much activity comes from repeat observed buyers?",
        "Describe customer engagement within the observation window.",
        "Design retention experiments; avoid lifetime claims.",
    ),
    "cohorts": (
        "How often do customer cohorts buy again?",
        "Compare observed retention patterns.",
        "Compare cohorts at equal maturity; flag incomplete last month.",
    ),
    "rfm": (
        "Which known customers have high recency, frequency and value?",
        "Support a historical segmentation exercise.",
        "Validate outreach rules on contemporary consented data.",
    ),
    "zero_days": (
        "Which dates have no recorded positive sales?",
        "Expose calendar coverage assumptions.",
        "Confirm whether gaps reflect closure or missing capture.",
    ),
    "contributions": (
        "How concentrated are sales across product codes?",
        "Identify assortment dependence.",
        "Review supply continuity for high-contribution codes.",
    ),
}


def load_queries(sql_dir):
    """Read named SQL statements from the checked-in analysis files."""
    result = {}
    for filename in ["02_data_quality.sql", "03_business_kpis.sql", "04_advanced_analysis.sql"]:
        contents = (sql_dir / filename).read_text(encoding="utf-8")
        parts = re.split(r"-- question: (\w+)\s*\n", contents)
        for index in range(1, len(parts), 2):
            result[parts[index]] = parts[index + 1].strip()
    if set(result) != set(QUESTIONS):
        raise ValueError("SQL questions and business metadata are inconsistent")
    return result


def interpretation(name, frame):
    """Summarize measured outputs without manufacturing findings."""
    if frame.empty:
        return "No qualifying observations; the question cannot be quantified under these filters."
    if name == "overview":
        row = frame.iloc[0]
        return (
            f"Gross sales were GBP {row.gross_sales:,.2f}; cancellation value was "
            f"GBP {row.cancellation_value:,.2f}; {int(row.sale_invoices):,} sale invoices were observed."
        )
    if name == "country":
        row = frame.iloc[0]
        return f"{row.country} led with {row.share:.1%} of accepted gross sales."
    if name == "duplicate_sensitivity":
        return (
            f"Hypothetical removal of repeated business rows changes gross sales by GBP "
            f"{frame.iloc[0].ambiguous_value_difference:,.2f}; identity remains uncertain."
        )
    if name == "zero_days":
        return (
            f"{len(frame)} calendar days had no positive recorded sales; the cause is unobserved."
        )
    if name == "cohorts":
        return (
            f"{frame.cohort.nunique()} observed first-purchase cohorts span {len(frame)} cohort-month cells. "
            "Later cohorts have shorter follow-up; absent future cells are unobserved, not zero retention."
        )
    first = frame.head(1).to_dict("records")[0]
    observed = "; ".join(
        f"{k}={v:,.4g}" if isinstance(v, (int, float)) else f"{k}={v}" for k, v in first.items()
    )
    return f"Output contains {len(frame):,} groups/periods. First reported result: {observed}."
