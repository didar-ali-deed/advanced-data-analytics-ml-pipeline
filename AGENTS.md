# Repository Guidelines

## Scope and Project Structure

These guidelines apply to the `advanced-data-analytics/` project. From the workspace root, change into that directory before running commands. The repository contains one `src/` directory with 25 numbered pipeline scripts and reusable `src/utils/` modules. Configuration lives in `config/`, SQL in `sql/`, and automated tests in `tests/`. Generated tables go to `data/`; models, reports, and figures have dedicated directories. Documentation and Power BI instructions live in `docs/` and `powerbi/`.

## Build, Test, and Development Commands

Create an environment with `python -m venv .venv`, then install `requirements.txt` using its Python interpreter. On PowerShell, use `.\.venv\Scripts\python.exe`.

- `python main.py --all`: run or resume the complete pipeline.
- `python main.py --stage 3`: run one stage with validated prerequisites.
- `python main.py --from-stage 7 --to-stage 15`: execute a range.
- `python -m pytest`: run unit tests and offline integration.
- `python -m ruff check .` and `python -m ruff format --check .`: verify code quality.

## Coding Style and Naming Conventions

Use Python 3.11+, four-space indentation, snake_case functions, descriptive names, type annotations, and concise docstrings. Ruff formats Python consistently. Use pathlib and configured paths. Keep each major operation in its dedicated numbered script; share reusable logic through utils. The runner uses explicit script paths for numeric filenames.

## Testing Guidelines

Name tests `test_*.py` and functions `test_<behavior>`. Use small synthetic fixtures exclusively for tests. Verify keys, monetary reconciliation, quarantine reasons, chronological separation, training-only preprocessing, inference, and checkpoint invalidation. No arbitrary coverage-percentage threshold is configured.

## Commit and Pull Request Guidelines

This new repository has no existing commit-message history. Use concise imperative subjects, optionally prefixed `feat:`, `fix:`, `test:`, or `docs:`. Pull requests should explain the problem, changed behavior, linked issues, verification commands, and affected reports. Include chart screenshots when visualization behavior changes.

## Data Integrity

Never modify raw source files or invent findings. Preserve source attribution, explicitly document overlap reconciliation, and exclude large datasets, databases, virtual environments, and trained binaries from Git. Regenerate downstream artifacts after code or configuration changes.

