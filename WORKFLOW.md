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

`op-cup-lab` non ha un guardiano automatico di freschezza: se la pipeline di
`appalti-pubblici` si ferma, le colonne `anac_*` invecchiano **senza segnale** e
`min_rows` non aiuta (le righe non cambiano). La data e' esposta nel clean
(`anac_data_ultima_agg`) e come `MAX` in `mart_territorio`: se non si muove tra
due run, la fonte a monte e' ferma.

### Attenzione a `anac_importo_aggiudicato`

Dal 2024 ANAC pubblica in `importo_aggiudicazione` una **copia dell'importo a
base d'asta** (96-98% dei casi, contro il 38-63% del 2007-2023; i ribassi > 0
scendono da 3-6% a 0,2%). La colonna `anac_importo_aggiudicato` somma quel campo:
per il **57,7% delle aggiudicazioni (27,5% del valore)** misura quindi la base
d'asta, non il prezzo. **Non usarla per confronti temporali** ne' come «prezzo
pagato».

Per i costi dell'opera il clean espone il quadro economico ANAC, omogeneo in
tutta la serie: `anac_importo_base`, `anac_importo_consuntivo`,
`anac_scostamento_pct` e `anac_n_varianti_qe` (varianti **distinte**). Il mart
`mart_costi` li aggrega per regione × settore.

Tre regole di lettura, perché qui "costo" e' un rapporto tra due popolazioni e
non un dato additivo:

1. **NULL = dato assente, mai zero.** La base c'e' quasi sempre, il consuntivo
   per un quarto dei CUP: se nessun CIG ha il consuntivo, `anac_importo_consuntivo`
   e `anac_scostamento_pct` sono NULL. Contarli come zero direbbe «i lavori sono
   costati zero» — sarebbe uno scostamento del -100% per la maggior parte dei CUP.
   `anac_n_cig_con_base` / `anac_n_cig_con_consuntivo` dicono su quanti CIG e'
   calcolato.
2. **Lo scostamento si calcola sui CIG appaiati.** Base e consuntivo devono
   essere dello **stesso** CIG: su un CUP parziale (alcuni CIG con consuntivo,
   altri no) «consuntivo di parte / base di tutti» e' strutturalmente negativo.
   Da qui `anac_importo_base_appaiata`, `anac_importo_consuntivo_appaiato`,
   `anac_n_cig_appaiati`; `mart_costi` dichiara `n_cup_con_base`,
   `n_cup_con_scostamento` e `n_cup_parziali`. Senza pairing la mediana scende
   da −4,4% a −7,3% e il totale da −11,2 mld a −117,7 mld: due numeri diversi
   per lo stesso fenomeno. Attenzione alle due popolazioni: la mediana su
   **tutti** i CIG appaiati e' −3,4%, quella sui CIG mappati su un CUP e' −4,4%.
3. **Base >= 10 mld su un singolo CIG = sospetta** (`anac_base_sospetta`). La
   fonte ha importi fino a 1e73: senza guardia due CUP valgono 16 mila miliardi.
   Gli importi sospetti restano fuori dalle somme, la riga resta visibile con il
   flag. La soglia e' 10 mld e non 1 mld perche' qui l'importo e' il *contratto*,
   non il lotto: 1 mld e' un'opera grande plausibile, non un refuso — quelli
   restano contati in `anac_n_cig_base_grande`.
4. **Questa non e' la stessa cosa di `mart_sforamento` in appalti-pubblici.**
   Per gli **importi** (`anac_importo_base`, `anac_importo_consuntivo`) qui si
   somma per CUP su tutti gli eventi, con `COALESCE` sui componenti; per lo
   **scostamento** si usano solo le coppie appaiate. `mart_cig`/`mart_sforamento`
   sommano per CIG **senza** `COALESCE`, quindi su una fetta piu' stretta (il
   62,3% delle righe `BASE_ASTA` ha almeno un componente NULL). I due
   "scostamenti" non sono confrontabili: sono popolazioni diverse.

### Download OpenCUP: cache persistente

Lo ZIP di `opencup-progetti` pesa ~3 GB. Lo script lo scarica in
`~/.cache/dataciviclab/opencup/` (override con `OPENCUP_CACHE_DIR`), non in una
directory temporanea: cosi' il `curl -C -` riprende davvero dopo un'interruzione,
invece di ripartire da zero. Prima stava in una `TemporaryDirectory` cancellata
all'uscita, e un download interrotto a 2 GB su 3 buttava via tutto.

Prima del merge lo ZIP passa `zipfile.testzip()`: un parziale che sembra
completo produrrebbe un parquet monco in silenzio.

## Confine tecnico

- pipeline e dati → questa repo
- ANAC/PNRR/COESIONE → rispettive repo + GCS
- policy comuni, template → `.github`

## Maintainers

1. revisionano PR e stato del mart/catalogo
2. verificano `make check` e i contract test
3. curano il rilascio e pubblicano i deliverable
