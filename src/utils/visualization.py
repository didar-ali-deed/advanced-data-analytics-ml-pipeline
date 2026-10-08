"""Consistent static figures with titles, units, and interpretations."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from utils.data_loader import write_json

PALETTE = ["#147D92", "#E19B42", "#555C83", "#C45B60", "#5D9372"]
sns.set_theme(style="whitegrid", palette=PALETTE, context="notebook")
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})


class Charts:
    """Save stage-owned charts and a manifest without shared mutable outputs."""

    def __init__(self, ctx, stage: int):
        self.ctx, self.stage, self.items, self.outputs = ctx, stage, [], []

    def save(
        self, fig, category: str, name: str, title: str, question: str, interpretation: str
    ) -> Path:
        """Save a labeled 300-DPI image and record its analytical purpose."""
        path = self.ctx.path("visualizations", category, name + ".png")
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.suptitle(title, fontsize=14, fontweight="bold")
        fig.tight_layout()
        fig.savefig(path, dpi=self.ctx.config["analysis"]["chart_dpi"], bbox_inches="tight")
        plt.close(fig)
        self.items.append(
            {
                "title": title,
                "path": path.relative_to(self.ctx.root).as_posix(),
                "question": question,
                "interpretation": interpretation,
            }
        )
        self.outputs.append(path)
        return path

    def finish(self) -> list[Path]:
        """Return chart artifacts and the stage-specific manifest."""
        manifest = self.ctx.path("reports", "exploratory", f"charts_{self.stage:02d}.json")
        return self.outputs + [write_json(self.items, manifest)]


def bar_figure(series: pd.Series, xlabel: str, ylabel: str):
    """Make a readable ordered horizontal bar chart."""
    fig, ax = plt.subplots(figsize=(10, 5))
    series.sort_values().plot.barh(ax=ax, color=PALETTE[0])
    ax.set(xlabel=xlabel, ylabel=ylabel)
    return fig
