"""Stage 01: acquire the documented UCI source without modifying raw records."""

from utils.acquisition import acquire
from utils.runner import stage_cli


def run(ctx):
    """Download, verify, safely extract, and record provenance."""
    return acquire(ctx)


if __name__ == "__main__":
    stage_cli(1)
