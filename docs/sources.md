# Fonti ufficiali

## OpenCUP (fonte primaria di dominio)

Anagrafe nazionale dei CUP, gestita da Sogei per conto della Presidenza del
Consiglio (DIPE). Tutti i progetti di investimento pubblico in Italia.

| Dataset | Contenuto | Dim (zip) |
|---|---|---|
| `OpendataProgetti.zip` | anagrafe universale CUP (stato, costo, settore, soggetto) | 2,2 GB |
| `OpendataLocalizzazione.zip` | CUP → regione/provincia/comune | 248 MB |
| `OpendataSoggetti.zip` | anagrafiche soggetti titolari/richiedenti | 3 MB |
| `OpendataFontiCopertura.zip` | fonti di copertura finanziaria | 161 MB |

- **Portale:** https://www.opencup.gov.it/portale/web/opencup/accesso-agli-open-data
- **Download:** `python opencup/scripts/download_opencup.py`
  (estrae gli URL correnti dalla pagina, robusto al cambio dei link Liferay `?t=...`)
- **Conversion in parquet:** `python opencup/scripts/convert_to_parquet.py`
- **Frequenza:** aggiornamento mensile (download locale in `opencup/data/`, fuori git)
- **Formato origine:** CSV delimitato `;`, encoding UTF-8, header

## Layer Lab (consumo diretto da GCS)

I 5 dataset puliti del Lab si leggono **direttamente dal bucket GCS pubblico**
con DuckDB (path contract `lab-connectors`, URL https nativi). Nessuna cache locale.

| Fonte | Slug clean | Cosa fornisce |
|---|---|---|
| ANAC appalti | `anac_appalti_master` | gare, aggiudicazioni, collaudo per CIG/CUP |
| OpenCoesione | `opencoesione_progetti` | ciclo, finanziamenti, stato |
| PNRR | `pnrr_progetti` | missione, finanziamenti, stato avanzamento |
| PNRR gare | `pnrr_gare` | CUP → CIG, importi aggiudicazione |
| PNRR pagamenti | `pnrr_pagamenti` | pagamenti PNRR |

- **Anno di riferimento:** 2026 (constante `https_url(..., year=2026)` in `pipeline.py`)
- **Licenza dei dati:** il Lab pubblica dati pubblici ufficiali; i file sono già puliti e normalizzati.

## Note qualità e pubblicazione

- I 7 shard CSV OpenCUP progetti (~15 GB) vengono uniti in un unico parquet tipizzato.
- `convert_to_parquet.py` importa con `all_varchar=true` (schema controllato in una fase successiva).
- Alcuni CIG del bridge ANAC hanno CUP placeholder (`ND`, `000000000000000`) o
  CUP "ombrello": vedi [join-cup-anac-rules.md](join-cup-anac-rules.md).
- Le metriche Lab cambiano quando la fonte viene rigenerata (es. `pnrr_pagamenti`
  aggiornato il 2026-08-05): da qui il refresh `make metrics`.