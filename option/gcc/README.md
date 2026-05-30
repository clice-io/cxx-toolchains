# GCC Option Metadata

This directory contains generated GCC option metadata.

- `manifest.toml` pins GCC release tags to immutable commit SHAs from
  `gcc-mirror/gcc`.
- `<major>/<version>.toml` contains the option metadata generated for one GCC
  release, for example `option/gcc/14/14.3.0.toml`.

## Source Data

GCC stores option definitions in `.opt` files under `gcc/`. The generator uses
Git to list the exact `gcc/**/*.opt` file set for each pinned release commit,
fetches those files by commit, and parses option records, enum records, raw
properties, help text, source locations, and source file SHA-256 hashes.

## Regeneration

```sh
pixi run refresh-gcc-options
pixi run generate-gcc-options
pixi run verify-gcc-options
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_gcc_options.py --generate --versions 3.4.0 10.5.0 16.1.0
python3 scripts/update_gcc_options.py --verify --versions 3.4.0 10.5.0 16.1.0
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/gcc/manifest.toml`
- the pinned upstream GCC commits
- the `pixi.lock` environment

Fetched source files and the local GCC git object cache are stored under
`.cache/gcc-options`, which is not committed. `--verify` regenerates the
selected versions into a temporary directory and byte-compares them with the
committed TOML files.
