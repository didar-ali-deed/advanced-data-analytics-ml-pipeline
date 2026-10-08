# Verification record

Verified locally on 2026-10-08 with Python 3.11.9 on Windows.

- The public UCI archive downloaded successfully; actual retrieval time and hashes are in data/raw/provenance.json.
- All 25 stages completed on the full real workbook. Final automated audit: reports/final/verification.json.
- Ruff check and formatting check passed.
- pytest: 31 passed, including all 25 stages on offline synthetic test fixtures. The run reports 271 warnings, principally installed plotting-library deprecations; no tests failed.
- Source rows reconcile to accepted plus quarantine. SQLite enforces keys; stage 24 independently checks export keys and row counts.
- Charts use 300 DPI and carry titles, questions and interpretations in visualizations/manifest.json. Missingness, cohort and holdout figures were visually inspected.
- Final scripts/verify_outputs.py audit passed: 25 valid stage checkpoints, matching row counts, valid SQLite/Power BI keys, 22 SQL outputs, 22 charts and no broken README/final-report links. All generated SQL report links were also checked.
- A second full run skipped all 25 stages after validating artifact hashes; direct stage 03 and range 07-15 runs also resumed successfully.
- Candidate selection occurred before final test evaluation. The model card states the one-day-ahead protocol and historical-data limitations.
- requirements-lock.txt records the actual installed dependency environment.

## Commands

```powershell
python -m ruff check .
python -m ruff format --check .
python -m pytest
python main.py --all
python scripts/verify_outputs.py
```

The checked-in GitHub Actions workflow targets Windows and Ubuntu but has not been run on GitHub in this session. Power BI Desktop import, DAX execution and PBIX construction require the documented manual steps; no PBIX has been generated or validated. No hosted production deployment or external account integration was attempted.
