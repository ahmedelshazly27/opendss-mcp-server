# Makefile for SoftwareX Paper Compilation

# Configuration
PAPER = opendss_mcp_softwarex
LATEX = pdflatex
BIBTEX = bibtex
VIEWER = open  # macOS; use 'evince' on Linux, 'start' on Windows

# Default target
all: $(PAPER).pdf

# Compile PDF (full build with bibliography)
$(PAPER).pdf: $(PAPER).tex
	@echo "==> First LaTeX pass..."
	$(LATEX) $(PAPER).tex
	@echo "==> Running BibTeX..."
	$(BIBTEX) $(PAPER)
	@echo "==> Second LaTeX pass..."
	$(LATEX) $(PAPER).tex
	@echo "==> Third LaTeX pass (finalizing)..."
	$(LATEX) $(PAPER).tex
	@echo "==> PDF compiled successfully: $(PAPER).pdf"

# Quick compile (no bibliography update)
quick: $(PAPER).tex
	@echo "==> Quick compile (single pass)..."
	$(LATEX) $(PAPER).tex

# View PDF
view: $(PAPER).pdf
	$(VIEWER) $(PAPER).pdf

# Clean auxiliary files
clean:
	@echo "==> Cleaning auxiliary files..."
	rm -f $(PAPER).aux
	rm -f $(PAPER).bbl
	rm -f $(PAPER).blg
	rm -f $(PAPER).log
	rm -f $(PAPER).out
	rm -f $(PAPER).toc
	rm -f $(PAPER).lof
	rm -f $(PAPER).lot
	rm -f $(PAPER).fls
	rm -f $(PAPER).fdb_latexmk
	rm -f $(PAPER).synctex.gz
	rm -f $(PAPER).run.xml
	rm -f $(PAPER)-blx.bib
	@echo "==> Cleaned!"

# Clean everything including PDF
cleanall: clean
	@echo "==> Removing PDF..."
	rm -f $(PAPER).pdf
	@echo "==> All files cleaned!"

# Word count (approximate)
wordcount:
	@echo "==> Approximate word count:"
	@detex $(PAPER).tex | wc -w

# Check for LaTeX errors
check:
	@echo "==> Checking for common LaTeX errors..."
	@grep -n "TODO" $(PAPER).tex || echo "No TODOs found"
	@grep -n "XXX" $(PAPER).tex || echo "No XXX markers found"
	@grep -n "FIXME" $(PAPER).tex || echo "No FIXMEs found"

# Spell check (requires aspell)
spell:
	@echo "==> Running spell check..."
	aspell -t -c $(PAPER).tex

# Help
help:
	@echo "Available targets:"
	@echo "  make          - Compile PDF with bibliography (default)"
	@echo "  make quick    - Quick compile (single pass, no bib)"
	@echo "  make view     - Open compiled PDF"
	@echo "  make clean    - Remove auxiliary files"
	@echo "  make cleanall - Remove all generated files including PDF"
	@echo "  make wordcount- Count words in document"
	@echo "  make check    - Check for TODO/XXX/FIXME markers"
	@echo "  make spell    - Run spell checker (requires aspell)"
	@echo "  make help     - Show this help message"

.PHONY: all quick view clean cleanall wordcount check spell help
