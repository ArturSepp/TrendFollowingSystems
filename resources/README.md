# Repository resources

This root folder holds writable paper-replication caches only. They are not
included in the wheel.

The immutable public futures dataset is package data under
`src/trendfollowing/resources/futures/` and is installed with `trendfollowing`.
Use `trendfollowing.universe.load_data()` to read it or set `TF_RESOURCE_PATH`
to an external replacement dataset.
