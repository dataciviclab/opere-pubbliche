# Contributing

Guida rapida per contribuire a Opere Pubbliche Intelligence. Le policy comuni
dell'organizzazione vivono in `.github`; qui stanno solo le istruzioni locali al repo.

## Setup minimo

Prerequisiti: Python ≥ 3.12 e accesso al repo.

```sh
# installa il package con le dipendenze (incluso lab-connectors)
pip install -e ".[dev]"

# verifica byte-compile e coerenza
make check
```

Per eseguire l'intera pipeline servono i dati OpenCUP (15 GB, download mensile):

```sh
mkdir -p opencup/data/raw
python opencup/scripts/download_opencup.py --out opencup/data/raw
python opencup/scripts/convert_to_parquet.py

make all         # metrics + layers + panorama
```

Se hai già i layer (parquet in `data/`), il comando quotidiano è veloce e non scarica nulla:

```sh
make layers      # ricostruisce mart + aggregati
make panorama    # deliverable in data/reporting/
```

## Test

```sh
make test                  # esegue test_smoke.py (richiede i layer)
python -m pytest tests/    # contract test (non richiedono i layer)
```

- `tests/test_contract.py` (marker `contract`) verifica la forma del repo: file richiesti,
  convenzioni, `.gitignore`, percorso query.
- `test_smoke.py` (marker `smoke`) protegge il mart e il catalogo dalle regressioni.
  Segue la [test-policy](https://github.com/dataciviclab/lab-ops) del Lab: ogni test
  nuovo deve avere un marker (`contract`/`policy`/`regression`/`adapter`/`pure_unit`/`smoke`).

## Dove scrivere cosa

- Domande civiche, interpretazioni, proposte di metriche → Discussions del repo.
- Bug, task, miglioramenti della pipeline → Issues del repo.
- Problemi del path contract GCS o della config DuckDB condivisa → repo `lab-connectors`.
- Contesto generale del Lab → repo `dataciviclab`.

## Confine con le altre repo

- **`lab-connectors`**: fornisce `https_url(...)` (path contract GCS) e il download/HTTP helper.
  Se un path GCS cambia contratto, si corregge lì, non qui.
- **`.github`**: issue/PR template e community health files condivisi.

## Regole veloci

- Non committare output: `data/`, `_local/`, `*.parquet`, `*.csv`, `*.zip` sono ignorati.
- Nota nelle colonne del mart in `docs/data_dictionary.md` quando cambi lo schema.
- Registra ogni scelta non ovvia in `docs/decisions.md`.
- I path nella documentazione sono root-relative e POSIX.