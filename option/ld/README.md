# GNU ld Option Metadata

This directory contains generated GNU ld option metadata from binutils releases.

- `manifest.toml` pins binutils release tags to immutable commit SHAs.
- `<major>/<version>.toml` contains the option metadata generated for one GNU ld
  release, for example `option/ld/2/2.46.0.toml`.

## Source Data

GNU ld defines its command-line option table in `ld/lexsup.c`. The generator
fetches that file from each pinned binutils release commit and extracts long
spellings, short spellings, argument kind, option code, help text, metavar, and
source location where recoverable from the table.

## Regeneration

```sh
pixi run refresh-ld-options
pixi run generate-ld-options
pixi run verify-ld-options
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_ld_options.py --generate --versions 2.10.0 2.40.0 2.46.0
python3 scripts/update_ld_options.py --verify --versions 2.10.0 2.40.0 2.46.0
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/ld/manifest.toml`
- the pinned upstream binutils commits
- the `pixi.lock` environment

Fetched sources are cached under `.cache/ld-options`, which is not committed.
`--verify` regenerates the selected versions into a temporary directory and
byte-compares them with the committed TOML files.
