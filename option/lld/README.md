# LLD Option Metadata

This directory contains generated LLD option metadata.

- `manifest.toml` pins LLVM release tags to immutable commit SHAs.
- `<major>/<version>.toml` contains the option metadata generated for one LLD
  release, for example `option/lld/22/22.1.6.toml`.
- Each version file merges the available LLD drivers: ELF, COFF, Mach-O,
  MinGW, and WebAssembly.

## Source Data

LLD stores option definitions in TableGen files such as
`lld/ELF/Options.td`, `lld/COFF/Options.td`, and `lld/wasm/Options.td`.
The generator fetches the pinned upstream source files, resolves TableGen
includes, runs `llvm-tblgen`, and records source SHA-256 hashes.

## Regeneration

```sh
pixi run refresh-lld-options
pixi run generate-lld-options
pixi run verify-lld-options
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/lld/manifest.toml`
- the pinned upstream LLVM commits
- the `pixi.lock` environment, including `llvm-tblgen`

`--verify` regenerates the selected versions into a temporary directory and
byte-compares them with the committed TOML files.
