# NVCC Option Metadata

This directory contains generated NVIDIA CUDA compiler driver option metadata.

- `manifest.toml` pins versioned CUDA documentation pages from NVIDIA's archive.
- `<major>/<version>.toml` contains the option metadata generated for one CUDA
  Toolkit documentation release, for example `option/nvcc/12/12.5.0.toml`.

## Source Data

NVIDIA publishes versioned `nvcc` option reference pages under the CUDA
documentation archive. The generator fetches each pinned
`cuda-compiler-driver-nvcc/index.html` page, supports both the older table
layout and the newer section/table-of-contents layout, and extracts option
spellings, aliases, argument text, section anchors, help text, source URL, and
source SHA-256.

## Regeneration

```sh
pixi run refresh-nvcc-options
pixi run generate-nvcc-options
pixi run verify-nvcc-options
```

To regenerate or verify a subset while developing:

```sh
python3 scripts/update_nvcc_options.py --generate --versions 8.0.0 11.8.0 12.5.0
python3 scripts/update_nvcc_options.py --verify --versions 8.0.0 11.8.0 12.5.0
```

## Reproducibility

Generation is expected to be reproducible from:

- this repository revision
- `option/nvcc/manifest.toml`
- the pinned CUDA documentation URLs and source SHA-256 values recorded in the
  generated files
- the `pixi.lock` environment

Fetched documentation pages are cached under `.cache/nvcc-options`, which is
not committed. `--verify` regenerates the selected versions into a temporary
directory and byte-compares them with the committed TOML files.
