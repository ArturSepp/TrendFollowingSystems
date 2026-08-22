## What changed

Describe the problem and the smallest coherent change that solves it.

## Verification

List the exact commands run and their results. For numerical changes, name the independent
closed-form, Monte Carlo, or replication cross-check.

## Checklist

- [ ] Tests cover the changed behavior or defect.
- [ ] Look-ahead, return, annualisation, signal, and volatility-targeting conventions remain explicit.
- [ ] Published paper values, packaged futures resources, and `TF_RESOURCE_PATH` are unchanged.
- [ ] No analytics or reporting already provided by `qis` has been reimplemented.
- [ ] No private data, local paths, generated output, or development environments are included.
- [ ] `uv run --no-sync pytest` and the relevant lint/docs/wheel checks pass.
- [ ] User-visible changes are documented in `CHANGELOG.md` and relevant docs.
- [ ] New runtime dependencies or public-signature changes are called out explicitly.
