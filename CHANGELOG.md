# Changelog

Tutte le modifiche di rilievo a questo progetto sono documentate qui.
Il formato segue [Keep a Changelog](https://keepachangelog.com/it/1.1.0/).

## [0.1.0] — 2026-08-18

### Aggiunto (public readiness)

- Convenzione “verticale consumer” del Lab: pipeline unica, GCS direct-read senza cache.
- Mart unico `data/cup/cup_fatti.parquet` (1 riga per CUP) + aggregati comune/regione/settore.
- Catalogo `queries/*.sql` (una domanda = un file, 7 domande) + deliverable `reports/panorama.py`.
- Smoke test di integrità del mart e del catalogo.
- Documentazione: `docs/` (overview, fonti, data dictionary, decisioni, join rules, contributing).
- Tooling condiviso: `.editorconfig`, `.gitattributes`, `.github` (PR/issue template, workflow CI).
- Contract test (`tests/`) conformi alla test-policy del Lab.