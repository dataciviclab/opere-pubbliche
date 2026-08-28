# Decision log — Opere Pubbliche Intelligence

Registriamo le scelte che cambiano il significato dei dati o il contratto verso i consumatori.

## D-001 — Repo verticale consumer, nessuna ingestione dei layer Lab

- **decisione:** questo repo consuma i layer clean del Lab da GCS (direct-read via DuckDB),
  non li riscarica né li cachea localmente. Per la stessa ragione convivono `metrics` + `layers`
  come unico entry point.
- **motivo:** aderire alla convenzione verticali del Lab (niente stale data, niente egress
  ricorrente, niente codice di cache da mantenere). Vedi [lab_links.md](lab_links.md).
- **impatto:** `make metrics` va eseguito solo quando la fonte Lab cambia; il comando quotidiano
  è `make layers`.
- **alternative:** cache locale dei parquet Lab (scartata: stale data + costo di manutenzione).

## D-002 — Mart unico `cup_fatti` (1 riga per CUP)

- **decisione:** un solo mart per CUP, con anagrafe + localizzazione + metriche Lab + soggetto.
  Tutte le query del catalogo leggono da qui (o dagli aggregati derivati).
- **motivo:** evitare il monolite "unified" precedente (troppo pesante) mantenendo però un solo
  grano di verità, protetto da `test_smoke.py`.
- **impatto:** aggiungere una metrica nuova = aggiungere una colonna al mart, mai una tabella parallela.

## D-003 — CUP ombrello e colonne "piccole" per ANAC

- **decisione:** i CUP-programma/ombrello non entrano negli importi aggregati. Si usano
  `anac_n_gare_piccole` / `anac_importo_gare_piccole` (solo gare sotto soglia) al posto della
  somma totale; `flag_ombrello = (anac_n_cig >= 50) AND (anac_importo_aggiudicato > costo*3)`.
- **motivo:** i CUP-programma gonfiano gli importi (es. smart grid: gare >> costo anagrafe).
  Il doppio criterio distingue i contenitori dalle opere vere con molte gare (es. Terzo Valico).
- **impatto:** regole dettagliate e casi reali in [join-cup-anac-rules.md](join-cup-anac-rules.md).
- **alternative:** solo `n_cig >= 50` (scartato: classifica male le opere vere con tante gare).

## D-004 — CUP placeholder esclusi dai join ANAC/PNRR

- **decisione:** nei join per CUP si escludono i placeholder `ND`, `000000000000000`, `''`.
- **motivo:** ~2,0M CIG su 7,0M (28,5%) hanno CUP placeholder; distorcono i *conteggi* (non gli importi).

## D-005 — Localizzazione territoriale senza righe "non-territorio"

- **decisione:** gli aggregati per comune escludono `'', 'TUTTI', 'TUTTI I COMUNI', 'AMBITO NAZIONALE'`.
- **motivo:** le voci non riferite a un comune reale inquinano i totali geografici.

## D-006 — datasets/ vs support/ per i 4 dataset OpenCUP

- **decisione:** OpenCUP Progetti sta in `datasets/` (main dataset), Localizzazione/Fonti/Soggetti
  stanno in `support/` (lookup tables). I support usano `type: http_file` + `extractor: unzip_first_csv`;
  Progetti usa `type: local_file` con parquet prodotto da `fetch_progetti.py`.
- **motivo:** Progetti è il dataset principale (11.94M CUP, 7 shard CSV da 14GB). I lookup sono
  tabelle di riferimento per join, non dataset analitici indipendenti. Il pattern è coerente
  con il project-template del Lab (`support/` per anagrafiche).
- **impatto:** `make run-all` processa sia `datasets/` che `support/`. `make run-seeds` processa
  solo `support/`. Il download di Progetti resta manuale (`make opencup`) per via della dimensione.
- **alternative:** tutto in `datasets/` (scartato: non rispetta il ruolo dei lookup);
  tutto in `support/` (scartato: Progetti non è un lookup).