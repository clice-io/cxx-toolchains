# MSVC Option Metadata

This directory contains generated Microsoft C/C++ compiler and linker option
metadata.

- `manifest.toml` pins the public `MicrosoftDocs/cpp-docs` source commit and
  the Microsoft Learn monikers used as Visual Studio major-version buckets.
- `<major>/<version>.toml` contains option metadata for one Visual Studio major
  moniker, for example `option/msvc/17/17.0.0.toml`.
- Each version file includes both `cl` and `link` rows, distinguished by the
  `driver` field.

## Source Data

MSVC does not publish option table source in the same form as LLVM, GCC, or
binutils. This generator therefore uses the public Microsoft C++ documentation
repository as a reproducible source and records the Learn moniker that the docs
declare, such as `msvc-170`.

The current source covers Visual Studio major monikers, not individual MSVC
toolset minor builds. Future installed-toolchain probes can add finer-grained
`cl /?` and `link /?` evidence on top of this docs-backed baseline.

## Regeneration

```sh
pixi run refresh-msvc-options
pixi run generate-msvc-options
pixi run verify-msvc-options
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_msvc_options.py --generate --versions 14.0.0 17.0.0 18.0.0
python3 scripts/update_msvc_options.py --verify --versions 14.0.0 17.0.0 18.0.0
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/msvc/manifest.toml`
- the pinned upstream `MicrosoftDocs/cpp-docs` commit
- the `pixi.lock` environment

Fetched markdown sources are cached under `.cache/msvc-options`, which is not
committed. `--verify` regenerates the selected versions into a temporary
directory and byte-compares them with the committed TOML files.
