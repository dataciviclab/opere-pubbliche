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

I compose leggono i clean da altre repo, su GCS:
- ANAC: `appalti_pubblici/anac_cup`, `anac_aggiudicazioni`, `anac_stati_avanzamento`
  (prima era il compose `anac_cross`, rimosso in `appalti-pubblici`: era un
  CIG-level da 11 join, ricostruito qui solo per le metriche che servono)
- PNRR: `open_pnrr/pnrr_*`
- OpenCoesione: `open_coesione/opencoesione_progetti_esteso`

`op-cup-lab` non ha un guardiano di freschezza: se la pipeline di
`appalti-pubblici` si ferma, le colonne `anac_*` invecchiano **senza segnale** e
`min_rows` non aiuta (le righe non cambiano). Controllo: `anac_data_ultima_agg`
nella tabella `mart_territorio`.

## Confine tecnico

- pipeline e dati → questa repo
- ANAC/PNRR/COESIONE → rispettive repo + GCS
- policy comuni, template → `.github`

## Maintainers

1. revisionano PR e stato del mart/catalogo
2. verificano `make check` e i contract test
3. curano il rilascio e pubblicano i deliverable
