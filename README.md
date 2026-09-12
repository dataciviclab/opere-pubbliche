# Opere Pubbliche Intelligence

**Dove vanno i soldi delle opere pubbliche in Italia? Chi li gestisce? Quanto arriva davvero a realizzazione?**

[![CI](https://github.com/dataciviclab/opere-pubbliche/actions/workflows/check.yml/badge.svg)](https://github.com/dataciviclab/opere-pubbliche/actions/workflows/check.yml)
[![Licenza: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Ogni progetto di investimento pubblico in Italia ha un CUP (Codice Unico di
Progetto). Questo repo raccoglie **tutti i CUP italiani** (anagrafe OpenCUP)
e li incrocia con i dati del Lab (appalti ANAC, PNRR, coesione) per
rispondere a quella domanda — con i numeri.

## Cosa contiene

| | |
|---|---|
| **CUP coperti** | 11,94 milioni (tutti i progetti di investimento pubblico, dal 1990 a oggi) |
| **Costo totale** | €4.135 miliardi |
| **Copertura Lab** | 25,6% dei CUP hanno almeno una fonte Lab (ANAC/PNRR/COESIONE) |
| **ANAC** | 1,5M CUP con gare, 1,2M gare tracciate, €1.574 mld importo |
| **Territorio** | fino al singolo comune (8.600+ comuni) |

## Esempi di domande

- **Quanto valgono le opere pubbliche nel mio comune?** E chi le gestisce?
- **Il PNRR sta riequilibrando il divario Nord-Sud?** (dato: no — incide ~3,5% ovunque)
- **Quali settori dipendono di più dai fondi PNRR?** (cultura 87%, trasporti 46%)
- **Quante opere arrivano davvero a collaudo?** (funnel: bando → aggiudicazione → SAL → collaudo)

## Come accedere ai dati

**1. DuckDB sul clean** — 1 riga per CUP con tutti gli attributi:

```bash
pip install "duckdb>=1.5"
python3 -c "import duckdb; print(duckdb.sql(\"SELECT regione, COUNT(*) n_cup FROM read_parquet('out/data/clean/op_cup_lab/2026/op_cup_lab_2026_clean.parquet') GROUP BY 1 ORDER BY 2 DESC LIMIT 5\"))"
```

**2. Query SQL sui mart** — aggregati pre-calcolati:

```python
import duckdb
# Copertura fonti per settore
duckdb.sql("SELECT * FROM read_parquet('out/data/mart/op_cup_lab/2026/mart_fonti.parquet')")
# Aggregati per regione x settore x anno
duckdb.sql("SELECT * FROM read_parquet('out/data/mart/op_cup_lab/2026/mart_territorio.parquet')")
```

## Come funziona

```bash
make run-all       # toolkit: datasets + support + compose (clean + mart)
make check         # valida tutti i config YAML
make test          # contract + smoke test
make registry      # catalogo artifact
```

## Struttura del repo

```
datasets/
  opencup-progetti/         ← anagrafe OpenCUP (11.94M CUP)
support/
  opencup-localizzazione/   ← lookup territorio
  opencup-fonti/            ← fonti finanziarie
  opencup-soggetti/         ← soggetti titolari
compose/
  op-cup-lab/               ← mega-join: anagrafe + loc + fonti + PNRR + ANAC + OC
out/                        ← toolkit output (fuori git)
tests/                      ← contract + smoke test
```

## Layer dati

| Layer | File | Righe | Uso |
|---|---|---|---|
| **Clean CUP** | `out/data/clean/op_cup_lab/2026/` | 11.942.784 | 1 riga/CUP con 57 attributi |
| **Mart territorio** | `out/data/mart/op_cup_lab/2026/mart_territorio.parquet` | 5.840 | regione × settore × anno |
| **Mart fonti** | `out/data/mart/op_cup_lab/2026/mart_fonti.parquet` | 33 | copertura fonti per settore × area |

## Fonti dei dati

| Fonte | Cosa fornisce | Dove legge |
|---|---|---|
| **OpenCUP** | anagrafe CUP (progetti, localizzazione, fonti) | `datasets/` + `support/` |
| **ANAC** | gare, aggiudicazioni, partecipanti, collaudo, SAL | `appalti-pubblici` (anac_cross) |
| **PNRR** | missione, finanziamenti, gare, pagamenti | `incubation/dataset-incubator` |
| **OpenCoesione** | ciclo, finanziamenti, stato progetti | `incubation/dataset-incubator` |

## Copertura Lab

| Fonte | CUP matchati | % su OpenCUP |
|---|---|---|
| OpenCoesione | 1.595.059 | 13,4% |
| ANAC (cross) | 1.510.809 | 12,6% |
| PNRR | 284.914 | 2,4% |
| **Almeno 1 fonte** | **3.055.303** | **25,6%** |

Il 74,5% dei CUP non ha fonte Lab — sono progetti locali piccoli, pre-2016, o non ancora in fase di gara.

## Limiti e trasparenza

- I numeri dipendono dalle fonti ufficiali: OpenCUP si aggiorna mensilmente.
- Una parte dei CUP è "ombrello" o placeholder: il flag `flag_ombrello` marca i CUP con ≥50 CIG o >30% gare piccole.
- I dati ANAC/PNRR/COESIONE vengono letti dai clean delle rispettive repo (non duplicati).
- Il compose `op-cup-lab` è la single source of truth per tutte le analisi.

## Partecipa

- **Discussions** → domande civiche, interpretazioni, proposte di metriche
- **Issues** → bug, problemi tecnici, miglioramenti della pipeline

## Licenza

MIT — vedi [LICENSE](LICENSE). Dati di fonte pubblica; la licenza vale per codice e documentazione del repo.
