# Opere Pubbliche Intelligence — Makefile
# Convenzione (ADR-001, modello multi-dataset):
#   datasets/  = dataset principali (anagrafe OpenCUP)
#   support/   = lookup OpenCUP (fonti, localizzazione, soggetti)
#   compose/   = cross-dataset compose (fonti Lab, cup_fatti, panorama)
# Il toolkit gestisce fetch→clean→mart; gli script Python gestiscono
# download OpenCUP (fetch_progetti.py) e deliverable speciali.
TOOLKIT = toolkit

# --- Dataset del repo -------------------------------------------------------
DATASETS := $(shell find datasets support -name dataset.yml 2>/dev/null | sort)
COMPOSE  := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Fetch OpenCUP (manuale, mensile) ---------------------------------------
# Progetti: script fetch+extract+merge → out/raw (per toolkit)

.PHONY: opencup
opencup:
	TOOLKIT_ALLOW_SCRIPT_SOURCE=1 $(TOOLKIT) run --config datasets/opencup-progetti/dataset.yml

# --- Compose (eseguire dopo i dataset singoli) ------------------------------

.PHONY: compose
compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

# --- Dataset principali ------------------------------------------------------

.PHONY: run
run:
	@for f in $(DATASETS); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

.PHONY: run-all
run-all: run compose

# --- Validazione config -------------------------------------------------------

.PHONY: check
check:
	@for f in $(DATASETS) $(COMPOSE); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Test --------------------------------------------------------------------

.PHONY: test
test:
	python3 -m pytest tests/ -v

# --- Registry ----------------------------------------------------------------

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix opere_pubbliche

registry-write:
	$(TOOLKIT) registry build --prefix opere_pubbliche --write

# --- Pulizia -----------------------------------------------------------------

.PHONY: clean
clean:
	rm -rf out/data/_runs out/data/probe out/data/raw out/data/clean out/data/mart out/data/cross

.PHONY: clean-data
clean-data:
	rm -rf data/build data/cup data/aggregati data/reporting

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
