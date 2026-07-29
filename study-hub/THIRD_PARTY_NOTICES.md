# Third-Party Notices

## F2

- Package: `f2==0.0.1.7`
- License: Apache License 2.0
- Upstream copyright notice: Copyright (c) 2023 JohnserfSeed

F2 is downloaded as an external Python dependency and is not committed to this
repository. It is installed with `--no-deps` into the ignored local `.vendor/`
directory because its package metadata pins obsolete dependency versions and
includes development dependencies that must not alter Study Hub's runtime.

F2 supplies the non-official, user-triggered Douyin work-detail request used by
Study Hub's bounded preflight flow. Its software license does not grant access
to Douyin content and does not imply authorization, affiliation, or endorsement
by Douyin or ByteDance. Platform terms, content rights, Cookie validity, rate
limits, verification, and other access controls still apply.

The compatible runtime dependency set is pinned separately in
`requirements-f2-runtime.txt`. The declared licenses include MIT, Apache-2.0,
BSD-family, and LGPL-family licenses. These packages are installed into the same
ignored `.vendor/` directory and are not used to read browser Cookie databases.
