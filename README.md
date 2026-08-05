# Opere Pubbliche Intelligence

**Anagrafe universale dei progetti di investimento pubblico italiani (OpenCUP) + incrocio con i dataset del Lab.**

Il repo produce la base dati di intelligence sulle opere pubbliche: l'anagrafe completa dei CUP
(dal portale OpenCUP) come fondamento, arricchita con i sottoinsiemi del Lab (appalti ANAC, PNRR,
coesione) via join su CUP.

## Scopo in una frase

> Da un CUP a un profilo completo: anagrafe universale (OpenCUP) + contratti (ANAC) + stanziamento
> (PNRR/coesione) + erogazione — per rispondere a "dove vanno i soldi delle opere pubbliche in Italia".

## Perché un repo separato (non DI)

- **Fonte propria da ~15GB** (OpenCUP: Progetti 2,2GB + Localizzazione 205MB + Soggetti 2,9MB),
  aggiornata mensilmente — non è un candidate standard, è una banca dati verticale.
- **Consuma i clean del Lab via GCS** (contratto stabile) come arricchimento, non li modifica.
- Pattern già usato dal Lab: `terzo-settore-intelligence`, `open-siope`.

## Come funziona

```
opencup/
  scripts/
    download_opencup.py     # scarica i 4 zip ufficiali (URL estratti dalla pagina)
    convert_to_parquet.py   # estrai + converti in parquet zstd
  data/                     # (fuori git) raw/ zip + parquet/ convertiti
build/
  join_map.yaml             # registro chiavi di join OpenCup ↔ Lab (con match rate)
  build_unified.py          # incrocio CUP → data/unified_operas.parquet
data/                       # (fuori git) deliverable: unified per CUP
```

## Dati (import 2026-08-05, aggiornamento mensile OpenCUP)

| Parquet | Righe | Dim | Contenuto |
|---|---|---|---|
| `opencup_progetti` | 11.861.554 | 1,4 GB | anagrafe universale CUP (62 col, 0 duplicati) |
| `opencup_localizzazione` | 13.504.100 | 199 MB | CUP → regione/provincia/comune |
| `opencup_soggetti` | 54.208 | 3 MB | anagrafiche soggetti titolari |
| `opencup_fonti_copertura` | 22.689.806 | 150 MB | CUP → fonti (statale/UE/regionale/privata) |

## Layer dati (architettura a 3 strati)

Il monolite `unified_operas` (11,86M righe, colonna descrizione ~1,6GB) è stato
separato in layer per grano — le analisi territoriali non scansionano più le
11,86M righe:

| Layer | File | Righe | Dim | Uso |
|---|---|---|---|---|
| 1. Fatti per CUP | `data/cup/cup_fatti.parquet` | 11.861.554 | 237 MB | join per singola opera (snello, senza descrizioni pesanti) |
| 2. Aggregato comune | `data/aggregati/comune.parquet` | 31.573 | ~2 MB | analisi territoriale per comune |
| 2. Aggregato regione×settore | `data/aggregati/regione_settore.parquet` | 231 | — | quadro macro |
| 2. Aggregato settore | `data/aggregati/settore.parquet` | 11 | — | benchmark |
| 3. Unified (derivato) | `data/unified_operas.parquet` | 11.861.554 | 794 MB | ricostruibile su richiesta (join dei layer) |

Le metriche ANAC degli aggregati usano le **colonne "piccole"** (gare sotto
soglia €5M) e il `flag_ombrello` per non inquinare i totali con i CUP-programma
(vedi `build/join-cup-anac-rules.md`). Il costo "pulito" esclude i CUP ombrello.

## Build unified (grano: 1 riga per CUP)

`build/build_unified.py` unisce OpenCup con i dataset Lab e produce `data/unified_operas.parquet`:

```
anagrafe_*   da OpenCup progetti (stato, costo, finanziamento, classificazione)
localizzazione_*  da OpenCup localizzazione (regione, provincia, comune)
fonti_*      da OpenCup fonti copertura (n fonti, ha_fonte_*)
pnrr_*       da pnrr_progetti (GCS): missione, fin_pnrr, stato avanzamento
gare_*       da pnrr_gare (locale, candidate #800): n gare, importo aggiudicato
anac_*       da anac_appalti_master (GCS): n gare, importo, collaudati
coe_*        da opencoesione (GCS): ciclo, finanziamento, pagamenti
```

### Match rate chiavi (verificati 2026-08-05)

| Dataset Lab | CUP unici | Match in OpenCup |
|---|---|---|
| pnrr_progetti | 285.992 | 99,9% |
| opencoesione | 1.594.780 | 99,9% |
| anac_cup | 1.538.176 | 97,5% |

## Fonti

| Fonte | File | Dim | Note |
|---|---|---|---|
| OpenCUP Progetti | `OpendataProgetti.zip` | 2,2 GB | 7 shard CSV, 62 col, ~11,9M CUP |
| OpenCUP Localizzazione | `OpendataLocalizzazione.zip` | 248 MB | localizzazioni dei CUP |
| OpenCUP Soggetti | `OpendataSoggetti.zip` | 3 MB | anagrafiche soggetti titolari/richiedenti |
| OpenCUP Fonti copertura | `OpendataFontiCopertura.zip` | 161 MB | fonti di copertura |
| Lab (consumo) | clean GCS + locale | — | anac, pnrr, opencoesione (via join_map.yaml) |

Download: `python opencup/scripts/download_opencup.py` (gli URL correnti sono estratti dalla
pagina OpenCUP, robusto al cambio dei link Liferay). Serve venv attivo (lab-connectors).

## Workflow

```bash
source .venv/bin/activate
make build          # pipeline completa: unified + 3 strati + view
make panorama       # deliverable: data/reporting/panorama.md + .json
```

Oppure, passo per passo:

```bash
python opencup/scripts/download_opencup.py            # scarica gli zip (skip se presenti)
python opencup/scripts/convert_to_parquet.py          # zip → parquet (opencup/data/parquet/)
python build/build_unified.py                         # unified per CUP → data/unified_operas.parquet
python build/build_layers.py                          # 3 strati: cup_fatti + aggregati (comune/regione/settore)
python build/materialize_views.py                     # view aggregate → data/views/
python reports/panorama.py                            # report → data/reporting/
```

## Catalogo analitico (queries/)

Ogni domanda = un file SQL, leggibile con duckdb sugli aggregati (istantaneo):

| Query | Domanda |
|---|---|
| `queries/01_panorama.sql` | Qual è il quadro macro delle opere pubbliche? |
| `queries/02_divario_aree.sql` | Il PNRR sta riequilibrando il divario Nord/Sud? |
| `queries/03_settori_pnrr.sql` | In quali settori il PNRR pesa di più? |

## Deliverable (data/reporting/)

`make panorama` serializza i numeri chiave:
- `panorama.md` — leggibile da umani
- `panorama.json` — machine-readable per altri tool

## Stato

- ✅ Import OpenCUP (4 parquet) + build unified (11,86M CUP, 100% copertura)
- ⏭️ Prossimi: analisi sui dati unified, profilo per comune/regione, integrazione soggetti
