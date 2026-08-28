# Workflow

Come contribuire in modo semplice a Opere Pubbliche Intelligence.

## Percorsi

- **feedback o idee:** Discussion della repo (domande civiche, interpretazioni, metriche)
- **avanzamento operativo:** Issue, project board o milestone della repo
- **insight o visual:** partiti da `queries/` o dal panorama in `data/reporting/`

## Flusso minimo

1. apri una domanda, un feedback o una pagina da chiarire
2. scegli una issue o aprine una nuova
3. lavora su un branch dedicato
4. apri una PR piccola e leggibile (usa il PR template)

## Flusso tecnico minimo

1. installa: `pip install -e ".[dev]"` (o `pip install -e ".[pipeline]"` per toolkit)
2. valida: `python -m pytest tests/` (contract, non richiede i layer)
3. se hai i dati: `make all` (toolkit + metrics + layers + panorama + test)
4. registra le scelte in `docs/decisions.md` e lo schema in `docs/data_dictionary.md` quando cambiano

## Confine tecnico

- pipeline, query e dati → questa repo
- path contract GCS / config DuckDB condivise → `lab-connectors`
- policy comuni, template, community health → `.github`
- contesto e mappa delle repo → repo `dataciviclab`

## Maintainers

1. revisionano PR e stato del mart/catalogo
2. verificano `make check` e i contract test
3. curano il rilascio (tag, CHANGELOG) e pubblicano i deliverable