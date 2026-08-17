# TrendFollowingSystems discoverability and adoption roadmap

Version 1.0, 2026-08-16

Source: adapted from
`C:\Users\artur\OneDrive\analytics\my_github\.agents\ROADMAP_OSS_DISCOVERABILITY_AND_ADOPTION.md`.

Status: execution in progress. U0 and the public-data portion of U1 were recorded on 2026-08-16;
M1, M2, U2, U3a, Maintainer Gate A, U3b, and U6 passed on 2026-08-16. U4a passed on
2026-08-17. The next implementation stage is U4b.

## Outcome

Make `trendfollowing` easy to discover, install, evaluate, and cite as the Python replication
package for *The Science and Practice of Trend-Following Systems*. A qualified new user should
be able to:

1. install the released wheel and run a deterministic analytical example;
2. understand when the European, American, and TSMOM implementations are appropriate;
3. reproduce an empirical workflow from the published futures data without a source-tree path
   accident; and
4. find the paper, conventions, public API, examples, verification evidence, and citation from
   one canonical documentation root.

The objective is qualified discovery followed by successful first use, not raw traffic or stars.

## Binding package decisions

These decisions adapt the portfolio roadmap to this repository and are mandatory.

1. **Migrate the installable package to a src layout.** Move `trendfollowing/` mechanically to
   `src/trendfollowing/`. Keep `tests/`, `papers/`, `resources/`, and `examples/` at the
   repository root. Do not combine the move with numerical or API changes.
2. **Keep user examples at the repository root.** `examples/` is the single public example
   location. Do not create `src/trendfollowing/examples`, a second copy under `docs/`, or
   notebook-only source code.
3. **Make the wheel contract truthful.** The 1.0.5 wheel is 67.8 kB and contains no futures
   CSVs, while the README says the empirical dataset is packaged. The recommended resolution is
   to move the immutable futures files into `src/trendfollowing/resources/futures/`, include
   them as package data, and load them through `importlib.resources`, while preserving
   `TF_RESOURCE_PATH` as the explicit override. If the maintainer rejects the larger wheel, the
   alternative is to label empirical examples as checkout-only and remove every packaged-data
   claim. Do not leave the present contradiction.
4. **Preserve scientific results.** No formulas, seeds, universe definitions, data bytes,
   backtest semantics, public call signatures, or reported values change under this roadmap.
5. **Keep replication code at the root.** `papers/` remains importable as `papers.*` from a
   checkout and is not installed as part of `trendfollowing`.
6. **Use `qis` for shared analytics and reporting.** This package remains a consumer of `qis`;
   no parallel performance-statistics or backtesting layer is introduced.
7. **Do not release implicitly.** Metadata, README, package-data, or layout changes reach PyPI
   only through an explicitly approved release after U8 passes.

If execution discovers that the src migration, data packaging, or a documentation claim changes a
numerical result, stop and report the mismatch. Do not update expected values to make it pass.

## Package adaptation profile

| Field | Package-specific answer |
|---|---|
| Distribution name | `trendfollowing` |
| Import name | `trendfollowing` |
| Current release | 1.0.5, released on PyPI 2026-08-01 |
| One-sentence role | Closed-form trend-following analytics, reference system implementations, and reproducible futures evidence in Python for quantitative researchers and practitioners |
| Primary users | Quantitative researchers, systematic-futures practitioners, and reviewers reproducing Sepp and Lucic (2026) |
| Priority task 1 | Compute expected return, Sharpe ratio, skewness, and turnover from white-noise, AR(1), ARFIMA, or empirical autocorrelation inputs |
| Priority task 2 | Select or interpret a trend-filter span under predictability, drift, and trading costs |
| Priority task 3 | Compare European, American, and TSMOM systems and reproduce the published futures evidence |
| Differentiating workflow | Link sample autocorrelation and drift to closed-form and realized trend-following performance, with Monte Carlo and 84-contract empirical verification |
| Canonical repository | `https://github.com/ArturSepp/TrendFollowingSystems` |
| Canonical documentation now | GitHub README only |
| Canonical documentation target | `https://artursepp.github.io/TrendFollowingSystems/`, subject to Gate A approval |
| Package index | `https://pypi.org/project/trendfollowing/` |
| Documentation system | None now; proposed Sphinx/MyST static site on GitHub Pages |
| First-success archetype | Offline library |
| First-success contract | Released wheel, no network or credentials, deterministic closed-form result in less than one minute |
| Empirical contract | Recommended: immutable futures data in the wheel; `TF_RESOURCE_PATH` remains an override |
| Release authority | Artur Sepp; PyPI and GitHub credentials required |
| Existing analytics | PyPI, GitHub, and Pepy badge; Search Console and docs analytics unknown |
| Scientific boundary | The paper, submission state, DOI, and journal process are separate; this roadmap may link and cite them but cannot claim acceptance or alter scientific results |
| Proceed/defer | Proceed: functionality is mature, the paper provides qualified demand, and first-use/distribution gaps are concrete |

## Canonical identity

Proposed public sentence:

> `trendfollowing` — closed-form trend-following analytics, reference system implementations,
> and reproducible futures evidence in Python for quantitative researchers and practitioners.

Proposed boundary sentence:

> It is a research and replication library, not a broker integration or general-purpose execution
> engine; portfolio analytics and reporting are delegated to `qis`.

Keep the exact distribution/import token `trendfollowing`. The repository name
`TrendFollowingSystems` may remain the GitHub project title.

## Current evidence that sets the priorities

The dated U1 report in `agents/DISCOVERABILITY_BASELINE.md` is authoritative. The main findings
that determine stage order are:

- the source package is at repository root, and `[tool.pytest.ini_options].pythonpath = ["."]`
  can mask packaging mistakes during checkout tests;
- `examples/` already exists at the repository root and contains three meaningful scripts, but
  there is no single wheel-tested, output-free quickstart;
- PyPI and the README instruct users to clone and install editable rather than lead with
  `pip install trendfollowing`;
- the README quickstart contains `daily_returns` without defining it, so the block is not
  runnable as one script;
- the 1.0.5 wheel contains package code and `settings.yaml` but no futures data;
- relative data paths resolve against the source checkout and do not establish an installed-wheel
  empirical workflow;
- `trendfollowing.__version__` is `1.0.0` while project, citation, README, tag, and PyPI say
  `1.0.5`;
- there is no independent documentation site, sitemap, canonical-page control, or task-level
  documentation entry point;
- GitHub, PyPI, the paper, examples, and package metadata do not yet form one short conversion
  path.

These are adoption and trust defects. They do not justify changes to the mathematical API.

## Artifacts

Public, candidate-for-commit execution contract:

```text
ROADMAP_DISCOVERABILITY_AND_ADOPTION.md
```

Local operational records under the untracked/ignored `agents/` directory:

```text
agents/README.md
agents/ADOPTION_PROFILE.md
agents/DISCOVERABILITY_BASELINE.md
agents/DISCOVERABILITY_AUDIT.md
agents/DISCOVERABILITY_90_DAY_REPORT.md
```

Credentials, Search Console exports, browser state, downloaded competitor material, and raw
analytics never enter the repository. Only redacted summaries belong in `agents/`.

## Global execution rules

- Execute and verify one stage at a time.
- Re-read every target file immediately before editing and preserve concurrent changes.
- A stage is complete only when its listed verification commands pass.
- Record the command, environment, and concise result in the status log.
- Use released public symbols in user documentation; verify every named symbol exists.
- State simple-return, excess-return, annualisation, lag, and in-sample conventions explicitly.
- A source example is authoritative. Documentation includes it mechanically or tests it; code is
  not copied by hand.
- Build and test both wheel and sdist. Editable-install success is insufficient.
- Run installed-artifact checks from a temporary directory outside the checkout.
- Do not add hard runtime dependencies for documentation, examples, or adoption measurement.
- Documentation dependencies may live in a `docs` optional extra.
- Keep generated HTML, figures, factsheets, downloaded data, notebook output, and analytics
  exports out of commits.
- Search observations are dated spot checks, not rank measurements.
- Comparisons use current primary sources and identify at least one use case that favors each
  genuine alternative.
- A version bump and release require explicit maintainer approval.

## Execution order

Master stage identifiers are retained, with two migration stages inserted before content work.
U6 is executed before U4 because the task pages must point to one verified source example.

| Order | Stage | Deliverable | Main gate |
|---:|---|---|---|
| 1 | U0 | Adaptation profile and proceed decision | Role and maintenance case are explicit |
| 2 | U1 | Dated discovery/conversion baseline | Pre-change evidence is fixed |
| 3 | M1 | Mandatory src-layout migration | Imports and tests no longer depend on root package placement |
| 4 | M2 | Installed-wheel data/resource contract | Empirical claim is reproducible or narrowed truthfully |
| 5 | U2 | Canonical identity and trust metadata | Public surfaces describe one package |
| 6 | U3a | Documentation foundation | Static docs build warning-free |
| 7 | Gate A | GitHub/About, Pages, Search Console | Credentialed public settings are approved |
| 8 | U3b | Deployed technical discoverability | Priority pages are reachable and indexable |
| 9 | U6 | Root first-success workflow | Clean wheel yields deterministic success |
| 10 | U4 | Three task-oriented documentation waves | Priority jobs are executable and interpretable |
| 11 | U5 | Neutral comparison/choice guide | Qualified users can decide fit |
| 12 | Gate B | Hosted-notebook decision | Default recommendation: defer |
| 13 | U7 | Optional thin notebook | Only if Gate B approves |
| 14 | U8 | Release, deploy, and trust alignment | Public artifacts match |
| 15 | U9 | 30/60/90-day measurement | Investment decision follows evidence |

---

## U0 — Triage and adapt

**Deliverable:** `agents/ADOPTION_PROFILE.md` and this roadmap.

Record the current release, dependency position, users, three priority tasks, offline first-success
contract, scientific boundary, documentation maturity, and maintenance decision.

**Acceptance:** the profile contains distinct positioning, concrete user tasks, a feasible
first-success path, and a proceed/defer decision.

**Verification:**

```powershell
Select-String -Path agents/ADOPTION_PROFILE.md -Pattern `
  'Distribution name','Primary user','Priority task','First-success','Proceed'
```

Manually compare the profile with `pyproject.toml`, `README.md`, `AGENTS.md`, package exports,
PyPI, GitHub About, root examples, and the `qis` dependency direction.

**Out of scope:** implementation, release, publication claims, and rebranding the package
portfolio.

## U1 — Establish the baseline

**Deliverable:** `agents/DISCOVERABILITY_BASELINE.md`.

Fix one dated snapshot before implementation:

- PyPI version, release date, artifact sizes, project links, description, and rendered README;
- GitHub canonical URL, About text/link, stars, forks, watchers, tags, and visible release state;
- current documentation topology and conversion path;
- branded query treatment and the three fixed non-branded task queries;
- wheel contents, src-layout state, root example state, and installed-data contract;
- Search Console, package-download, docs-referral, and citation data, marking unavailable values
  `unknown`;
- contradictions, broken paths, and adoption friction.

Fixed non-branded queries:

1. `trend following Sharpe ratio formula Python`
2. `predict trend following Sharpe autocorrelation Python`
3. `trend following systems Python backtest`

Branded means a query containing `trendfollowing` or `TrendFollowingSystems`, case-insensitive.

**Acceptance:** every value has a date and source family; unknown credentialed data remains
unknown; the report has `Indexing`, `Queries`, `Conversion path`, `Adoption signals`, and
`Limitations`.

**Verification:**

```powershell
$required = 'Indexing','Queries','Conversion path','Adoption signals','Limitations'
$text = Get-Content agents/DISCOVERABILITY_BASELINE.md -Raw
$required | ForEach-Object { if ($text -notmatch [regex]::Escape($_)) { throw "missing $_" } }
```

**Out of scope:** changing public settings while measuring the baseline.

## M1 — Mandatory migration to src layout

**Execution status (2026-08-16): PASS.** See `agents/M1_IMPLEMENTATION_REPORT.md`.

**Deliverable:** one mechanical layout commit whose only architectural change is the location of
the installable package.

Target layout:

```text
src/
    trendfollowing/
        __init__.py
        analysis/
        analytics/
        processes/
        systems/
        backtests.py
        conventions.py
        local_path.py
        settings.yaml
        universe.py
examples/                       remains at repository root
papers/                         remains at repository root
resources/                      paper resources remain at repository root
tests/                          remains at repository root by replication contract
```

Implementation requirements:

1. Use `git mv trendfollowing src/trendfollowing`; do not rewrite moved modules for style.
2. Configure setuptools explicitly:

   ```toml
   [tool.setuptools]
   package-dir = {"" = "src"}

   [tool.setuptools.packages.find]
   where = ["src"]
   include = ["trendfollowing*"]
   ```

3. Update coverage source to `src/trendfollowing`.
4. Keep top-level `tests/` and the `papers.*` checkout import contract. If `pythonpath = ["."]`
   remains for `papers.*`, add an import-provenance test so it cannot mask a root
   `trendfollowing/` directory.
5. Assert the old repository-root `trendfollowing/` directory is absent.
6. Update only path/layout references required by the move. Content and positioning changes wait
   for U2/U4.
7. Preserve all imports (`import trendfollowing...`) and public signatures.
8. Keep `examples/` at the root and add a structural test that fails if examples migrate into the
   installable package.
9. Update CI so one job tests a normal install and one artifact check imports from outside the
   checkout.

Failure-first tests:

- add a test that rejects a root-level `trendfollowing/` package, temporarily recreate an empty
  root package, observe failure, remove it, and record the evidence;
- add an installed-import provenance check, run it before installation to see it fail, then run
  it against the built wheel to pass.

Numerical preservation evidence:

- capture pre-move and post-move outputs for the closed-form smoke set;
- run the existing unit suite;
- run the ARFIMA variance-scale and EWMA normalization verification scripts;
- hash every moved source and data file before and after the mechanical move, accounting only for
  intentionally edited packaging/path files.

**Acceptance:**

- only `src/trendfollowing` supplies the installed package;
- `examples/`, `papers/`, and `tests/` remain at root;
- the public import path and signatures are unchanged;
- all tests and independent numerical gates pass with unchanged results;
- wheel and sdist contain exactly one `trendfollowing` package;
- a temporary working directory outside the checkout imports the built wheel successfully.

**Verification:**

```powershell
python -m pip install -e ".[dev]"
pytest tests/ -q
ruff check src/trendfollowing/local_path.py tests/test_concat_sort_convention.py `
  tests/test_src_layout.py
python -m papers.tf_systems.replication.verify_arfima_variance_scale
python -m papers.tf_systems.replication.ewma_variance_check
python -m build
python -m twine check dist/*
```

The repository-wide `ruff check src/trendfollowing/ tests/ examples/` command is recorded as an
informational baseline until its existing violations receive a separate cleanup. For M1, require
the intentionally edited/new Python files to pass and prove every other moved source file is
byte-identical. Do not turn a mechanical layout stage into a repository-wide style refactor.

Then create a clean virtual environment outside the checkout, install the wheel without `-e`,
change to a temporary directory, and run:

```python
from pathlib import Path
import trendfollowing as tf

assert "TrendFollowingSystems" not in str(Path(tf.__file__).resolve())
assert abs(tf.sharpe_ar1(phi=0.05, long_span=21) - 0.336) < 0.001
```

Use the repository's supported Python matrix and Windows/Linux/macOS CI. Record exact pre/post
numerical values rather than relying only on rounded README values.

**Out of scope:** data redistribution, docs content, formula changes, test relocation, package
renaming, dependency changes, version bump, and release.

## M2 — Make the installed data/resource contract truthful

**Execution status (2026-08-16): PASS.** See `agents/M2_IMPLEMENTATION_REPORT.md`.

**Deliverable:** a separate packaging change resolving the current mismatch between public claims
and built artifacts.

Recommended implementation:

1. Move the immutable futures dataset from `resources/futures/` to
   `src/trendfollowing/resources/futures/` as package data. Keep paper caches and replication
   working material under root `resources/papers/`.
2. Preserve every futures file byte-for-byte and record SHA-256 hashes before and after.
3. Resolve the default dataset with `importlib.resources.files("trendfollowing")`; retain
   `TF_RESOURCE_PATH` as the explicit external override.
4. Remove instructions to edit `settings.yaml` inside `site-packages`. Package installation must
   be immutable.
5. Keep output and paper-cache destinations external to the package. Never write inside the
   installed package directory.
6. Include the intended data globs explicitly in setuptools configuration and test wheel/sdist
   manifests.
7. Update the README/data notes only enough to state the actual installed behavior.

The baseline futures directory is approximately 49.25 MiB uncompressed. Record the resulting
wheel/sdist sizes and PyPI limit margin. Size alone is not a reason to silently omit the files.

If the maintainer rejects data in the core wheel, stop and approve an alternate contract before
editing:

- retain data at repository root;
- call it checkout-only rather than packaged;
- make the analytical quickstart the sole offline wheel contract;
- make empirical examples fail with one actionable message naming `TF_RESOURCE_PATH`;
- remove claims that `pip install trendfollowing` includes the dataset.

Do not invent an automatic network downloader or a second data distribution under this roadmap.

Failure-first test:

- install the current 1.0.5 wheel in a clean environment and record that
  `trendfollowing.universe.load_data()` cannot find the dataset;
- run the same test against the candidate wheel and require the 84-contract checks to pass.

**Acceptance for the recommended contract:**

- the built wheel contains the documented futures files;
- `load_data()` works outside the checkout without an environment variable;
- `TF_RESOURCE_PATH` overrides the bundled dataset;
- package code never writes to bundled resources;
- shapes, dates, columns, costs, and data hashes match the pre-migration baseline;
- paper replication modules continue to consume the same public loader;
- README, package metadata, and artifact contents agree.

**Verification:**

```powershell
pytest tests/test_universe.py -q
pytest tests/ -q
python -m build
python -m twine check dist/*
```

In a clean wheel environment outside the checkout:

```python
from trendfollowing.universe import load_data

prices, costs, benchmarks, description, groups = load_data()
assert prices.shape[1] == 84
assert costs.shape == prices.shape
assert list(benchmarks.columns) == ["60/40 Equity/Bond", "SG Trend"]
assert description.index.equals(prices.columns)
assert groups[0] == "Equities"
```

Run a second check with `TF_RESOURCE_PATH` pointing to a temporary fixture and confirm that the
override, not the bundled path, is used.

**Out of scope:** changing data, adding live-data access, regenerating the universe, changing
published sample periods, or moving paper caches into the wheel.

## U2 — Establish one canonical identity and repair trust metadata

**Execution status (2026-08-16): PASS.** See `agents/U2_IMPLEMENTATION_REPORT.md`.

**Deliverable:** one focused identity/trust commit after M1 and M2.

Align:

- `[project].description`, keywords, and URLs;
- README title, first paragraph, installation path, and package/repository layout;
- documentation landing title and description;
- GitHub About text at Gate A;
- citation metadata and the unreleased changelog;
- `qis` dependency floor stated in README and `pyproject.toml`;
- the package version reported at runtime.

Replace the stale literal `trendfollowing.__version__ == "1.0.0"` with one authoritative version
source, preferably `importlib.metadata.version("trendfollowing")`, and add a test that installed
runtime metadata agrees with `pyproject.toml`, `CITATION.cff`, and the README software citation.
Treat the corrected public value as a release-visible trust fix and document it.

Lead installation with:

```bash
pip install trendfollowing
```

Keep editable installation in a contributor/development section.

**Acceptance:** primary surfaces use the canonical sentence and boundary, dependencies and
versions do not contradict one another, and no capability claim exceeds a tested artifact.

**Verification:**

```powershell
pytest tests/test_version_metadata.py -q
pytest tests/ -q
python -m build
python -m twine check dist/*
```

Inspect wheel `METADATA` for `Name`, `Version`, `Summary`, `Requires-Dist`, project URLs, and
license. Install the wheel and compare:

```python
from importlib.metadata import version
import trendfollowing

assert trendfollowing.__version__ == version("trendfollowing")
```

**Out of scope:** GitHub settings, documentation expansion, custom domain, API changes, release,
or scientific-title/status changes.

## U3a — Build the documentation foundation

**Execution status (2026-08-16): PASS.** See `agents/U3A_IMPLEMENTATION_REPORT.md`.

**Deliverable:** a minimal Sphinx/MyST site and deployment workflow, without the U4 content wave.

Proposed canonical root:

```text
https://artursepp.github.io/TrendFollowingSystems/
```

Foundation:

- `docs/conf.py` and a small MyST index;
- a `docs` optional dependency group, never a runtime dependency;
- warning-as-error HTML and link-check commands;
- server-rendered navigation to quickstart, workflows, API, paper/replication, changelog, source,
  issues, citation, PyPI, and `qis`;
- canonical URL configuration;
- GitHub Pages build/deploy workflow;
- no committed `_build/` output;
- sitemap support only after checking the host's deployed behavior. If GitHub Pages provides no
  usable sitemap for the uploaded Sphinx artifact, add the smallest maintained docs-only
  solution and verify the resulting XML.

Do not copy the long README wholesale. The landing page identifies the package, names the three
priority tasks, and routes the reader.

**Acceptance:** local HTML builds warning-free; all navigation is available without JavaScript;
generated pages contain canonical HTTPS URLs; source, issue, package-index, paper, and changelog
links are visible.

**Verification:**

```powershell
python -m pip install -e ".[docs]"
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
```

Inspect the generated landing HTML before requesting Gate A.

**Out of scope:** task-page prose, comparison content, Search Console actions, custom domain, and
release.

## Maintainer Gate A — External identity, hosting, and indexing

**Execution status (2026-08-16): PASS.** See `agents/DISCOVERABILITY_AUDIT.md`.

These actions require repository and Search Console authority:

1. Enable GitHub Pages for the approved workflow/environment.
2. Set GitHub About to the canonical sentence.
3. Set GitHub Website to the canonical docs root; retain paper and PyPI links in README/docs.
4. After deployment, update `[project.urls].Documentation` in the next release candidate.
5. Verify the active Search Console property for the canonical docs root using a persistent
   public method appropriate for GitHub Pages.
6. Submit or confirm the canonical sitemap.
7. Inspect the landing page, quickstart, API, and paper/replication page.
8. Record a redacted summary in `agents/DISCOVERABILITY_AUDIT.md`; do not store private exports
   or credentials.

**Gate evidence:** property type, verification date, Pages deployment URL/commit, sitemap status,
and priority-page status. Fresh-property processing delay is recorded as normal latency.

## U3b — Audit deployed technical discoverability

**Execution status (2026-08-16): PASS.** The deployed checker validates five public HTML pages,
seven sitemap URLs, the robots policy, and seven required outbound routes. See
`agents/DISCOVERABILITY_AUDIT.md`.

**Deliverable:** update `agents/DISCOVERABILITY_AUDIT.md`; remediate only observed defects.

Check deployed pages, not only local HTML:

- root, quickstart, API, paper/replication, robots, and sitemap HTTP results;
- redirects, accidental `noindex`/`nosnippet`, robots exclusion, and canonical tags;
- one canonical HTTPS URL per important page;
- server-rendered title, description, primary content, and navigation;
- internal reachability of every public task page;
- links from docs to PyPI, source, issues, changelog, citation, paper, and `qis`;
- links from PyPI and GitHub back to the docs root after release/deployment;
- no competing `latest`, `stable`, branch, or README URL presented as canonical.

Use scripted checks with bounded retries after host deployment. Do not add `llms.txt`, AI crawler
files, doorway pages, or speculative schema.

**Acceptance:** priority pages are reachable, indexable, canonical, internally linked, and
represented in a valid sitemap.

**Verification:**

```powershell
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
python tools/check_deployed_docs.py --root https://artursepp.github.io/TrendFollowingSystems/
```

Create `tools/check_deployed_docs.py` only if no existing repository/portfolio tool owns these
checks. The script must validate HTTP, canonical, robots, and sitemap state without adding a
runtime dependency.

**Out of scope:** content expansion, paid SEO tools, custom-domain migration, and search-rank
claims.

## U6 — Create one root source of truth for first success

**Execution status (2026-08-16): PASS.** The root quickstart, mechanical docs inclusion,
headless example matrix, and clean-wheel execution passed. See
`agents/U6_IMPLEMENTATION_REPORT.md`.

**Deliverable:** `examples/quickstart.py` at repository root plus docs inclusion/drift checks.

The script:

1. imports the released public API;
2. computes a small closed-form AR(1) and ARFIMA result without network or data;
3. prints the installed version and compact deterministic evidence;
4. states the annualisation/process/span conventions in adjacent prose or comments;
5. points to the first parameters to change;
6. finishes in less than one minute on a normal laptop;
7. writes no files and opens no GUI.

The docs quickstart mechanically includes the root script (for example with MyST/Sphinx literal
include) or verifies its code block against it. The README links to the authoritative script and
may show only a deliberately short tested excerpt.

Keep the existing root examples:

- `examples/analytic_sharpe_vs_span.py`
- `examples/backtest_european_system.py`
- `examples/predict_sharpe_from_acf.py`

Make their environment, runtime, data use, output path, and expected result explicit. Run plotting
examples with a non-interactive backend in CI and a temporary working directory so figures are not
committed. Empirical examples must pass the M2 installed-data contract.

Add structural checks:

- `examples/` exists at repository root;
- `examples/quickstart.py` is present;
- no `src/trendfollowing/examples/` exists;
- docs reference the root example instead of maintaining a second copy.

Failure-first evidence:

- run the current README quickstart as one script and record its undefined `daily_returns`
  failure;
- add the root example smoke test, temporarily alter the expected deterministic output, observe
  failure, then restore.

**Acceptance:** a new user can `pip install trendfollowing` and run the root quickstart against
the built wheel from outside the checkout; documentation and source cannot silently drift.

**Verification:**

```powershell
python examples/quickstart.py
pytest tests/test_examples.py -q
```

In a clean wheel environment:

```powershell
python -m pip install dist/trendfollowing-*.whl
python C:/path/to/checkout/examples/quickstart.py
```

Also execute all claimed root examples with `MPLBACKEND=Agg` and a temporary current directory.
Record runtime and compact output; compare analytical and realized claims through the independent
tests already in the repository.

**Out of scope:** notebook dependencies, generated figures in version control, live market data,
broker integration, and duplicating examples inside the package.

## U4 — Publish task-oriented documentation

**Deliverable:** three focused waves. Keep each implementation reviewable and do not combine more
than roughly five content/config files without a new execution proposal.

### U4a — Closed-form analytics and span selection

Create a page covering:

- white noise, AR(1), ARFIMA, and empirical ACF inputs;
- expected return, Sharpe, turnover, and skewness outputs;
- `long_span`, `short_span`, `af`, `sr_underlying`, drift, and cost units;
- the arithmetic simple-excess-return Sharpe convention;
- exact versus leading-order results;
- a runnable root example and expected interpretation;
- failure modes and non-goals.

### U4b — Predict Sharpe from autocorrelation and drift

Create a page covering:

- point-in-time versus in-sample descriptive use;
- volatility normalization and lag construction;
- sample ACF/drift inputs and output interpretation;
- why the published comparison is a replication result, not a promise of future performance;
- the authoritative `examples/predict_sharpe_from_acf.py`;
- data coverage, missing observations, and estimation risk.

### U4c — Compare and backtest the three systems

Create a page covering:

- European continuous EWMA weights, American crossover/ATR stops, and TSMOM signs;
- inputs, outputs, units, costs, volatility targeting, warmup, and no-look-ahead timing;
- packaged universe scope and `TF_RESOURCE_PATH`;
- use of `qis` for backtesting/reporting;
- the authoritative empirical root example and verification catalog;
- paper reproduction versus reusable package workflow.

Cross-cutting pages may cover:

- data and reproducibility;
- conventions and annualisation;
- paper exhibit map and citation;
- public API/reference.

Every symbol must exist in the built public artifact. Link to lower-level `qis` documentation for
delegated behavior rather than copying it.

**Acceptance:** each priority task has one focused entry page; examples execute in the claimed
environment; units and conventions are explicit; numerical claims are checked independently.

**Verification:**

```powershell
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
pytest tests/test_examples.py -q
pytest tests/ -q
```

Run any public-name coverage check added for docs and manually audit symbols against installed
`trendfollowing`, not `dir()` accidents from checkout imports.

**Out of scope:** new algorithms, new backtests, duplicated `qis` documentation, changed paper
values, or generated marketing figures.

## U5 — Publish a neutral comparison and choice guide

**Deliverable:** one dated page comparing workflows, not declaring a universal winner.

Candidate genuine alternatives:

- `pysystemtrade` for a broader systematic-futures research/production stack;
- `vectorbt` for vectorized parameter exploration and general backtesting;
- `backtrader` or `backtesting.py` for general event/rule-driven strategy backtesting.

Confirm current stable versions and active official sources at execution time. The final set should
contain two to four alternatives and at least one use case favoring each.

Capability dimensions:

- closed-form trend-following moments;
- supported process models and analytical span/cost study;
- European/American/TSMOM reference implementations;
- bundled or user-supplied futures data;
- Monte Carlo/scientific replication;
- general strategy engine scope;
- execution/broker integration;
- intended research versus production audience;
- license and extension implications.

Required sections:

- overlap and different design goals;
- capability matrix;
- workflow-based decision guide;
- where `trendfollowing` is specialized;
- where broader engines are a better fit;
- methodology, date, versions, citations, and limitations.

**Acceptance:** every nontrivial competitor claim resolves to official documentation,
repositories, releases, or papers; unknowns are marked; popularity does not determine the
technical recommendation.

**Verification:**

```powershell
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
```

Perform a manual primary-source and license audit.

**Out of scope:** favorable benchmark construction, installing alternatives, or expanding this
package into a general execution engine.

## Maintainer Gate B — Decide on a hosted notebook

**Default recommendation:** defer U7 through the first 90-day cycle.

The root script and static docs should establish first success with less maintenance and without a
second execution surface. Reconsider only if U9 shows qualified users reach the quickstart but fail
to install/run locally, or if paper readers demonstrably need a hosted analytical trial.

Approval criteria:

- the released wheel installs within a normal Colab session;
- runtime and data size are suitable;
- the notebook imports the root quickstart mechanically;
- no Jupyter dependency enters the core package;
- a maintainer accepts the recurring clean-runtime verification cost.

Record `SKIPPED` when deferred; scheduling a later review is not a completed U7.

## U7 — Optional thin hosted notebook

**Deliverable, only after Gate B approval:** one output-free notebook linking to and mechanically
checking the root `examples/quickstart.py`.

The notebook installs the released package, prints the installed version, runs the same
deterministic analytical workflow, links to versioned docs and the paper, and embeds no large
outputs or unpublished checkout.

**Acceptance:** clean Colab `Run all` passes and a drift check runs cross-platform.

**Verification:** JSON parse, drift test, root script execution, and one maintainer-confirmed clean
hosted run.

**Out of scope:** notebook gallery, Binder, copied source, or Jupyter runtime dependencies.

## U8 — Release, deploy, and align trust surfaces

**Deliverable:** an explicitly approved release because layout, wheel contents, metadata, README,
and runtime version behavior must reach PyPI. A 1.1.0 release is a reasonable non-breaking
candidate, but the maintainer chooses the version.

Before release:

1. confirm `pyproject.toml`, `CITATION.cff`, README software BibTeX, runtime
   `__version__`, changelog, tag, and docs version agree;
2. run full tests and the two independent numerical verification jobs;
3. build wheel/sdist from a clean checkout;
4. inspect artifact contents, hashes, metadata, license, and data size;
5. install each artifact in a clean environment outside the checkout;
6. run root quickstart and empirical loader;
7. build docs warning-free and verify they describe the candidate version;
8. obtain explicit PyPI/GitHub Release approval.

Repository commands:

```powershell
pytest tests/ -q
ruff check src/trendfollowing/ tests/ examples/
python -m papers.tf_systems.replication.verify_arfima_variance_scale
python -m papers.tf_systems.replication.ewma_variance_check
sphinx-build -W --keep-going -b html docs docs/_build/html
sphinx-build -W --keep-going -b linkcheck docs docs/_build/linkcheck
python -m build
python -m twine check dist/*
```

After release:

- verify PyPI renders the new README and project links;
- verify tag, GitHub Release, PyPI version, citation, and docs agree;
- install from PyPI, not local `dist/`, and rerun quickstart and `load_data()`;
- verify GitHub Pages deployed the intended commit;
- repeat U3b deployed HTTP/canonical/robots/sitemap checks;
- record commit, tag, artifact URLs/hashes/sizes, docs deployment, and results.

**Acceptance:** all public surfaces expose the intended release and identity, installed artifacts
meet both first-success and empirical contracts, and numerical evidence is unchanged.

**Out of scope:** bundling unrelated scientific, API, or strategy changes into the adoption
release.

## U9 — Measure at approximately 30, 60, and 90 days

**Deliverable:** update `agents/DISCOVERABILITY_90_DAY_REPORT.md` at each checkpoint.

Start D0 on the date U8's release and deployed-doc checks pass. Do not use roadmap creation as D0.
If U8 passed on 2026-08-16, illustrative Europe/Zurich dates would be 2026-09-15,
2026-10-15, and 2026-11-14; replace them with actual release-relative dates.

Fixed definitions:

- Search Console window: latest 28 complete days ending at least two days before observation;
- branded: query contains `trendfollowing` or `TrendFollowingSystems`, case-insensitive;
- non-branded: the three U1 queries, unchanged;
- priority pages: landing, quickstart, closed-form/span page, ACF prediction page, and systems
  comparison/backtest page;
- downloads: same trailing-period source at every checkpoint, never unique users;
- GitHub stars, forks, watchers, dependents, issues, and external citations: secondary proxies;
- exact-name treatment: dated text observation in the maintainer's normal search context;
- missing, delayed, and privacy-suppressed values remain missing.

Compare:

- indexed/canonical priority pages and sitemap state;
- branded/non-branded impressions, clicks, CTR, and landing pages;
- documentation entry paths and quickstart referrals when analytics exist;
- package downloads and GitHub signals;
- issues, discussions, citations, or external references attributable to the new material;
- installation, data, or example failure reports;
- exact package-name treatment.

At 90 days recommend exactly one primary action:

1. deepen a performing topic;
2. repair a demonstrated conversion failure;
3. improve external distribution; or
4. stop investing in a channel without qualified use.

Use multiple observations and state attribution limits. Do not infer causality from one metric.

**Acceptance:** every checkpoint uses the fixed definitions, missing data is explicit, and the
recommendation follows from evidence.

**Scheduling:** schedule task-attached checkpoints only after U8 establishes D0 and only with
maintainer approval. Scheduling completes setup, not U9.

## Stage dependencies and stop conditions

```text
U0 -> U1 -> M1 -> M2 -> U2 -> U3a -> Gate A -> U3b
                                             |
                                             v
                         U6 -> U4 -> U5 -> Gate B -> U7 (optional)
                                             |
                                             v
                                            U8 -> U9
```

Stop and propose before continuing when:

- a stage exceeds the stated package/data/docs boundary;
- more than roughly five non-mechanical files must change in one review unit;
- any public signature or numerical result changes;
- data hashes differ;
- the wheel cannot meet the recommended empirical contract within release constraints;
- a required external property or release credential is unavailable;
- competitor/source claims cannot be supported by primary sources;
- docs deployment creates conflicting canonical URLs.

## Pull-request slicing

Recommended review units:

1. `chore: migrate trendfollowing package to src layout` — M1 only;
2. `fix: package immutable futures data for installed use` — M2 only;
3. `docs: align trendfollowing identity and runtime metadata` — U2;
4. `docs: add Sphinx foundation and Pages workflow` — U3a;
5. `docs: add wheel-tested root quickstart` — U6;
6. `docs: add closed-form and span-selection guide` — U4a;
7. `docs: add ACF prediction workflow` — U4b;
8. `docs: add system comparison and backtest workflow` — U4c;
9. `docs: add neutral package choice guide` — U5;
10. `release: publish approved adoption release` — U8.

M1's `git mv` naturally touches many paths; keep it mechanical so review is still tractable.

## Status log

Append one line for every completed, skipped, or blocked stage:

```text
YYYY-MM-DD · stage · branch/commit · PASS|SKIPPED|BLOCKED · concise verification result
```

Use `PASS-LOCAL` only temporarily before required deployed checks, then replace it with `PASS`.

```text
2026-08-16 · U0 · main@ffdecbbe · PASS · package adaptation profile completed; proceed decision recorded
2026-08-16 · U1 · main@ffdecbbe · PASS · public/local baseline recorded; credentialed analytics explicitly unknown
2026-08-16 · M1 · main@working-tree · PASS · src migration, 32 public tests, numerical gates, and built-wheel checks passed
2026-08-16 · M2 · main@working-tree · PASS · bundled futures resources, override contract, and artifact checks passed
2026-08-16 · U2 · main@working-tree · PASS · canonical identity, runtime metadata, and built-artifact checks passed
2026-08-16 · U3a · main@working-tree · PASS · warning-free HTML/linkcheck, static navigation, and Pages workflow passed
2026-08-16 · Gate A · main@2e30bb5 · PASS · Pages, canonical GitHub identity, Search Console ownership, and sitemap submission completed
2026-08-16 · U3b · main@working-tree · PASS · deployed HTTP, canonical, robots, sitemap, navigation, and outbound-route audit passed
2026-08-16 · U6 · main@working-tree · PASS · root quickstart, docs drift guard, headless examples, and clean-wheel execution passed
2026-08-17 · U4a · main@working-tree · PASS · focused guide, public-symbol audit, root example, numerical cross-checks, and docs build passed
```

## Definition of complete

Implementation is complete when M1 and M2 pass; selected U0-U8 stages pass; root examples remain
the single source of runnable first-success code; public deployments and credentialed gates are
recorded; and U9 checkpoints are scheduled from the actual U8 date.

The roadmap is complete only after the 90-day observation and recommendation. Scientific
submission, acceptance, DOI changes, and paper-result changes remain separate maintainer-approved
work.
