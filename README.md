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
| **`unified_operas`** | **11.861.554** | **794 MB** | profilo 1 riga per CUP, arricchito |

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
python opencup/scripts/download_opencup.py            # scarica gli zip (skip se presenti)
python opencup/scripts/convert_to_parquet.py          # zip → parquet (opencup/data/parquet/)
python build/build_unified.py                         # unified per CUP → data/unified_operas.parquet
```

## Stato

- ✅ Import OpenCUP (4 parquet) + build unified (11,86M CUP, 100% copertura)
- ⏭️ Prossimi: analisi sui dati unified, profilo per comune/regione, integrazione soggetti
