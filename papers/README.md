# Research paper workspaces

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Project: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](../CITATION.cff).

| Workspace | Repository availability |
|---|---|
| [tf_systems](tf_systems/README.md) | Existing approved LaTeX source, SIAM class, twelve figures, replication code and nine frozen caches; no tracked PDF |
| `smart_diversification`, `smart_diversification_slides` | Local and ignored |
| `layer_attribution_2026`, `tf_diversification_long_run_2026` | Local and ignored |
| Other or future workspaces | Local until explicitly approved |

The [paper contract](AGENTS.md) defines `paper/`, `drafts/`, `presentations/`,
`private/`, `replication/` and `agents/`. Local directories need no tracked
placeholders. Drafts, private records and agent notes are always ignored.
Static inputs and approved manuscript assets use exact per-file exceptions.

Frozen paper caches belong in `replication/data/reference/`. The common futures
dataset stays in the installed package; new research output stays outside the
checkout. Paper workspaces are excluded from both Python distributions.
