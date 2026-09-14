# Opere Pubbliche Intelligence — Makefile
# Ordine: support → datasets → compose
# Il toolkit esegue i support prima dei dataset che li dichiarano.
TOOLKIT = toolkit

# Abilita source type `script` del toolkit (download OpenCUP, SILOS)
export TOOLKIT_ALLOW_SCRIPT_SOURCE ?= 1

# --- Dataset del repo -------------------------------------------------------
SUPPORT  := $(shell find support -name dataset.yml 2>/dev/null | sort)
DATASETS := $(shell find datasets -name dataset.yml 2>/dev/null | sort)
COMPOSE  := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Run toolkit (support → datasets → compose) -----------------------------

.PHONY: run
run:
	@for f in $(SUPPORT); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done
	@for f in $(DATASETS); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done
	@for f in $(COMPOSE); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

.PHONY: run-all
run-all: run

# --- Validazione config ------------------------------------------------------

.PHONY: check
check:
	@for f in $(SUPPORT) $(DATASETS) $(COMPOSE); do \
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
