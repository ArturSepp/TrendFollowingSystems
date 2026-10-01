# Frozen reference caches

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Project: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

These nine files were moved byte-for-byte from
`resources/papers/tf_systems/results/`. `sha256.json` records their original
SHA-256 hashes. They are trusted repository inputs, not arbitrary downloaded
pickles; only load pickle files from a trusted source.

- Eight `expected_return_*_part_*.pkl` files hold frozen Monte Carlo aggregates
  for the three process figures. Their generator uses seed 8; this migration
  preserves the existing evidence rather than certifying a new simulation run.
- `grid_cache.pkl` holds the frozen cross-system attribution/grid results.

`replication.cached_figures` reads these inputs and writes external figure
candidates. New generation and legacy resumable scripts use external `results/`.
Table 6.1's `t6_part_*` caches are not included here; generating that table needs
its separate simulation stages. No fallback combines missing new-run inputs
with these references. Record source revision, input hashes, environment,
parameters and seeds before reviewing or replacing a frozen cache.
