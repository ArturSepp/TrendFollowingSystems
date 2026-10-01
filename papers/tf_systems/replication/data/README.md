# Paper inputs

*Author: [Artur Sepp](https://github.com/ArturSepp)*

Project: [TrendFollowingSystems](https://github.com/ArturSepp/TrendFollowingSystems).
Software citation: [CITATION.cff](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The common futures dataset stays in `src/trendfollowing/resources/futures/`
and is loaded with `trendfollowing.universe.load_data()`. `TF_RESOURCE_PATH`
can select an explicit replacement. Do not duplicate the packaged dataset here.

[reference/](reference/README.md) contains the nine preserved Monte Carlo/grid
caches needed for available cached exhibits, with a SHA-256 inventory. New run
results belong in the external runtime. Restricted inputs, if needed, go into
ignored `local/` and must not be substituted silently for frozen inputs.
