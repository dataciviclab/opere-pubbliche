# Opere Pubbliche Intelligence

**Dove vanno i soldi delle opere pubbliche in Italia? Chi li gestisce? Quanto arriva davvero a realizzazione?**

[![CI](https://github.com/dataciviclab/opere-pubbliche-intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/dataciviclab/opere-pubbliche-intelligence/actions/workflows/ci.yml)
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
| **PNRR** | €144 miliardi — il 3,5% del costo totale |
| **Territorio** | fino al singolo comune (8.600+ comuni) |
| **Aggiornamento** | mensile (fonte OpenCUP) |

## Esempi di domande

- **Quanto valgono le opere pubbliche nel mio comune?** E chi le gestisce?
- **Il PNRR sta riequilibrando il divario Nord-Sud?** (dato: no — incide ~3,5% ovunque)
- **Quali settori dipendono di più dai fondi PNRR?** (cultura 87%, trasporti 46%)

## Come accedere ai dati

Tre modi, tutti sui layer già pronti in `data/`:

**1. DuckDB sul mart** — 1 riga per CUP, con anagrafe + localizzazione + metriche Lab:

```bash
pip install "duckdb>=1.0"
python3 -c "import duckdb; print(duckdb.sql(\"SELECT regione, COUNT(*) n_cup FROM read_parquet('data/cup/cup_fatti.parquet') GROUP BY 1 ORDER BY 2 DESC LIMIT 5\"))"
```

**2. Query SQL catalogate** — una domanda = un file in `queries/` (leggibili su mart e aggregati):

```bash
python3 -c "import duckdb; [duckdb.sql(open(f).read()) for f in ['queries/01_panorama.sql']]"
```

**3. Panorama pre-calcolato** — i numeri chiave già serializzati:

- `data/reporting/panorama.md` — leggibile da umani
- `data/reporting/panorama.json` — machine-readable per altri tool

## Come funziona

```
make opencup       # download OpenCUP + merge 7 shard → parquet (mensile)
make run-all       # toolkit processa tutti i 4 dataset (fetch HTTP + clean + mart)
make metrics       # metriche ANAC/PNRR/coesione da GCS → data/build/
make layers        # cup_fatti (1 riga/CUP) + aggregati → data/cup/ + data/aggregati/
make panorama      # deliverable: data/reporting/panorama.md + .json
make test          # contract + smoke test
make all           # pipeline completa
```

## Struttura del repo

```
datasets/
  opencup-progetti/         ← anagrafe OpenCUP (11.94M CUP, type=local_file)
support/
  opencup-localizzazione/   ← lookup territorio (type=http_file + unzip_first_csv)
  opencup-fonti/            ← lookup fonti finanziarie (type=http_file + unzip_first_csv)
  opencup-soggetti/         ← lookup soggetti (type=http_file + unzip_first_csv)
opencup/scripts/            ← fetch_progetti.py (download + merge 7 shard)
scripts/                    ← metriche_anac.py, cup_fatti.py, panorama.py
queries/                    ← 8 query SQL analitiche
reports/                    ← scheda_opera.py
data/                       ← output: cup_fatti, aggregati, reporting (fuori git)
out/                        ← toolkit output (fuori git)
```

## Layer dati

| Layer | File | Righe | Uso |
|---|---|---|---|
| Mart per CUP | `data/cup/cup_fatti.parquet` | 11.942.784 | unica fonte per tutte le domande del catalogo |
| Aggregato comune | `data/aggregati/comune.parquet` | 8.623 | analisi territoriale per comune |
| Aggregato regione×settore | `data/aggregati/regione_settore.parquet` | 231 | quadro macro |
| Aggregato settore | `data/aggregati/settore.parquet` | 11 | benchmark |

## Catalogo analitico (queries/)

Ogni domanda = un file SQL, leggibile con duckdb su `data/cup/cup_fatti.parquet`
o sugli aggregati (istantaneo):

| Query | Domanda |
|---|---|
| `queries/01_panorama.sql` | Qual è il quadro macro delle opere pubbliche? |
| `queries/02_divario_aree.sql` | Il PNRR sta riequilibrando il divario Nord/Sud? |
| `queries/03_settori_pnrr.sql` | In quali settori il PNRR pesa di più? |
| `queries/04_missioni_pnrr.sql` | Come si distribuisce il PNRR per missione? |
| `queries/05_soggetti_titolari.sql` | Chi gestisce i soldi delle opere? |
| `queries/06_stato_gestione.sql` | Dove le opere vengono chiuse d'ufficio? |
| `queries/07_esecuzione_anac.sql` | Quante opere arrivano davvero a gara e collaudo? |
| `queries/08_scheda_opera.sql` | Cosa sappiamo di un'opera? (1 CUP = 1 scheda) |

## Fonti

| Fonte | Cosa fornisce | Aggiornamento |
|---|---|---|
| OpenCUP | anagrafe CUP (progetti, localizzazione, soggetti, fonti) | mensile |
| ANAC appalti | gare, aggiudicazioni, collaudo per CIG/CUP | dal Lab (GCS) |
| PNRR | missione, finanziamenti, stato avanzamento, gare, pagamenti | dal Lab (GCS) |
| OpenCoesione | ciclo, finanziamenti, stato progetti coesione | dal Lab (GCS) |

## Limiti e trasparenza

- I numeri dipendono dalle fonti ufficiali: OpenCUP si aggiorna mensilmente.
- Una parte dei CUP ANAC è "ombrello" o placeholder: le regole di pulizia sono
  esplicite in [`docs/decisions.md`](docs/decisions.md) e pre-assegnate nel mart
  (`flag_ombrello`, colonne "piccole").
- Il dato pulito del Lab si legge da GCS direttamente (nessuna cache locale): zero stale data.
- Le scelte progettuali sono documentate in [`docs/`](docs/README.md).

## Partecipa

Hai un'idea, un'interpretazione o vuoi una nuova domanda?

- **Discussions** → domande civiche, interpretazioni, proposte di metriche
- **Issues** → bug, problemi tecnici, miglioramenti della pipeline
- **Contributing** → [`docs/contributing.md`](docs/contributing.md)

## Stato

- ✅ Toolkit pipeline (4 dataset: progetti + 3 support) con CI e GCS sync
- ✅ Scripts: metriche Lab da GCS, cup_fatti (1 riga/CUP), aggregati, panorama
- ✅ Smoke test + contract test conformi alla test-policy del Lab
- ⏭️ Prossimi: dashboard Streamlit, profilo per comune/regione

## Licenza

MIT — vedi [LICENSE](LICENSE). Dati di fonte pubblica; la licenza vale per codice e documentazione del repo.
