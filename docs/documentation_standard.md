---
myst:
  html_meta:
    description: >-
      Authoring rules for the trendfollowing handbook: page forms and the eight-row convention
      card, reserved notation, portable mathematics, executed worked examples, the single
      bibliography, API coverage, figure provenance and the verification commands.
---

# Documentation standard

*Author: [Artur Sepp](https://github.com/ArturSepp)*

This standard applies to [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

This is the trendfollowing supplement to the
[shared OSS documentation standard](https://github.com/ArturSepp/ArturSepp/blob/main/docs/documentation_standard.md).
The shared guide owns the common authoring rules; this page records the conventions of the
trendfollowing handbook, which follows the design of the
[qis](https://quantinveststrats.readthedocs.io/) and
[optimalportfolios](https://optimalportfolios.readthedocs.io/) handbooks, and the checks that
enforce them. General changes belong in the shared guide.

## Page forms

Four page forms exist:

- A **methodology chapter** has the eight H2 sections of the shared template, in order, with the
  H2 `Implementation in trendfollowing`: Overview; Inputs, notation, and assumptions; Methodology;
  Worked example; Implementation in trendfollowing; Interpretation and limitations; See also;
  References.
- A **case study** reports a study of the package's paper, in the form of the optimalportfolios
  case studies: Overview; Study design and data; Configuration; Results; What the study does and
  does not show; Reproduce; See also; References. Results are quoted from the paper with their
  study design and are never recomputed; its Python block builds the configuration and
  demonstrates the mechanism on synthetic data.
- A **guide** is a task-oriented page that predates the handbook: the quickstart, the closed-form
  analytics guide, the attribution guide, the system comparison, the example workflows and the
  package comparison. Guides keep their headings and the wording that `tests/test_examples.py`
  and `tests/test_docs_foundation.py` check, and link to the chapters for methodology.
- A **utility page** (home, installation, API reference, bibliography, paper map and this
  standard) has a byline, the software-citation line and a metadata description, and no empty
  sections.

`tests/test_documentation_handbook.py` lists the methodology chapters and the case study and checks
their structure.

## Handbook conventions

- **Convention card.** The first table under *Inputs, notation, and assumptions* of a methodology
  chapter has the header `| Convention | This article |` and exactly these rows, in order: Return
  basis, Normalisation, Signal filter, Moment basis, Annualisation, Timing, Costs,
  trendfollowing default. The [notation chapter](notation_and_conventions.md) defines each row.
- **Reserved notation.** The symbols of the [notation chapter](notation_and_conventions.md) keep
  one meaning in every chapter. The annualisation factor is $\mathrm{af}$, as in qis and
  optimalportfolios, where the paper writes $a$. A local symbol is declared in the chapter's
  notation table and never reuses a reserved one.
- **Results and concise proofs.** A result is stated in a paragraph opening with a bold
  **Definition.**, **Identity.**, **Lemma.**, **Proposition.** or **Corollary.** label, cites the
  section of the paper where it comes from it, and is followed by a short **Proof.** ending in
  $\square$. Longer derivations are cited, not reproduced.
- **Insight and Pitfall callouts.** Write `> **Insight.** ...` or `> **Pitfall.** ...` as an
  ordinary blockquote; `docs/_ext/trendfollowing_callouts.py` renders it as an admonition in
  Sphinx, and GitHub shows a quotation. A Pitfall documents the behaviour of the code as it is;
  a suspected defect is reported, not silently fixed in the documentation.
- **Executed worked examples.** Every `python` block of a methodology chapter or the case study
  runs offline in `tests/test_documentation_examples.py`, in one namespace per page, and asserts
  every number the page quotes against a reference computed a different way: a closed form, an
  independent NumPy calculation or a Monte Carlo estimate with its standard error. A schematic
  block that cannot run carries the comment `<!-- docs-test: skip -->` on the line before its
  fence. Seeds are fixed with `numpy.random.default_rng`.
- **One bibliography.** [The bibliography](bibliography.md) holds every cited work once. A
  chapter's References section is a numbered list whose items begin with a bibliography entry
  verbatim, optionally followed by a sentence on what the work contributes, and it includes the
  trendfollowing software citation. Each DOI is checked against its Crossref record before it is
  added; entries without a DOI carry `[pending publisher check]` until checked.
- **API coverage.** Every top-level export of `trendfollowing` appears in the
  [API reference](api.md), which documents each object in the section of the chapter that explains
  it. Chapters link to it with `{py:func}` and `{py:class}` roles, which the strict build resolves.
- **Spelling.** Prose uses British spelling; Python names keep their published American spelling.

## Portable mathematics

Follow the shared
[portable mathematics rules](https://github.com/ArturSepp/ArturSepp/blob/main/docs/documentation_standard.md#user-content-portable-mathematics).
MyST's `dollarmath` extension is enabled in `docs/conf.py`. Because GitHub applies Markdown
escapes before rendering math, spell every command with letters: write `\lvert x \rvert`,
`\lbrace` and `\rbrace`, and avoid the thin space written as backslash-comma. In inline math write
`\lt` and `\gt` for the comparison signs, attach subscripts to a letter (`\mu_{\mathrm{an}}`, not a
subscript after a closing brace), and never start a line of a display block with `+`, `-`, `*`,
`>` or `#`. Put display equations in paragraphs, not inside list items.

## The paper and its numbering

The package's paper, Sepp and Lucic (2026), is a public working paper on SSRN and arXiv. Chapters
cite it by section, appendix, figure and table numbers of the tracked SIFIN manuscript in
`papers/tf_systems/paper/`, and quote its results with their study design. Numbers in a worked
example are computed on the page; numbers attributed to the paper are quoted, not recomputed, and
a mismatch between the two is reported rather than reconciled by editing either.

## Figures

The site displays only the twelve approved manuscript figures tracked in
`papers/tf_systems/paper/figures/`, referenced by relative path. Each caption states what the
figure shows, its figure number in the paper and its generator under
`papers/tf_systems/replication/`, as mapped by the `PaperFigure` enum of `reproduce_all_figures.py`;
the alt text describes the comparison. New generated images, including teaching figures in the
style of the qis handbook, need an explicit publication decision and an exact allowlist entry, as
the repository's [AGENTS.md](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/AGENTS.md)
requires; the worked examples therefore assert numbers instead of drawing charts.

## Verification

In the prescribed external environment, run:

```console
python -m pytest tests/test_documentation_handbook.py tests/test_documentation_examples.py -q
python -m sphinx -E -W --keep-going -b html docs <external-output>/html
python -m sphinx -E -W -b linkcheck docs <external-output>/linkcheck
```

The HTML build is strict and nitpicky: unresolved references into `trendfollowing` fail it, while
references into NumPy, pandas, qis and the standard library are not checked offline. Build from a
source export outside a synchronised folder when the checkout lives in one. The link check needs the
network and runs separately, as in the documentation workflow. Source checks, executed examples,
the rendered site and the visual review of equations are different outcomes; record which were
performed.

## See also

- [Documentation home](index.md)
- [Notation and conventions](notation_and_conventions.md)
- [Bibliography](bibliography.md)
- [API reference](api.md)
- [Contributor guidance](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/AGENTS.md)
