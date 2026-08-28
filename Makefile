# Opere Pubbliche Intelligence — Makefile
# Pipeline toolkit (dataset.yml) + script analitici.
# Convenzione Lab: toolkit gestisce fetch→clean→mart; gli script
# Python gestiscono metriche, cup_fatti, panorama.
TOOLKIT = toolkit

# --- Dataset del repo -------------------------------------------------------
DATASETS := $(shell find datasets support -name dataset.yml 2>/dev/null | sort)

# --- Fetch OpenCUP (manuale, mensile) ---------------------------------------
# Progetti: script fetch+extract+merge → out/raw (per toolkit)
# Localizzazione/Fonti: toolkit scarica nativamente da HTTP

.PHONY: opencup
opencup:
	python3 opencup/scripts/fetch_progetti.py

# --- Run toolkit ------------------------------------------------------------

.PHONY: run
run:
	$(TOOLKIT) run --batch batch.txt

.PHONY: run-seeds
run-seeds:
	@find support -name dataset.yml | sort > batch.txt; \
	$(TOOLKIT) run --batch batch.txt

.PHONY: run-all
run-all:
	@find datasets support -name dataset.yml | sort > batch.txt; \
	TOOLKIT_ALLOW_SCRIPT_SOURCE=1 $(TOOLKIT) run --batch batch.txt

# --- Validazione config ------------------------------------------------------

.PHONY: check
check:
	@for f in $(DATASETS); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Script analitici (leggono da GCS + out/) -------------------------------

.PHONY: metrics
metrics:
	python3 scripts/metriche_anac.py

.PHONY: layers panorama
layers:
	python3 scripts/cup_fatti.py

panorama:
	python3 scripts/panorama.py

# --- Pipeline completa: toolkit + analitici + test ----------------------------

.PHONY: all
all: run-all metrics layers panorama test

# --- Test --------------------------------------------------------------------

.PHONY: test
test:
	python3 -m pytest tests/ -v

# --- Registry ----------------------------------------------------------------

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix opere_pubbliche_intelligence --flat

registry-write:
	$(TOOLKIT) registry build --prefix opere_pubbliche_intelligence --flat --write

# --- Pulizia -----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart

.PHONY: clean-data
clean-data:
	rm -rf data/build data/cup data/aggregati data/reporting

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
