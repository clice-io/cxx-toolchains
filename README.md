# cxx-toolchains

A machine-readable reference for C and C++ toolchains.

`cxx-toolchains` collects structured metadata about compilers, linkers,
runtimes, target platforms, command-line options, ABI details, sysroots, and
symbols. The goal is to make toolchain knowledge reusable across language
servers, build systems, compilation database generators, cross-compilation
tools, static analyzers, package managers, and binary compatibility checkers.

## Motivation

C and C++ toolchain behavior is spread across compiler source trees, official
manuals, release artifacts, distribution patches, build-system probes, and
private detection code inside downstream tools.

A common example is system include and library detection. Compiler drivers have
their own logic, build systems often implement another version of it, and
language servers need yet another implementation to resolve code correctly. The
same pattern repeats across option parsing, target triples, runtime discovery,
linker behavior, sysroot layout, and ABI compatibility.

This repository aims to provide a neutral shared data layer for those facts.

## Scope

The project is intended to cover:

- compiler and toolchain releases, including LLVM/Clang, GCC, MSVC, Intel,
  NVIDIA, Apple Clang, Zig, and related tools
- compiler and linker option metadata, including parsing grammar and semantic
  effects on inputs, outputs, phases, targets, sysroots, standard libraries, and
  linker forwarding
- implicit system include paths, library search paths, resource directories,
  built-in includes, built-in macros, and default flags
- target triples, architectures, operating systems, environments, ABIs, aliases,
  and compatibility relationships
- libc and C++ standard library metadata, including glibc, musl, newlib, UCRT,
  libstdc++, libc++, and MSVC STL
- sysroot layout, startup objects, dynamic loaders, and default runtime
  libraries
- symbol and ABI metadata, including symbol versions, minimum runtime
  requirements, compiler builtins, and library ownership
- platform and version quirks such as distribution patches, unusual search
  orders, known bugs, and compatibility traps

## Design Principles

- Data and code are separate. The repository should primarily contain schemas,
  source data, generated data, provenance, and validation cases.
- Facts and derivations are separate. Tools can generate their own profiles,
  parsers, detectors, or sysroot resolvers from the same underlying facts.
- Data should be verifiable. Prefer upstream source files, official
  documentation, release artifacts, and real tool probes over hand-written
  assumptions.
- Machine-readable data comes first. Human documentation should be generated
  from the same source of truth where possible.
- Coverage should be broad by default. Mainstream toolchains should work out of
  the box, with extension points for custom or proprietary toolchains.

## Status

The first metadata sets are Clang, GCC, and LLD options. See
[`option`](option) for generated TOML files, provenance, and reproducible
pixi-managed regeneration and verification commands. See
[`docs/option-sources.md`](docs/option-sources.md) for extraction strategies for
additional tools such as GNU ld, NVCC, and MSVC.
