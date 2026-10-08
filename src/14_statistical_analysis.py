"""Stage 14: customer-level tests and serially aware descriptive uncertainty."""

import numpy as np
from scipy import stats

from utils.data_loader import read_frame, write_json, write_text
from utils.runner import stage_cli
from utils.statistics import block_bootstrap_mean, bootstrap_difference, holm_adjust


def run(ctx):
    """Test a predefined geographic contrast using one observation per known customer."""
    customers = read_frame(ctx.path("data", "processed", "customers_eda.parquet"))
    eligible = customers.loc[customers["countries"].eq(1)].copy()
    a = eligible.loc[eligible["country"].eq("United Kingdom"), "average_order"].to_numpy()
    b = eligible.loc[~eligible["country"].eq("United Kingdom"), "average_order"].to_numpy()
    if min(len(a), len(b)) < 10:
        raise ValueError(
            "At least 10 identified single-country customers per contrast are required"
        )
    welch = stats.ttest_ind(a, b, equal_var=False)
    mw = stats.mannwhitneyu(a, b, alternative="two-sided")
    adjusted = holm_adjust([welch.pvalue, mw.pvalue])
    pooled = np.sqrt(
        ((len(a) - 1) * np.var(a, ddof=1) + (len(b) - 1) * np.var(b, ddof=1))
        / (len(a) + len(b) - 2)
    )
    effect = (a.mean() - b.mean()) / pooled if pooled > 0 else None
    ci = bootstrap_difference(
        a, b, ctx.config["analysis"]["bootstrap_repetitions"], ctx.config["seed"]
    )
    rng = np.random.default_rng(ctx.config["seed"])
    daily = read_frame(ctx.path("data", "processed", "daily.parquet")).iloc[:-1]
    mean_ci = block_bootstrap_mean(
        daily["gross_sales"],
        ctx.config["analysis"]["bootstrap_repetitions"],
        ctx.config["analysis"]["bootstrap_block_days"],
        ctx.config["seed"],
    )
    normality = {
        label: {
            "n_sample": min(len(values), 5000),
            "shapiro_p": stats.shapiro(
                rng.choice(values, min(len(values), 5000), replace=False)
            ).pvalue,
        }
        for label, values in [("UK", a), ("Other", b)]
    }
    pearson = stats.pearsonr(eligible["orders"], eligible["average_order"])
    spearman = stats.spearmanr(eligible["orders"], eligible["average_order"])
    report = {
        "contrast": "UK minus other-country known single-country customers",
        "unit": "One customer; unweighted mean of each customer's positive invoice-group values",
        "n_uk": len(a),
        "n_other": len(b),
        "excluded_anonymous": True,
        "excluded_multi_country_customers": int((customers.countries > 1).sum()),
        "mean_uk_gbp": a.mean(),
        "mean_other_gbp": b.mean(),
        "mean_difference_gbp": a.mean() - b.mean(),
        "mean_difference_ci95_gbp": ci,
        "cohen_d": effect,
        "tests": [
            {
                "test": "Welch independent-samples t-test",
                "null": "Equal population means",
                "alternative": "Unequal means",
                "statistic": welch.statistic,
                "p_value": welch.pvalue,
                "holm_p": adjusted[0],
                "effect": effect,
                "effect_definition": "Cohen d, UK minus other",
            },
            {
                "test": "Mann-Whitney U sensitivity",
                "null": "Equal distributions",
                "alternative": "Unequal distributions",
                "statistic": mw.statistic,
                "p_value": mw.pvalue,
                "holm_p": adjusted[1],
                "effect": 2 * mw.statistic / (len(a) * len(b)) - 1,
                "effect_definition": "Rank-biserial effect; not a median test without equal shapes",
            },
        ],
        "normality_diagnostics": normality,
        "customer_orders_vs_average_order": {
            "pearson_r": pearson.statistic,
            "spearman_r": spearman.statistic,
            "note": "Descriptive association only; no causal interpretation or additional significance claim.",
        },
        "daily_mean_gbp": daily["gross_sales"].mean(),
        "daily_mean_block_ci95_gbp": mean_ci,
        "assumptions": [
            "Customers treated as independent; shared markets and unknown wholesale relationships may violate this.",
            "Country comparison is observational and not adjusted for mix, tenure or season.",
            "Welch permits unequal variances; heavy tails motivate the nonparametric sensitivity test.",
            "Holm correction covers the two explicitly reported geographic tests.",
            "Bootstrap intervals describe this sample era, not future prediction intervals.",
            "Seven-day moving blocks preserve local dependence but not all long-term seasonality.",
            "Paired tests/ANOVA/chi-square omitted because this predefined contrast does not require them.",
        ],
    }
    markdown = (
        "# Statistical analysis\n\n"
        f"UK: {len(a):,} customers; other countries: {len(b):,}. "
        f"Mean customer-level invoice difference: GBP {report['mean_difference_gbp']:,.2f}, "
        f"bootstrap 95% CI [{ci[0]:,.2f}, {ci[1]:,.2f}].\n\n"
        f"Welch p={welch.pvalue:.6g}, Holm p={adjusted[0]:.6g}; "
        f"Mann-Whitney p={mw.pvalue:.6g}, Holm p={adjusted[1]:.6g}.\n\n"
        "Differences are associations conditional on identified customers. They do not establish "
        "an effect of geography. Review wholesale/customer mix before acting.\n\n"
        + "\n".join("- " + text for text in report["assumptions"])
    )
    return [
        write_json(report, ctx.path("reports", "statistical", "statistics.json")),
        write_text(markdown, ctx.path("reports", "statistical", "statistics.md")),
    ]


if __name__ == "__main__":
    stage_cli(14)
