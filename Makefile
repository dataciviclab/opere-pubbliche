# Opere Pubbliche Intelligence — Makefile
# Un solo entry point: pipeline.py. Niente cache: i layer Lab si leggono da GCS.
.PHONY: all opencup metrics layers panorama test check clean help

## Pipeline completa: metrics (fonti Lab) + layers (mart + aggregati)
all: metrics layers panorama

## Fonte di dominio: scarica OpenCUP (4 zip) e converte in parquet
## (opencup/data/raw → opencup/data/parquet). Mensile, solo quando la fonte cambia.
opencup:
	python3 opencup/scripts/download_opencup.py --out opencup/data/raw
	python3 opencup/scripts/convert_to_parquet.py --raw opencup/data/raw --out opencup/data/parquet

## Step 1: materializza le metriche per CUP dai layer Lab (GCS direct-read).
## Da usare quando la fonte Lab è cambiata (refresh mensile) o per rebuild deliberato.
metrics:
	python3 pipeline.py --step metrics

## Step 2: cup_fatti (unico mart) + aggregati comune/regione/settore. Comando quotidiano.
layers:
	python3 pipeline.py --step layers

## Deliverable: panorama in data/reporting/ (md + json)
panorama:
	mkdir -p data/reporting
	python3 reports/panorama.py

## Test di integrità (antidoto alle regressioni). Richiede i layer già prodotti.
test:
	python3 test_smoke.py

## Validazione statica: byte-compile dei .py + esecuzione delle query del catalogo
check:
	@python3 -m compileall -q pipeline.py reports/panorama.py opencup/scripts test_smoke.py
	@echo "✅ byte-compile ok"
	@test -f data/cup/cup_fatti.parquet && python3 test_smoke.py || echo "layer non presenti — esegui prima: make layers"
	@echo "✅ check completato"

## Helptext
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort

## Pulizia degli artefatti (fuori git)
clean:
	rm -rf data/build data/cup data/aggregati data/reporting
