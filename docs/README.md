# Docs

Documentazione locale di Opere Pubbliche Intelligence. Per gli standard del Lab
e riferimenti organizzativi vedi [lab_links.md](lab_links.md).

Il repo è un **verticale consumer** (vedi convenzione del Lab): il dato pulito del
Lab si consuma da GCS, il lavoro qui è join + aggregazione + lettura. Il motore
condiviso (path contract GCS, HTTP client) vive in `lab-connectors`.

## Essenziali

- [overview.md](overview.md) — dominio, unità di analisi, copertura, limiti
- [sources.md](sources.md) — fonti ufficiali, URL, licenze, frequenza
- [data_dictionary.md](data_dictionary.md) — schema del mart e degli aggregati
- [decisions.md](decisions.md) — decisioni e trade-off (perché questo repo è fatto così)
- [join-cup-anac-rules.md](join-cup-anac-rules.md) — regole di cardinalità CUP→ANAC
- [contributing.md](contributing.md) — come contribuire

## Dove scrivere cosa

- bug o proposte su questo repo → Issues / Discussions qui
- problemi del path contract GCS o di config DuckDB condivisa → `lab-connectors`
- contesto generale del Lab → `dataciviclab`
- policy comuni e community health files → `.github`