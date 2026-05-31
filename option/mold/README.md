# mold Option Metadata

This directory contains generated mold linker option metadata.

- `manifest.toml` pins mold release tags to immutable commit SHAs.
- `<major>/<version>.toml` contains the option metadata generated for one mold
  release, for example `option/mold/2/2.41.0.toml`.

## Source Data

mold publishes versioned manpage sources in its repository. Newer releases use
`docs/mold.md`; older releases use `docs/mold.1`. The generator fetches the
pinned source file for each release and extracts option groups, spellings,
syntax forms, argument shape, descriptions, source locations, and source
SHA-256.

## Regeneration

```sh
pixi run refresh-mold-options
pixi run generate-mold-options
pixi run verify-mold-options
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_mold_options.py --generate --versions 0.9.6 1.11.0 2.41.0
python3 scripts/update_mold_options.py --verify --versions 0.9.6 1.11.0 2.41.0
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/mold/manifest.toml`
- the pinned upstream mold commits
- the `pixi.lock` environment

Fetched documentation sources are cached under `.cache/mold-options`, which is
not committed. `--verify` regenerates the selected versions into a temporary
directory and byte-compares them with the committed TOML files.
