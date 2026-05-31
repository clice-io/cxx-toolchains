#!/usr/bin/env python3
"""Fetch and generate mold option metadata from versioned documentation."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path
from urllib.parse import quote
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MANIFEST = ROOT / "option" / "mold" / "manifest.toml"
DEFAULT_OUTPUT_DIR = ROOT / "option" / "mold"
DEFAULT_CACHE_DIR = ROOT / ".cache" / "mold-options"

MOLD_REPO_URL = "https://github.com/rui314/mold"
MOLD_GIT_URL = "https://github.com/rui314/mold.git"
MOLD_RAW_URL = "https://raw.githubusercontent.com/rui314/mold"
SOURCE_PATHS = ["docs/mold.md", "docs/mold.1"]


def run(
    args: list[str],
    *,
    timeout: int = 300,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=True,
        text=True,
        timeout=timeout,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def normalize_version(tag_name: str) -> str | None:
    match = re.fullmatch(r"v(\d+)\.(\d+)(?:\.(\d+))?", tag_name)
    if match is None:
        return None
    return ".".join([match.group(1), match.group(2), match.group(3) or "0"])


def major_version(version: str) -> str:
    return version.split(".", 1)[0]


def version_output_path(output_dir: Path, version: str) -> Path:
    return output_dir / major_version(version) / f"{version}.toml"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, timeout: int = 120, attempts: int = 5) -> bytes:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = Request(url, headers={"User-Agent": "cxx-toolchains-option-generator"})
            with urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as error:
            last_error = error
            if isinstance(error, HTTPError) and error.code == 404:
                break
            if attempt + 1 == attempts:
                break
            time.sleep(0.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def source_url(ref: str, path: str) -> str:
    return f"{MOLD_RAW_URL}/{quote(ref)}/{quote(path)}"


def fetch_source(ref: str, path: str, cache_dir: Path) -> tuple[bytes, str]:
    cache_path = cache_dir / "sources" / ref / path
    if cache_path.exists():
        data = cache_path.read_bytes()
        return data, sha256_bytes(data)
    data = fetch_bytes(source_url(ref, path))
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(data)
    return data, sha256_bytes(data)


def fetch_first_source(ref: str, paths: list[str], cache_dir: Path) -> tuple[str, bytes, str]:
    last_error: Exception | None = None
    for path in paths:
        try:
            data, source_sha = fetch_source(ref, path, cache_dir)
            return path, data, source_sha
        except Exception as error:
            last_error = error
    assert last_error is not None
    raise last_error


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def toml_value(value: object) -> str:
    if value is None:
        raise ValueError("TOML does not support null values")
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return toml_string(value)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    raise TypeError(f"unsupported TOML value: {type(value)!r}")


def write_table(lines: list[str], table: dict[str, object]) -> None:
    for key, value in table.items():
        if value is None:
            continue
        if isinstance(value, list) and len(value) == 0:
            lines.append(f"{key} = []")
            continue
        lines.append(f"{key} = {toml_value(value)}")


def markdown_inline(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"=_{0,1}([A-Za-z0-9_.-]+)_", r"=<\1>", value)
    value = re.sub(r"=Ar\s+([A-Za-z0-9_.-]+)", r"=<\1>", value)
    value = re.sub(r"\s_([A-Za-z0-9_.-]+)_", r" <\1>", value)
    value = re.sub(r"_([A-Za-z0-9_.-]+)_", r"<\1>", value)
    value = value.replace("\\-", "-")
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def clean_description(value: str) -> str:
    value = re.sub(r"`([^`]*)`", r"\1", value)
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"_([A-Za-z0-9_.-]+)_", r"\1", value)
    value = value.replace("\\-", "-")
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return re.sub(r"\s+([.,;:])", r"\1", value)


def split_forms(syntax: str) -> list[str]:
    forms: list[str] = []
    start = 0
    square_depth = 0
    paren_depth = 0
    brace_depth = 0
    angle_depth = 0
    for index, char in enumerate(syntax):
        is_paren_option = char in "()" and index > 0 and syntax[index - 1] == "-"
        if char == "[":
            square_depth += 1
        elif char == "]":
            square_depth = max(square_depth - 1, 0)
        elif char == "(" and not is_paren_option:
            paren_depth += 1
        elif char == ")" and not is_paren_option:
            paren_depth = max(paren_depth - 1, 0)
        elif char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth = max(brace_depth - 1, 0)
        elif char == "<":
            angle_depth += 1
        elif char == ">":
            angle_depth = max(angle_depth - 1, 0)
        elif char == "," and not (square_depth or paren_depth or brace_depth or angle_depth):
            form = syntax[start:index].strip()
            if form:
                forms.append(form)
            start = index + 1
    form = syntax[start:].strip()
    if form:
        forms.append(form)
    return forms


def spelling_from_form(form: str) -> str | None:
    form = form.strip()
    if form.startswith("-z "):
        return "-z"
    if form.startswith("--"):
        match = re.match(r"(--[A-Za-z0-9][A-Za-z0-9_.+-]*)", form)
        return match.group(1) if match else None
    if form.startswith("-"):
        if form.startswith("-(") or form.startswith("-)"):
            return form[:2]
        match = re.match(r"(-[A-Za-z?][A-Za-z0-9_.+-]*)", form)
        if match is None:
            return None
        spelling = match.group(1)
        if len(spelling) > 2 and "<" in form and form.startswith(spelling):
            return spelling[:2]
        return spelling
    return None


def argument_kind(forms: list[str]) -> str:
    has_required = False
    forms_by_spelling: dict[str, set[str]] = {}
    for form in forms:
        if "[" in form:
            return "optional"
        spelling = spelling_from_form(form)
        if spelling is None:
            continue
        tail = form[len(spelling) :].strip()
        if tail:
            has_required = True
            forms_by_spelling.setdefault(spelling, set()).add("argument")
        else:
            forms_by_spelling.setdefault(spelling, set()).add("bare")
    if any(kinds == {"bare", "argument"} for kinds in forms_by_spelling.values()):
        return "optional"
    return "required" if has_required else "none"


def make_option(
    *,
    option_id: int,
    section: str,
    syntax: str,
    description: str,
    source_path: str,
    line_no: int,
) -> dict[str, object] | None:
    syntax = markdown_inline(syntax)
    forms = split_forms(syntax)
    spellings: list[str] = []
    for form in forms:
        spelling = spelling_from_form(form)
        if spelling is not None and spelling not in spellings:
            spellings.append(spelling)
    if not spellings:
        return None
    return {
        "id": option_id,
        "section": section,
        "spellings": spellings,
        "syntax": syntax,
        "forms": forms,
        "argument_kind": argument_kind(forms),
        "description": clean_description(description),
        "source_location": f"{source_path}:{line_no}",
    }


def markdown_sections(text: str) -> dict[str, list[tuple[int, str]]]:
    sections: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for line_no, line in enumerate(text.splitlines(), start=1):
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading is not None:
            current = heading.group(1)
            sections.setdefault(current, [])
            continue
        if current is not None:
            sections[current].append((line_no, line))
    return sections


def parse_markdown_options(text: str, source_path: str) -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    sections = markdown_sections(text)
    for section in ["MOLD-SPECIFIC OPTIONS", "GNU-COMPATIBLE OPTIONS"]:
        entries = sections.get(section, [])
        index = 0
        while index < len(entries):
            line_no, line = entries[index]
            match = re.match(r"^\*\s+(.+):\s*$", line)
            if match is None:
                index += 1
                continue
            syntax = match.group(1)
            desc_lines: list[str] = []
            index += 1
            while index < len(entries):
                _, desc_line = entries[index]
                if re.match(r"^\*\s+.+:\s*$", desc_line):
                    break
                if desc_line.strip():
                    desc_lines.append(desc_line.strip())
                index += 1
            option = make_option(
                option_id=len(options) + 1,
                section=section,
                syntax=syntax,
                description=" ".join(desc_lines),
                source_path=source_path,
                line_no=line_no,
            )
            if option is not None:
                options.append(option)
    return options


def clean_man(value: str) -> str:
    value = value.strip().strip('"')
    value = re.sub(r"\\fI([^\\]+?)\\fR", r"<\1>", value)
    value = re.sub(r"\\f[BRI]", "", value)
    value = value.replace("\\-", "-")
    value = value.replace("\\&", "")
    value = value.replace("\\ ", " ")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def extract_man_ip(line: str) -> str | None:
    match = re.match(r'^\.IP\s+"?(.+?)"?\s*$', line)
    if match is None:
        return None
    return clean_man(match.group(1))


def mdoc_form(line: str) -> str:
    body = line.removeprefix(".It").strip()
    forms: list[str] = []
    for segment in re.split(r"\s+,\s+", body):
        tokens = segment.split()
        pieces: list[str] = []
        concat_next = False
        index = 0
        while index < len(tokens):
            token = tokens[index]
            piece: str | None = None
            if token == "Fl" and index + 1 < len(tokens):
                value = tokens[index + 1]
                if value == "z" and index + 2 < len(tokens) and tokens[index + 2] not in {"Ns", "Ar"}:
                    piece = f"-z {tokens[index + 2]}"
                    index += 3
                elif value.startswith("-"):
                    piece = "-" + value
                    index += 2
                elif len(value) == 1 or value in {"(", ")", "EL"}:
                    piece = "-" + value
                    index += 2
                else:
                    piece = "--" + value
                    index += 2
            elif token == "Ar" and index + 1 < len(tokens):
                piece = f"<{tokens[index + 1].strip('.')}>"
                index += 2
            elif token == "Op":
                values = [item for item in tokens[index + 1 :] if item != "Sy"]
                piece = "[" + " ".join(values).strip() + "]"
                index = len(tokens)
            elif token == "Ns":
                concat_next = True
                index += 1
                continue
            elif token == "=":
                piece = "="
                index += 1
            else:
                index += 1
            if piece is None:
                continue
            if pieces and not concat_next and piece != "=":
                pieces.append(" ")
            pieces.append(piece)
            concat_next = False
        form = "".join(pieces).strip()
        if form:
            forms.append(form)
    return ", ".join(forms)


def clean_mdoc_description(lines: list[str]) -> str:
    kept = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped in {".", ".."} or stripped.startswith((".\\", ".ig")):
            continue
        kept.append(line)
    text = " ".join(kept)
    text = re.sub(r"\.(Pp|Bl|El|Bd|Ed)\b[^\n]*", " ", text)
    text = re.sub(r"\.Fl\s+(-?[A-Za-z0-9_.+-]+)", lambda m: "-" + m.group(1), text)
    text = re.sub(r"\.Ar\s+([A-Za-z0-9_.+-]+)", r"\1", text)
    text = re.sub(r"\.Dv\s+([A-Za-z0-9_.+-]+)", r"\1", text)
    text = re.sub(r"\.Ic\s+([A-Za-z0-9_.+-]+)", r"\1", text)
    text = re.sub(r"\.Nm\b", "mold", text)
    text = text.replace("\\-", "-")
    text = text.replace("\\", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s+([.,;:])", r"\1", text)


def parse_man_options(text: str, source_path: str) -> list[dict[str, object]]:
    if re.search(r"(?m)^\.Sh\s+", text):
        return parse_mdoc_options(text, source_path)
    return parse_nroff_options(text, source_path)


def parse_nroff_options(text: str, source_path: str) -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    in_options = False
    pending_forms: list[str] = []
    pending_line = 0
    desc_lines: list[str] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.startswith(".SH "):
            if in_options:
                break
            in_options = line.strip() == ".SH OPTIONS"
            continue
        if not in_options:
            continue
        form = extract_man_ip(line)
        if form is not None:
            if pending_forms and desc_lines:
                option = make_option(
                    option_id=len(options) + 1,
                    section="OPTIONS",
                    syntax=", ".join(pending_forms),
                    description=" ".join(desc_lines),
                    source_path=source_path,
                    line_no=pending_line,
                )
                if option is not None:
                    options.append(option)
                pending_forms = []
                desc_lines = []
            if not pending_forms:
                pending_line = line_no
            pending_forms.append(form)
            continue
        if line.startswith((".PD", ".PP", ".RS", ".RE")):
            continue
        if pending_forms:
            desc_lines.append(clean_man(line))
    if pending_forms:
        option = make_option(
            option_id=len(options) + 1,
            section="OPTIONS",
            syntax=", ".join(pending_forms),
            description=" ".join(desc_lines),
            source_path=source_path,
            line_no=pending_line,
        )
        if option is not None:
            options.append(option)
    return options


def parse_mdoc_options(text: str, source_path: str) -> list[dict[str, object]]:
    options: list[dict[str, object]] = []
    option_sections = {"OPTIONS", "MOLD-SPECIFIC OPTIONS", "GNU-COMPATIBLE OPTIONS"}
    in_options = False
    current_section = "OPTIONS"
    pending_forms: list[str] = []
    pending_line = 0
    desc_lines: list[str] = []

    def flush_pending() -> None:
        nonlocal pending_forms, pending_line, desc_lines
        if not pending_forms:
            return
        option = make_option(
            option_id=len(options) + 1,
            section=current_section,
            syntax=", ".join(pending_forms),
            description=clean_mdoc_description(desc_lines),
            source_path=source_path,
            line_no=pending_line,
        )
        if option is not None:
            options.append(option)
        pending_forms = []
        desc_lines = []

    for line_no, line in enumerate(text.splitlines(), start=1):
        if line.startswith(".Sh "):
            flush_pending()
            heading = line.removeprefix(".Sh").strip().strip('"')
            if heading in option_sections:
                in_options = True
                current_section = heading
                continue
            if in_options:
                break
            continue
        if not in_options:
            continue
        if line.startswith(".It "):
            form = mdoc_form(line)
            if pending_forms and desc_lines:
                flush_pending()
            if form:
                if not pending_forms:
                    pending_line = line_no
                pending_forms.append(form)
            continue
        if line.strip() in {".", ".."} or line.startswith((".Pp", ".Bl", ".El", ".ig", ".\\")):
            continue
        if pending_forms:
            desc_lines.append(line)
    flush_pending()
    return options


def parse_options(text: str, source_path: str) -> list[dict[str, object]]:
    if source_path.endswith(".md"):
        return parse_markdown_options(text, source_path)
    return parse_man_options(text, source_path)


def write_manifest(path: Path, releases: list[dict[str, str]]) -> None:
    lines = [
        "# Generated by scripts/update_mold_options.py --refresh-manifest.",
        "# Edit only when intentionally changing the pinned source set.",
        "",
        "[metadata]",
    ]
    write_table(
        lines,
        {
            "tool": "mold",
            "source_repo": MOLD_REPO_URL,
            "stable_only": True,
            "source_paths": SOURCE_PATHS,
        },
    )
    lines.append("")
    for release in releases:
        lines.append("[[releases]]")
        write_table(lines, release)
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def refresh_manifest(path: Path, cache_dir: Path) -> None:
    output = run(["git", "ls-remote", "--tags", MOLD_GIT_URL, "refs/tags/v*"], timeout=300).stdout
    candidates: dict[str, tuple[str, str, int]] = {}
    for line in output.splitlines():
        sha, ref = line.split("\t", 1)
        if ref.endswith("^{}"):
            continue
        tag = ref.rsplit("/", 1)[1]
        version = normalize_version(tag)
        if version is None:
            continue
        specificity = tag.count(".")
        old = candidates.get(version)
        if old is None or specificity > old[2]:
            candidates[version] = (sha, tag, specificity)
    releases: list[dict[str, str]] = []
    for version, (commit, tag, _) in sorted(candidates.items(), key=lambda item: version_key(item[0])):
        try:
            source_path, _, _ = fetch_first_source(commit, SOURCE_PATHS, cache_dir)
        except Exception:
            continue
        releases.append(
            {
                "version": version,
                "tag": tag,
                "commit": commit,
                "source_path": source_path,
            }
        )
    write_manifest(path, releases)


def load_manifest(path: Path) -> tuple[dict[str, object], list[dict[str, str]]]:
    with path.open("rb") as file:
        data = tomllib.load(file)
    metadata = data.get("metadata", {})
    releases = data.get("releases", [])
    if not isinstance(metadata, dict) or not isinstance(releases, list):
        raise ValueError(f"invalid manifest shape: {path}")
    return metadata, releases


def generate_release(
    release: dict[str, str],
    metadata: dict[str, object],
    *,
    output_dir: Path,
    cache_dir: Path,
) -> Path:
    version = release["version"]
    source_path = release["source_path"]
    data, source_sha = fetch_source(release["commit"], source_path, cache_dir)
    text = data.decode("utf-8", errors="replace")
    options = parse_options(text, source_path)
    output = version_output_path(output_dir, version)
    lines = [
        "# Generated by scripts/update_mold_options.py --generate.",
        "# Do not edit by hand.",
        "",
        "[metadata]",
    ]
    write_table(
        lines,
        {
            "schema_version": 1,
            "tool": "mold",
            "version": version,
            "source_repo": MOLD_REPO_URL,
            "source_tag": release["tag"],
            "source_commit": release["commit"],
            "source_path": source_path,
            "source_sha256": source_sha,
            "generator": "scripts/update_mold_options.py",
            "option_count": len(options),
        },
    )
    lines.append("")
    lines.append("[[source_files]]")
    write_table(
        lines,
        {
            "path": source_path,
            "ref": release["commit"],
            "sha256": source_sha,
            "url": source_url(release["commit"], source_path),
        },
    )
    lines.append("")
    for option in options:
        lines.append("[[options]]")
        write_table(lines, option)
        lines.append("")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return output


def select_releases(
    releases: list[dict[str, str]],
    versions: list[str] | None,
) -> list[dict[str, str]]:
    if not versions:
        return releases
    wanted = set(versions)
    selected = [release for release in releases if release["version"] in wanted]
    found = {release["version"] for release in selected}
    missing = sorted(wanted - found, key=version_key)
    if missing:
        raise SystemExit(f"versions not in manifest: {', '.join(missing)}")
    return selected


def verify_outputs(
    releases: list[dict[str, str]],
    metadata: dict[str, object],
    *,
    output_dir: Path,
    cache_dir: Path,
) -> None:
    with tempfile.TemporaryDirectory(prefix="mold-options-verify-") as tmp:
        temp_output = Path(tmp) / "option" / "mold"
        for release in releases:
            generate_release(release, metadata, output_dir=temp_output, cache_dir=cache_dir)
        failures: list[str] = []
        for release in releases:
            rel = Path(major_version(release["version"])) / f"{release['version']}.toml"
            expected = output_dir / rel
            actual = temp_output / rel
            if not expected.exists():
                failures.append(f"missing generated file: {expected}")
                continue
            if expected.read_bytes() != actual.read_bytes():
                failures.append(f"not reproducible: {expected}")
    if failures:
        raise SystemExit("\n".join(failures))


def remove_stale_outputs(output_dir: Path, releases: list[dict[str, str]]) -> None:
    keep = {
        str(Path(major_version(release["version"])) / f"{release['version']}.toml")
        for release in releases
    }
    for path in output_dir.rglob("*.toml"):
        if path.name == "manifest.toml":
            continue
        rel = path.relative_to(output_dir).as_posix()
        if rel not in keep:
            path.unlink()
    for path in sorted(output_dir.iterdir(), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--cache-dir", type=Path, default=DEFAULT_CACHE_DIR)
    parser.add_argument("--refresh-manifest", action="store_true")
    parser.add_argument("--generate", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--clean", action="store_true")
    parser.add_argument("--versions", nargs="*", help="versions to process")
    args = parser.parse_args(argv)

    if args.refresh_manifest:
        refresh_manifest(args.manifest, args.cache_dir)
    if not args.generate and not args.verify and not args.clean:
        return 0

    metadata, releases = load_manifest(args.manifest)
    selected = select_releases(releases, args.versions)
    if args.generate:
        for release in selected:
            output = generate_release(release, metadata, output_dir=args.output_dir, cache_dir=args.cache_dir)
            print(output.relative_to(ROOT))
    if args.clean:
        remove_stale_outputs(args.output_dir, releases)
    if args.verify:
        verify_outputs(selected, metadata, output_dir=args.output_dir, cache_dir=args.cache_dir)
        print("mold option metadata is reproducible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
