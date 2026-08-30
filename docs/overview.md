# Overview — Opere Pubbliche Intelligence

## Cos'è

Questo repo risponde a una domanda civica: **dove vanno i soldi delle opere
pubbliche in Italia, chi li gestisce e quanto arriva davvero a realizzazione?**

Ogni progetto di investimento pubblico in Italia ha un CUP (Codice Unico di
Progetto). Il repo raccoglie **tutti i CUP italiani** (anagrafe OpenCUP) e li
incrocia con i dati del Lab (appalti ANAC, PNRR, coesione) in un mart unico,
`cup_fatti`, da cui derivano aggregati e un catalogo di query prontamente
leggibili.

## Unità di analisi e chiavi

- **unità di analisi:** singolo CUP (Codice Unico di Progetto)
- **granularità territoriale:** fino al singolo comune (8.000+ comuni)
- **chiave primaria:** `cup` (15 caratteri alfanumerici)
- **granularità temporale:** stato aggiornato a ogni refresh della fonte (mensile OpenCUP)

## Copertura

- **anni coperti:** dal 1990 a oggi (nuovi CUP ogni anno)
- **CUP coperti:** ~11,86 milioni (copia integrale dell'anagrafe OpenCUP)
- **costo totale anagrafe:** ~€4.114 miliardi
- **quota PNRR:** ~€144 miliardi (~3,5% del costo totale)
- **territorio:** tutte le regioni, province e comuni italiani

## Domande civiche che puoi esplorare

- Quanto valgono le opere pubbliche nel mio comune? E chi le gestisce?
- Il PNRR sta riequilibrando il divario Nord-Sud? (dato: no — incide ~3,5% ovunque)
- Quali settori dipendono di più dai fondi PNRR? (cultura 87%, trasporti 46%)
- Dove le opere vengono chiuse d'ufficio? (segnale di mancata realizzazione — Calabria in testa)
- Quante opere arrivano davvero a gara e collaudo? (dato: 6% con gara, 1,3% collaudate)

## Limiti e caveat

- I numeri dipendono dalla qualità e tempestività delle fonti ufficiali (Sogei/OpenCUP, ANAC, DIPE).
- Una parte dei CIG ANAC ha CUP placeholder o CUP "ombrello" (contenitori programmatici):
  le regole di pulizia sono documentate in [decisions.md](decisions.md) e
  [join-cup-anac-rules.md](join-cup-anac-rules.md).
- La localizzazione OpenCUP include anche righe non riferite a un comune (es. "TUTTI I COMUNI",
  "AMBITO NAZIONALE"): gli aggregati territoriali le escludono esplicitamente.
- "Costo" = costo del progetto da anagrafe; i valori ANAC usano le colonne "piccole"
  (sotto soglia) per non inquinare i totali con i CUP-programma.

## Metodo

Pipeline toolkit + scripts custom:

```
FETCH (make opencup)
  └─> fetch_progetti.py: Liferay → ZIP → 7 CSV → parquet

TOOLKIT (make run-all)
  ├─> datasets/opencup-progetti: local_file → clean → mart
  ├─> support/opencup-localizzazione: http_file + unzip_first_csv → clean → mart
  ├─> support/opencup-fonti: http_file + unzip_first_csv → clean → mart
  └─> support/opencup-soggetti: http_file + unzip_first_csv → clean → mart

ANALISI (make metrics → layers → panorama)
  ├─> scripts/metriche_anac.py: metriche Lab da GCS → data/build/
  ├─> scripts/cup_fatti.py: join OpenCUP + metriche → cup_fatti + aggregati
  └─> scripts/panorama.py: deliverable → data/reporting/
```

Per dettagli di esecuzione vedi [contributing.md](contributing.md) e il README principale.