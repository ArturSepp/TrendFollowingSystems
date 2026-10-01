PY ?= python3

.PHONY: help paper figures reproduce verify

help:
	@echo "Set PY to the configured external interpreter. Outputs stay outside the checkout."
	@echo "paper: compile approved manuscript assets in external latex-build/"
	@echo "figures: render five exhibits from frozen caches"
	@echo "reproduce: full generator, including expensive simulations"
	@echo "verify: existing analytical gates"

paper:
	cd ../.. && $(PY) -m papers.tf_systems.replication.build_paper

figures:
	cd ../.. && $(PY) -m papers.tf_systems.replication.cached_figures

reproduce:
	cd ../.. && $(PY) -m papers.tf_systems.replication.reproduce_all_figures

verify:
	cd ../.. && $(PY) -m papers.tf_systems.replication.verify_arfima_variance_scale
	cd ../.. && $(PY) -m papers.tf_systems.replication.ewma_variance_check
