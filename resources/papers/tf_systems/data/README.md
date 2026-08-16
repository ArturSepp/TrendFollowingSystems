# Data

This paper runs entirely from the common futures dataset packaged under
`src/trendfollowing/resources/futures/` (84 contracts, daily log returns,
seven asset classes, volume-based costs), loaded through
`trendfollowing.universe.load_data()`. Set `TF_RESOURCE_PATH` to override with
a local folder. No paper-specific data files are required, so this folder is
intentionally empty.
