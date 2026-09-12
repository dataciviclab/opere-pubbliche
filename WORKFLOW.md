# Workflow

Come contribuire a Opere Pubbliche Intelligence.

## Percorsi

- **feedback o idee:** Discussion della repo (domande civiche, interpretazioni, metriche)
- **avanzamento operativo:** Issue della repo
- **insight o visual:** dal clean o dai mart in `out/data/`

## Flusso minimo

1. apri una domanda, un feedback o una pagina da chiarire
2. scegli una issue o aprine una nuova
3. lavora su un branch dedicato
4. apri una PR piccola e leggibile (usa il PR template)

## Flusso tecnico minimo

1. installa: `pip install -r requirements.txt`
2. valida: `make check` (config YAML)
3. test: `make test` (contract + smoke, non richiede i layer)
4. esegui: `make run-all` (datasets + support + compose)
5. query: duckdb su `out/data/clean/op_cup_lab/` o sui mart

## Struttura dati

- **datasets/** + **support/** → anagrafe OpenCUP (toolkit pipeline)
- **compose/op-cup-lab/** → mega-join CUP-level (anagrafe + Lab)
- **out/** → output toolkit (fuori git)
- **tests/** → contract + smoke test

## Dati esterni

I compose leggono i clean da altre repo:
- ANAC: `appalti-pubblici/out/data/clean/anac_cross/`
- PNRR: `incubation/dataset-incubator/out/data/clean/pnrr_*/`
- OpenCoesione: `incubation/dataset-incubator/out/data/clean/opencoesione_*/`

Per CI, questi path verranno sostituiti con GCS.

## Confine tecnico

- pipeline e dati → questa repo
- ANAC/PNRR/COESIONE → rispettive repo + GCS
- policy comuni, template → `.github`

## Maintainers

1. revisionano PR e stato del mart/catalogo
2. verificano `make check` e i contract test
3. curano il rilascio e pubblicano i deliverable
