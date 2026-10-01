# Paper and replication

The package accompanies Artur Sepp and Vladimir Lucic's *The Science and Practice of
Trend-Following Systems*.

- [Read the paper on SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3167787).
- [Open the replication guide](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/papers/tf_systems/README.md).
- [Browse the replication modules](https://github.com/ArturSepp/TrendFollowingSystems/tree/main/papers/tf_systems/replication).
- [Cite the software and paper](https://github.com/ArturSepp/TrendFollowingSystems/blob/main/CITATION.cff).

The wheel contains the immutable futures inputs used by the public examples. Frozen paper caches remain in the source checkout under
`papers/tf_systems/replication/data/reference/`; new caches and generated outputs
go to the external runtime. Neither is installed as package resources. See the replication guide before regenerating exhibits.

For a shorter route into the implementation, begin with the maintained
{doc}`example workflows <workflows>`.
