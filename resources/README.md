# Repository resources

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Project: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

This directory retains ignored legacy local research caches. New paper runs
must use the configured external runtime rather than write into this checkout.
The nine tracked tf_systems reference caches now live in
`papers/tf_systems/replication/data/reference/`. Both paper workspaces and this
root resources directory are excluded from Python distributions.

The immutable public futures dataset remains in
`src/trendfollowing/resources/futures/` and is installed with `trendfollowing`.
Use `trendfollowing.universe.load_data()` or the explicit `TF_RESOURCE_PATH`
override. The package's existing external-path API is unchanged for other users.
