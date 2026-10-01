# Paper workspaces

This contract applies to TFS papers. Root AGENTS.md controls the prescribed
external Python environment, numerical invariants and runtime configuration.

## Layout

Keep each workspace at `papers/<paper_id>/`, outside `src/trendfollowing/`.

| Section | Purpose | Git policy |
|---|---|---|
| `paper/` | One current manuscript, bibliography/class dependencies, reading PDF and `figures/` | Exact approved files only |
| `drafts/<version>/` | Previous drafts with their figures and dependencies | Always ignored |
| `presentations/<event>/` | Presentations and their figures | Ignored by default; exact approved exceptions |
| `private/` | Editor correspondence, referee reports, replies and permissions | Always ignored |
| `replication/` | Code, static `data/`, and automated `tests/` | Approved code and redistributable inputs tracked |
| `agents/` | Paper roadmaps, execution reports and working records | Always ignored |

Create local sections when needed; do not track empty placeholders. Per-paper
`agents/` explicitly overrides the generated shared core's root-only record
location. Repository-wide work stays in root `agents/`. `AGENTS.md` is a tracked
instruction file, not a working record.

## Publication and preservation

- The existing `tf_systems` source, SIAM class and twelve figures remain approved.
  The compiled PDF is not tracked; the SSRN manuscript source remains local.
  Preserve these exact permissions and all companion-workspace exclusions.
- Deny new paper workspaces by default. A new public workspace requires an
  explicit publication decision, index/checker update and root ignore exception.
  SSRN availability, journal submission or acceptance does not grant GitHub rights.
- Use exact per-file exceptions for manuscripts, slides and static data. Do not
  use wildcards to approve future versions or figures. Record public availability
  in the paper index/README; confidential permission records belong in `private/`.
- Frozen Monte Carlo inputs live in `replication/data/reference/`, with provenance
  and SHA-256 hashes. Keep new runs separate; do not overwrite reference values
  merely to agree with new dependencies or code. Missing run inputs must fail
  clearly rather than silently falling back to frozen values.
- The shared immutable futures dataset stays in `src/trendfollowing/resources/`.
  Do not copy it into each paper. Preserve the universe and input bytes.
- Keep restricted inputs in ignored `replication/data/local/`. Public examples,
  licensed-data requirements and exact archived reproduction are different claims.
- Preserve local material when untracking or moving files. Archive drafts with
  their own figures. Ignored material requires private backup outside Git;
  removing index entries does not erase existing Git history.
- Companion papers remain entirely local. Preserve their current historical
  structure until their contents and dependency paths have been reviewed.

## Replication and output

Use `python -m papers.tf_systems.replication.<module>` from the repository root
in the prescribed environment. Existing package tests remain in root `tests/`;
paper-specific tests belong in `replication/tests/test_*.py`. Keep standalone
analytical verification scripts and historical research modules at their current
entry points. Production package modules must never depend on `papers.*`.

Configure `Enter-AgentRepo.ps1` before Python/checks on this Windows host.
`TF_PAPER_OUTPUT_PATH` optionally selects an absolute external run directory;
otherwise paper output uses the configured C-local runtime. `TF_FIGURE_PATH`
can override the figure directory. Both must stay outside the checkout and
OneDrive. Historical manual scripts must also run with an external working
directory and the source root on `PYTHONPATH` if they use relative user inputs.
Do not change the package's external-resource API as incidental layout cleanup.

Render available frozen exhibits with `replication.cached_figures`. Regeneration
uses external `results/`, figures use external `figures/`, and manuscript builds
use external `latex-build/`. Promote reviewed assets explicitly. Do not infer
pixel equality or a successful full manuscript rebuild from a cache move.

## Checks

Run these from the repository root after runtime configuration:

```powershell
python .github/scripts/check_paper_policy.py --worktree
python .github/scripts/paper_policy_test.py
python -m pytest papers/tf_systems/replication/tests -q
```

Before committing, run `.github/scripts/check_paper_policy.py` without options
to check the actual staged index and indexed ignore rules. Never force-add
private material. CI repeats these checks. Verify wheels and source archives
with `--artifacts <directory>`: paper workspaces and root agent records must be
absent, while the deliberately installed futures dataset must remain included.
For moves, update consumers, docs and CI together and verify input hashes.
For numerical changes, preserve the root repository's analytical/Monte Carlo
verification requirements; this folder policy does not relax them.
