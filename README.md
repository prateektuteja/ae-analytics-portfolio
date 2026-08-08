# AE Analytics Portfolio — Olist E-Commerce dbt Project

A dbt-core + DuckDB analytics engineering project transforming the [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) into a tested, documented star schema.

<!-- TODO Day 13: 1-2 sentence summary of what this project demonstrates (staging → intermediate → marts, testing, docs, CI/CD) -->

## Overview

<!-- TODO Day 13: what problem/dataset this models, why a galaxy schema (fct_orders + fct_order_items), key design decisions worth calling out -->

- **Source data:** 9 raw tables (orders, customers, products, payments, reviews, sellers, order items, product category translation, geolocation)
- **Layers:** staging (8 models) → intermediate (4 models) → marts (5 models: 3 dims, 2 facts)
- **Tests:** 53+ tests (schema + singular), including composite-key uniqueness via `dbt_utils`
- **Stack:** dbt-core, dbt-duckdb, DuckDB, Python (pandas, validation scripts)

## Architecture / Project DAG

<!-- TODO Day 13: embed the full-project DAG screenshot from Day 9 here -->

![DAG](docs/dag_screenshot.png)

## Setup

```bash
# clone and enter the project
git clone https://github.com/prateektuteja/ae-analytics-portfolio.git
cd ae-analytics-portfolio/ae_analytics_portfolio

# create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# install dependencies
pip install -r requirements.txt

# configure your local profile (see profiles.yml example below)
dbt debug

# load seed data
dbt seed

# build the full project
dbt build
```

<!-- TODO Day 13: note that seeds/raw_geolocation.csv is gitignored (50MB+) and must be downloaded separately from Kaggle -->

### profiles.yml (not committed — create at `~/.dbt/profiles.yml`)

```yaml
ae_analytics_portfolio:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: dev.duckdb
      threads: 4
```

## Testing

```bash
dbt test
```

<!-- TODO Day 13: brief note on schema tests vs. singular tests, and the two Python validation scripts (spot-check + full-population edge cases) -->

## Documentation

```bash
dbt docs generate
dbt docs serve
```

<!-- TODO Day 13: note that this serves a full column-level documented catalog + lineage DAG -->

## Tech stack

- dbt-core 1.10 + dbt-duckdb adapter
- DuckDB (local, file-based)
- Python 3 (pandas, PyYAML) for validation scripts
- GitHub Actions (CI — see `.github/workflows/`) <!-- TODO Day 11 -->

## Project structure

```
models/
  staging/         # 8 models, 1:1 with raw sources, cleaning + renaming only
  intermediate/     # 4 models, grain-changing aggregation/dedup
  marts/            # 5 models, star/galaxy schema (3 dims, 2 facts)
tests/              # singular tests
macros/             # custom Jinja macros
seeds/              # raw CSV source data
```

<!-- TODO Day 14: final polish pass, interview talking points -->
