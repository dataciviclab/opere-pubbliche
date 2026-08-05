# Opere Pubbliche Intelligence

**Dove vanno i soldi delle opere pubbliche in Italia? Chi li gestisce? Quanto arriva davvero a realizzazione?**

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
- **Dove le opere vengono chiuse d'ufficio?** (segnale di mancata realizzazione — Calabria in testa)
- **Quante opere arrivano davvero a gara e collaudo?** (dato: 6% con gara, 1,3% collaudate)

## Come funziona

```
opencup/            fonte: download + convert in parquet (15GB, mensile)
build/              pipeline: unified per CUP + 3 strati (fatti/aggregati) + regole join
queries/            catalogo analitico: una domanda = un file SQL
reports/            deliverable: data/reporting/panorama.md + .json
```

```bash
make build          # pipeline completa (unified + 3 strati + view)
make panorama       # deliverable: data/reporting/panorama.md + .json
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
| 1. Fatti per CUP | `data/cup/cup_fatti.parquet` | 11.861.554 | 237 MB | join per singola opera (snello) |
| 2. Aggregato comune | `data/aggregati/comune.parquet` | 31.573 | ~2 MB | analisi territoriale per comune |
| 2. Aggregato regione×settore | `data/aggregati/regione_settore.parquet` | 231 | — | quadro macro |
| 2. Aggregato settore | `data/aggregati/settore.parquet` | 11 | — | benchmark |
| 3. Unified (derivato) | `data/unified_operas.parquet` | 11.861.554 | 794 MB | ricostruibile su richiesta |

Le metriche ANAC degli aggregati usano le **colonne "piccole"** (gare sotto
soglia €5M) e il `flag_ombrello` per non inquinare i totali con i CUP-programma
(vedi `build/join-cup-anac-rules.md`). Il costo "pulito" esclude i CUP ombrello.

## Catalogo analitico (queries/)

Ogni domanda = un file SQL, leggibile con duckdb sugli aggregati (istantaneo):

| Query | Domanda |
|---|---|
| `queries/01_panorama.sql` | Qual è il quadro macro delle opere pubbliche? |
| `queries/02_divario_aree.sql` | Il PNRR sta riequilibrando il divario Nord/Sud? |
| `queries/03_settori_pnrr.sql` | In quali settori il PNRR pesa di più? |
| `queries/04_missioni_pnrr.sql` | Come si distribuisce il PNRR per missione? |
| `queries/05_soggetti_titolari.sql` | Chi gestisce i soldi delle opere? |
| `queries/06_stato_gestione.sql` | Dove le opere vengono chiuse d'ufficio? |
| `queries/07_esecuzione_anac.sql` | Quante opere arrivano davvero a gara e collaudo? |

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

## Deliverable (data/reporting/)

`make panorama` serializza i numeri chiave:
- `panorama.md` — leggibile da umani
- `panorama.json` — machine-readable per altri tool

## Stato

- ✅ Import OpenCUP (4 parquet) + build unified (11,86M CUP, 100% copertura)
- ✅ 3 strati + catalogo 7 query + deliverable panorama
- ⏭️ Prossimi: profilo per comune/regione completo, integrazione soggetti nel unified
