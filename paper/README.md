# SoftwareX Paper: OpenDSS MCP Server

This directory contains the SoftwareX journal paper submission for OpenDSS MCP Server.

## Files

- `opendss_mcp_softwarex.tex` - Main LaTeX source file
- `Makefile` - Build automation
- `opendss_mcp_softwarex.pdf` - Compiled PDF (generated)
- `opendss_mcp_softwarex.bbl` - Bibliography (generated)

## Structure

The paper follows the SoftwareX template with the following sections:

1. **Title**: OpenDSS MCP Server: Conversational Distribution System Analysis with Large Language Models
2. **Abstract** (200 words): Problem, solution, results, impact
3. **Keywords**: Power systems, OpenDSS, MCP, AI, distribution planning
4. **Section 1 - Motivation and Significance**: Problem statement, gap analysis, contribution
5. **Section 2 - Software Description**: Architecture, tools, functionalities, metadata
6. **Section 3 - Illustrative Example**: Kuwait utility use case with conversational workflow
7. **Section 4 - Impact**: Performance benchmarks, workflow improvement, deployment impact
8. **Section 5 - Conclusions**: Summary, limitations, future work
9. **References**: 13 citations

## Key Features

### Software Metadata Table
Complete metadata following SoftwareX requirements:
- Version: v1.0.0
- License: MIT
- Language: Python 3.10+
- Dependencies: mcp, opendssdirect.py, pandas, numpy, matplotlib, networkx
- Test coverage: 78% (220 tests)

### Architecture Diagram
TikZ diagram showing three-layer architecture:
- Layer 1: Claude Desktop (natural language interface)
- Layer 2: MCP Server with 7 tools
- Layer 3: OpenDSS engine

### Performance Benchmarks
Comparison against target specifications:
- Power flow: 0.3 ms (16,667× faster than target)
- DER optimization: 5.2 ms (5,769× faster)
- Time-series: 1.5 ms (40,000× faster)

### Validation Table
Results comparison with traditional scripting:
- All metrics within 3% accuracy
- Optimal bus rankings match exactly

### Workflow Comparison
Traditional (56 hours) vs. MCP Server (32 minutes):
- 105× workflow acceleration
- Real-world deployment: 100+ feeders analyzed

## Compilation

### Requirements

Install LaTeX distribution:

**macOS:**
```bash
brew install --cask mactex
```

**Ubuntu/Debian:**
```bash
sudo apt-get install texlive-full
```

**Windows:**
Download MikTeX from https://miktex.org/

### Build Instructions

```bash
# Compile PDF
make

# Clean auxiliary files
make clean

# Clean everything including PDF
make cleanall

# View PDF (macOS)
make view
```

### Manual Compilation

```bash
# First pass
pdflatex opendss_mcp_softwarex.tex

# Bibliography
bibtex opendss_mcp_softwarex

# Second pass (resolve references)
pdflatex opendss_mcp_softwarex.tex

# Third pass (finalize)
pdflatex opendss_mcp_softwarex.tex
```

## SoftwareX Requirements

This paper meets all SoftwareX requirements:

✅ **Original Software Paper** format
✅ Software metadata table included
✅ Code repository link (GitHub)
✅ Software license specified (MIT)
✅ Installation instructions (via reference to main README)
✅ Example usage with code listings
✅ Performance benchmarks
✅ Validation results
✅ Impact statement
✅ Data availability statement
✅ Declaration of competing interests

## Submission Checklist

Before submitting to SoftwareX:

- [ ] Compile PDF successfully
- [ ] Verify all figures render correctly
- [ ] Check all references are formatted properly
- [ ] Ensure line numbers are visible (review mode)
- [ ] Validate metadata table completeness
- [ ] Confirm software version matches paper (v1.0.0)
- [ ] Test all URLs are accessible
- [ ] Run plagiarism check
- [ ] Obtain any required institutional approvals
- [ ] Prepare cover letter

## Journal Information

**Journal**: SoftwareX
**Publisher**: Elsevier
**Submission**: https://www.editorialmanager.com/softx/
**Template**: Elsarticle class (review mode)
**Article Type**: Original Software Paper
**Typical Length**: 6-8 pages

## Citation

Once published, cite as:

```bibtex
@article{elshazly2025opendss,
  title={OpenDSS MCP Server: Conversational Distribution System Analysis with Large Language Models},
  author={El-Shazly, Ahmed},
  journal={SoftwareX},
  year={2025},
  publisher={Elsevier},
  note={In press}
}
```

## License

This paper describes software licensed under MIT. The paper text itself is:
- Copyright © 2025 Ahmed El-Shazly
- Submitted to SoftwareX (Elsevier) under their standard author agreement
- Post-publication, authors retain rights per Elsevier policy

## Contact

**Author**: Ahmed El-Shazly
**Email**: ahmedelshazly27@gmail.com
**ORCID**: (Add your ORCID if you have one)
