# Opere Pubbliche Intelligence — Makefile
# Pattern: come terzo-settore-intelligence (entry point unico, deliverable in data/reporting/).
.PHONY: build unified layers views cache refresh panorama all clean

all: build panorama

# Pipeline completa: unified + 3 strati + view aggregate
build: unified layers views

# Cache del layer clean Lab grande (anac, opencoesione) — una tantum, evita egress GCS
cache:
	mkdir -p data/cache
	python3 build/cache_lab.py

# Strato 1+3: unified per CUP (da OpenCup + join Lab)
unified:
	python3 build/build_unified.py

# Strato 2: cup_fatti + aggregati (comune/regione/settore)
layers:
	python3 build/build_layers.py

# Refresh leggero: pagamenti in cup_fatti + aggregati (senza rifare il unified)
refresh:
	python3 build/refresh_layers.py

# View aggregate materializzate (leggere, in data/views/)
views:
	python3 build/materialize_views.py

# Deliverable: panorama in data/reporting/ (md + json)
panorama:
	mkdir -p data/reporting
	python3 reports/panorama.py

clean:
	rm -rf data/unified_operas.parquet data/cup data/aggregati data/views data/reporting
