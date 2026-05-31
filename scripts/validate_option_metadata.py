#!/usr/bin/env python3
"""Validate generated option metadata layout and TOML invariants."""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OPTION_DIR = ROOT / "option"


def load_toml(path: Path) -> dict[str, object]:
    with path.open("rb") as file:
        return tomllib.load(file)


def major_version(version: str) -> str:
    return version.split(".", 1)[0]


def validate_generated_file(path: Path, tool: str, version: str) -> list[str]:
    errors: list[str] = []
    try:
        data = load_toml(path)
    except Exception as error:
        return [f"{path}: failed to parse TOML: {error}"]

    metadata = data.get("metadata")
    options = data.get("options", [])
    source_files = data.get("source_files", [])
    if not isinstance(metadata, dict):
        errors.append(f"{path}: missing [metadata]")
        return errors
    if metadata.get("tool") != tool:
        errors.append(f"{path}: metadata.tool is {metadata.get('tool')!r}, expected {tool!r}")
    if metadata.get("version") != version:
        errors.append(f"{path}: metadata.version is {metadata.get('version')!r}, expected {version!r}")
    if not isinstance(options, list):
        errors.append(f"{path}: options must be a list")
        return errors
    if metadata.get("option_count") != len(options):
        errors.append(
            f"{path}: metadata.option_count is {metadata.get('option_count')!r}, "
            f"expected {len(options)}"
        )
    if not isinstance(source_files, list) or not source_files:
        errors.append(f"{path}: source_files must be a non-empty list")

    for index, option in enumerate(options, start=1):
        if not isinstance(option, dict):
            errors.append(f"{path}: options[{index}] must be a table")
            continue
        option_id = option.get("id")
        if option_id is not None and (not isinstance(option_id, int) or option_id <= 0):
            errors.append(f"{path}: options[{index}].id must be a positive integer")
        spellings = option.get("spellings")
        if spellings is not None:
            if not isinstance(spellings, list) or not spellings:
                errors.append(f"{path}: options[{index}].spellings must be a non-empty list")
            elif not all(isinstance(spelling, str) and spelling for spelling in spellings):
                errors.append(f"{path}: options[{index}].spellings contains a non-string value")
    return errors


def validate_tool(tool_dir: Path) -> tuple[int, list[str]]:
    errors: list[str] = []
    manifest_path = tool_dir / "manifest.toml"
    try:
        manifest = load_toml(manifest_path)
    except Exception as error:
        return 0, [f"{manifest_path}: failed to parse TOML: {error}"]

    metadata = manifest.get("metadata")
    releases = manifest.get("releases")
    tool = tool_dir.name
    if not isinstance(metadata, dict):
        errors.append(f"{manifest_path}: missing [metadata]")
    elif metadata.get("tool") != tool:
        errors.append(f"{manifest_path}: metadata.tool is {metadata.get('tool')!r}, expected {tool!r}")
    if not isinstance(releases, list):
        return 0, errors + [f"{manifest_path}: releases must be a list"]

    expected_paths: set[Path] = set()
    for index, release in enumerate(releases, start=1):
        if not isinstance(release, dict):
            errors.append(f"{manifest_path}: releases[{index}] must be a table")
            continue
        version = release.get("version")
        if not isinstance(version, str) or not version:
            errors.append(f"{manifest_path}: releases[{index}].version must be a non-empty string")
            continue
        expected = tool_dir / major_version(version) / f"{version}.toml"
        expected_paths.add(expected)
        if not expected.exists():
            errors.append(f"{expected}: missing generated file")
            continue
        errors.extend(validate_generated_file(expected, tool, version))

    actual_paths = {
        path
        for path in tool_dir.rglob("*.toml")
        if path.name != "manifest.toml"
    }
    for extra in sorted(actual_paths - expected_paths):
        errors.append(f"{extra}: generated file is not listed in manifest")
    return len(releases), errors


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--option-dir", type=Path, default=DEFAULT_OPTION_DIR)
    parser.add_argument("--tools", nargs="*", help="tool directories to validate")
    args = parser.parse_args(argv)

    option_dir = args.option_dir
    if args.tools:
        tool_dirs = [option_dir / tool for tool in args.tools]
    else:
        tool_dirs = sorted(path for path in option_dir.iterdir() if (path / "manifest.toml").exists())

    errors: list[str] = []
    total_releases = 0
    for tool_dir in tool_dirs:
        if not tool_dir.exists():
            errors.append(f"{tool_dir}: missing tool directory")
            continue
        release_count, tool_errors = validate_tool(tool_dir)
        total_releases += release_count
        errors.extend(tool_errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"validated option metadata for {len(tool_dirs)} tools and {total_releases} releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
