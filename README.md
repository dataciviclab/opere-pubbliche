# Opere Pubbliche Intelligence

**Dove vanno i soldi delle opere pubbliche in Italia? Chi li gestisce? Quanto arriva davvero a realizzazione?**

[![CI](https://github.com/dataciviclab/opere-pubbliche-intelligence/actions/workflows/test.yml/badge.svg)](https://github.com/dataciviclab/opere-pubbliche-intelligence/actions/workflows/test.yml)
[![Licenza: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Ogni progetto di investimento pubblico in Italia ha un CUP (Codice Unico di Progetto).
Questo repo raccoglie **tutti i CUP italiani** (anagrafe OpenCUP) e li incrocia con i dati
del Lab (appalti ANAC, PNRR, coesione) per rispondere a quella domanda — con i numeri.

## Cosa contiene

| | |
|---|---|
| **CUP coperti** | 11,86 milioni (tutti i progetti di investimento pubblico, dal 1990 a oggi) |
| **Costo totale** | €4.114 miliardi |
| **PNRR** | €144 miliardi — il 3,5% del costo totale |
| **Territorio** | fino al singolo comune (8.000+ comuni) |
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
- **Dove le opere vengono chiuse d'ufficio?** (segnale di mancata realizzazione — Calabria in testa)
- **Quante opere arrivano davvero a gara e collaudo?** (dato: 6% con gara, 1,3% collaudate)

## Come funziona

Flusso end-to-end in 4 fasi, un solo entry point (`pipeline.py`):

```
opencup/            fonte: download + convert in parquet (mensile)
pipeline.py         metrics → mart → aggregati
queries/            catalogo analitico: una domanda = un file SQL
reports/            deliverable: data/reporting/panorama.md + .json
```

```bash
make all            # metrics + layers + panorama (pipeline completa)
make layers         # rebuild mart + aggregati (comando quotidiano, veloce)
make metrics        # ri-materializza metriche Lab da GCS (solo quando la fonte cambia)
make panorama       # deliverable: data/reporting/panorama.md + .json
make test           # smoke test di integrità (antidoto alle regressioni)
```

## Layer dati

Un solo mart + derivati leggeri (niente monolite):

| Layer | File | Righe | Uso |
|---|---|---|---|
| 1. Mart per CUP | `data/cup/cup_fatti.parquet` | 11.861.554 | unica fonte per tutte le domande del catalogo |
| 2. Aggregato comune | `data/aggregati/comune.parquet` | 31.573 | analisi territoriale per comune |
| 2. Aggregato regione×settore | `data/aggregati/regione_settore.parquet` | 231 | quadro macro |
| 2. Aggregato settore | `data/aggregati/settore.parquet` | 11 | benchmark |

`cup_fatti` è 1 riga per CUP con: anagrafe (stato, costo, settore, soggetto titolare),
localizzazione (regione/provincia/comune), metriche Lab (PNRR missione+finanziamenti,
gare e pagamenti PNRR, gare ANAC con collaudo, coesione) e `flag_ombrello` per i
CUP-programma. Il costo "pulito" degli aggregati esclude i CUP ombrello.

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
| `queries/08_scheda_opera.sql` | Cosa sappiamo di un'opera? (1 CUP = 1 scheda — mart + SILOS) |

### Schede opera (per il forum)

`reports/scheda_opera.py` genera la scheda di un'opera dal catalogo 08, in
`data/reporting/schede/{cup}.md` — pensata per il forum (1 discussione = 1 opera):

```bash
python3 reports/scheda_opera.py F81H92000000008   # Terzo Valico
python3 reports/scheda_opera.py --all             # le 5 opere-icona del seed
```

Le 5 opere del seed (SILOS ∩ mart, con dati esecutivi): Terzo Valico, MO.S.E.,
Pedemontana Lombarda, Palermo-Catania, Torino-Lione.

## Fonti

| Fonte | File | Dim | Note |
|---|---|---|---|
| OpenCUP Progetti | `OpendataProgetti.zip` | 2,2 GB | 7 shard CSV, 62 col, ~11,9M CUP |
| OpenCUP Localizzazione | `OpendataLocalizzazione.zip` | 248 MB | localizzazioni dei CUP |
| OpenCUP Soggetti | `OpendataSoggetti.zip` | 3 MB | anagrafiche soggetti titolari/richiedenti |
| OpenCUP Fonti copertura | `OpendataFontiCopertura.zip` | 161 MB | fonti di copertura |
| Lab (consumo, GCS pubblico) | clean parquet | — | anac, pnrr, opencoesione |

Download: `python opencup/scripts/download_opencup.py` (gli URL correnti sono estratti dalla
pagina OpenCUP, robusto al cambio dei link Liferay). Serve venv attivo (lab-connectors).

## Deliverable (data/reporting/)

`make panorama` serializza i numeri chiave:
- `panorama.md` — leggibile da umani
- `panorama.json` — machine-readable per altri tool

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

- ✅ Import OpenCUP (4 parquet) + mart cup_fatti (11,86M CUP, 100% copertura)
- ✅ Un solo entry point (pipeline.py), aggregati leggeri, catalogo 8 query, panorama
- ✅ Smoke test (test_smoke.py) — protegge mart + catalogo dalle regressioni
- ⏭️ Prossimi: profilo per comune/regione completo, integrazione soggetti nel mart

## Licenza

MIT — vedi [LICENSE](LICENSE). Dati di fonte pubblica; la licenza vale per codice e documentazione del repo.
