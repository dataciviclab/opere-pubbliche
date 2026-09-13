# Opere Pubbliche Intelligence — Makefile
# Convenzione (ADR-001, modello multi-dataset):
#   datasets/  = dataset principali (anagrafe OpenCUP + SILOS)
#   support/   = lookup OpenCUP (fonti, localizzazione, soggetti)
#   compose/   = cross-dataset compose (cup-lab con tutti gli attributi)
TOOLKIT = toolkit

# --- Dataset del repo -------------------------------------------------------
DATASETS := $(shell find datasets support -name dataset.yml 2>/dev/null | sort)
COMPOSE  := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Run toolkit ------------------------------------------------------------

.PHONY: run
run:
	@for f in $(DATASETS); do \
		echo "=== $$f ==="; \
		TOOLKIT_ALLOW_SCRIPT_SOURCE=1 $(TOOLKIT) run --config "$$f" || exit 1; \
	done

.PHONY: compose
compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

.PHONY: run-all
run-all: run compose

# --- Validazione config ------------------------------------------------------

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

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
