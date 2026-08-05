# Opere Pubbliche Intelligence — Makefile
# Un solo entry point: pipeline.py. Niente cache: i layer Lab si leggono da GCS.
.PHONY: metrics layers all panorama clean

# Pipeline completa: metrics (fonti Lab) + layers (mart + aggregati)
all: metrics layers panorama

# Step 1: materializza le metriche per CUP dai layer Lab (GCS direct-read).
# Da usare quando la fonte Lab è cambiata (refresh mensile) o per rebuild deliberato.
metrics:
	python3 pipeline.py --step metrics

# Step 2: cup_fatti (unico mart) + aggregati comune/regione/settore. Comando quotidiano.
layers:
	python3 pipeline.py --step layers

# Deliverable: panorama in data/reporting/ (md + json)
panorama:
	mkdir -p data/reporting
	python3 reports/panorama.py

clean:
	rm -rf data/build data/cup data/aggregati data/reporting
