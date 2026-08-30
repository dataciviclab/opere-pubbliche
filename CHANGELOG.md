# Changelog

Tutte le modifiche di rilievo a questo progetto sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).

## [0.2.0] — 2026-08-28

### Cambiato (modernizzazione a pattern DPI)

- **Toolkit pipeline**: 4 dataset processati da toolkit (`datasets/` + `support/`), con `dataset.yml` + `sql/clean.sql` + `sql/mart.sql`.
- **Support datasets**: opencup-localizzazione, opencup-fonti, opencup-soggetti in `support/` con `type: http_file` + `extractor: unzip_first_csv`.
- **Progetti**: `type: local_file` con parquet prodotto da `opencup/scripts/fetch_progetti.py`.
- **CI**: `ci.yml` (lint + config check) + `pipeline.yml` (toolkit + scripts + GCS sync + registry).
- **Makefile**: pattern DPI (`run-all`, `run-seeds`, `metrics`, `layers`, `panorama`, `registry`).
- **pyproject.toml**: build-system, markers pytest, ruff, toolkit.extends, extra pipeline.
- **Scripts**: `scripts/metriche_anac.py`, `scripts/cup_fatti.py`, `scripts/panorama.py`.
- **Rimossi**: `pipeline.py` (legacy), `test_smoke.py` (root), `download_opencup.py`, `convert_to_parquet.py`.

## [0.1.0] — 2026-08-18

### Aggiunto (public readiness)

- Convenzione “verticale consumer” del Lab: pipeline unica, GCS direct-read senza cache.
- Mart unico `data/cup/cup_fatti.parquet` (1 riga per CUP) + aggregati comune/regione/settore.
- Catalogo `queries/*.sql` (una domanda = un file, 7 domande) + deliverable `reports/panorama.py`.
- Smoke test di integrità del mart e del catalogo.
- Documentazione: `docs/` (overview, fonti, data dictionary, decisioni, join rules, contributing).
- Tooling condiviso: `.editorconfig`, `.gitattributes`, `.github` (PR/issue template, workflow CI).
- Contract test (`tests/`) conformi alla test-policy del Lab.