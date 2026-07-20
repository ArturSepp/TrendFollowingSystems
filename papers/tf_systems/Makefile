PY    ?= python3
PAPER  = paper
REPL   = replication

.PHONY: help paper figures verify clean

help:
	@echo "Targets:"
	@echo "  make paper    - compile paper/TrendFollowing_PaperA_SIFIN_v1.pdf (3x pdflatex, no BibTeX)"
	@echo "                  siamonline250211.cls is committed in paper/"
	@echo "  make figures  - re-render the manuscript figures from the committed caches"
	@echo "  make verify   - run the fast verification gates"
	@echo "  make clean    - remove LaTeX build artifacts"

paper:
	cd $(PAPER) && pdflatex -interaction=nonstopmode TrendFollowing_PaperA_SIFIN_v1.tex && pdflatex -interaction=nonstopmode TrendFollowing_PaperA_SIFIN_v1.tex && pdflatex -interaction=nonstopmode TrendFollowing_PaperA_SIFIN_v1.tex

figures:
	cd ../.. && $(PY) -m papers.tf_systems.replication.reproduce_all_figures

verify:
	cd $(REPL) && PYTHONPATH=../../.. $(PY) verify_arfima_variance_scale.py && PYTHONPATH=../../.. $(PY) ewma_variance_check.py

clean:
	rm -f $(PAPER)/*.aux $(PAPER)/*.log $(PAPER)/*.out $(PAPER)/*.synctex.gz
