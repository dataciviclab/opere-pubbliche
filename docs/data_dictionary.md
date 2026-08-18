# Data Dictionary

Schema sintetico del mart e degli aggregati. Audience: maintainers e consumatori.

## Mart `data/cup/cup_fatti.parquet`

1 riga per CUP. Fonte unica per tutte le query del catalogo `queries/`.

| Colonna | Tipo | Descrizione | Nullable | Origine |
| --- | --- | --- | --- | --- |
| `cup` | string | Codice Unico di Progetto (15 char) | no | OpenCUP |
| `anno_decisione` | string | Anno di decisione del progetto | sì | OpenCUP |
| `stato_progetto` | string | Stato anagrafico (es. `CHIUSO D'UFFICIO`, `REALIZZATO`, `IN CORSO`) | sì | OpenCUP |
| `costo_progetto` | double | Costo del progetto da anagrafe (€) | sì | OpenCUP |
| `finanziamento_progetto` | double | Finanziamento da anagrafe (€) | sì | OpenCUP |
| `soggetto_titolare` | string | Nome soggetto titolare | sì | OpenCUP |
| `piva_soggetto_titolare` | string | PIVA/CF soggetto titolare | sì | OpenCUP |
| `natura_intervento` | string | Natura (nuova realizzazione, recupero, ...) | sì | OpenCUP |
| `tipologia_intervento` | string | Tipologia | sì | OpenCUP |
| `settore_intervento` | string | Settore (es. CULTURA, TRASPORTI) | sì | OpenCUP |
| `categoria_intervento` | string | Categoria | sì | OpenCUP |
| `regione` / `provincia` / `comune` | string | Localizzazione (da mettere in lowercase/accapo se serve) | sì | OpenCUP loc. |
| `codice_comune` | string | Codice ISTAT comune | sì | OpenCUP loc. |
| `n_fonti` | int | Numero fonti di copertura | sì | OpenCUP fonti |
| `ha_fonte_statale` / `ha_fonte_ue` / `ha_fonte_regionale` / `ha_fonte_privata` | int (0/1) | Flag fonte presente (statale, UE, regionale, privata) | sì | OpenCUP fonti |
| `pnrr_missione` | string | Missione PNRR | sì | Lab PNRR |
| `pnrr_stato_avanzamento` | string | Stato avanzamento PNRR | sì | Lab PNRR |
| `pnrr_amministrazione_titolare` | string | Amministrazione titolare del progetto PNRR | sì | Lab PNRR |
| `pnrr_fin_pnrr` | double | Finanziamento PNRR (€) | sì | Lab PNRR |
| `pnrr_fin_totale` | double | Finanziamento totale progetto PNRR (€) | sì | Lab PNRR |
| `pnrr_n_gare` | int | Numero gare PNRR | sì | Lab PNRR gare |
| `pnrr_n_gare_con_cig` | int | Gare PNRR con CIG | sì | Lab PNRR gare |
| `pnrr_importo_aggiudicato` | double | Importo aggiudicazione gare PNRR (€) | sì | Lab PNRR gare |
| `pag_fin_pnrr` | double | Finanziamento PNRR pagamenti | sì | Lab PNRR pagamenti |
| `pag_pagato_pnrr` | double | Pagato PNRR | sì | Lab PNRR pagamenti |
| `pag_pagato_totale` | double | Pagato totale | sì | Lab PNRR pagamenti |
| `pag_assorbimento_pct` | double | % pagato su finanziamento PNRR | sì | derivato |
| `anac_n_gare` | int | Gare ANAC | sì | Lab ANAC |
| `anac_n_cig` | int | CIG ANAC totali | sì | Lab ANAC |
| `anac_importo_aggiudicato` | double | Importo aggiudicazione ANAC totale (€) | sì | Lab ANAC |
| `anac_n_gare_pnrr` | int | Gare ANAC marcate PNRR | sì | Lab ANAC |
| `anac_n_collaudati` | int | Gare con collaudo | sì | Lab ANAC |
| `anac_n_gare_piccole` | int | Gare ANAC "piccole" (sotto soglia, esclusi ombrello) | sì | derivato |
| `anac_importo_gare_piccole` | double | Importo gare "piccole" (€) | sì | derivato |
| `anac_n_cig_b` | int | Affidamenti diretti (CIG prefisso B — smartCIG + affidamenti estesi) | sì | Lab ANAC |
| `anac_importo_cig_b` | double | Importo affidamenti diretti (€) | sì | Lab ANAC |
| `flag_ombrello` | boolean | True se CUP-programma (n_cig ≥ 50 e gare > 3× costo) | no | derivato |
| `coe_n_progetti` | int | Progetti coesione | sì | Lab OpenCoesione |
| `coe_finanz_tot_pubblico` | double | Finanziamento pubblico coesione (€) | sì | Lab OpenCoesione |
| `coe_pagamenti` | double | Pagamenti coesione (€) | sì | Lab OpenCoesione |

### Colonne "contrattuali" protette da `test_smoke.py`

`cup`, `regione`, `comune`, `soggetto_titolare`, `stato_progetto`, `costo_progetto`,
`pnrr_missione`, `pnrr_fin_pnrr`, `anac_n_cig`, `anac_n_gare_piccole`,
`anac_n_collaudati`, `flag_ombrello`, `anac_n_cig_b`, `anac_importo_cig_b`.

## Aggregati `data/aggregati/`

Derivati dal mart, ricalcolabili in <1 s (`make layers`). Non committano dati Lab raw.

### `comune.parquet`

| Colonna | Descrizione |
| --- | --- |
| `comune` | nome comune |
| `codice_comune` | codice ISTAT |
| `regione`, `provincia` | territorio |
| `n_cup` | numero CUP |
| `costo_mld_pulito` | costo totale esclusi CUP ombrello (€) |
| `fin_pnrr` | finanziamento PNRR (€) |
| `fin_totale` | finanziamento totale (€) |
| `anac_importo_gare_piccole` | importo gare ANAC "piccole" (€) |
| `pag_pagato_pnrr` | pagamenti PNRR (€) |
| `n_cup_pnrr` | CUP con missione PNRR |
| `n_cup_coesione` | CUP coesione |

Il WHERE esclude `comune IN ('', 'TUTTI', 'TUTTI I COMUNI', 'AMBITO NAZIONALE')`.

### `regione_settore.parquet`

`regione`, `settore_intervento`, `n_cup`, `costo_mld_pulito`, `fin_pnrr`,
`anac_importo_gare_piccole`, `pag_pagato_pnrr`.

### `settore.parquet`

`settore_intervento`, `n_cup`, `costo_mld_pulito`, `fin_pnrr`, `pag_pagato_pnrr`.