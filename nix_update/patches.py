from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from .utils import info, nix_command, run

if TYPE_CHECKING:
    from .eval import Package
    from .options import Options


def _skip_space_and_comments(text: str, offset: int) -> int:
    while offset < len(text):
        if text[offset].isspace():
            offset += 1
        elif text.startswith("#", offset):
            newline = text.find("\n", offset)
            offset = len(text) if newline < 0 else newline + 1
        elif text.startswith("/*", offset):
            end = text.find("*/", offset + 2)
            offset = len(text) if end < 0 else end + 2
        else:
            break
    return offset


def _quoted_end(text: str, offset: int) -> int:
    indented = text.startswith("''", offset)
    delimiter = "''" if indented else '"'
    offset += len(delimiter)
    while offset < len(text):
        if not indented and text[offset] == "\\":
            offset += 2
        elif text.startswith(delimiter, offset):
            return offset + len(delimiter)
        else:
            offset += 1
    return len(text)


def _element_end(text: str, offset: int) -> int:
    if text[offset] == '"' or text.startswith("''", offset):
        return _quoted_end(text, offset)
    pairs = {"(": ")", "{": "}", "[": "]"}
    if text[offset] not in pairs:
        end = offset
        while end < len(text) and not text[end].isspace() and text[end] != "]":
            end += 1
        return end

    stack = [pairs[text[offset]]]
    offset += 1
    while offset < len(text) and stack:
        if text[offset] == '"' or text.startswith("''", offset):
            offset = _quoted_end(text, offset)
            continue
        if text.startswith("#", offset):
            newline = text.find("\n", offset)
            offset = len(text) if newline < 0 else newline + 1
            continue
        if text.startswith("/*", offset):
            end = text.find("*/", offset + 2)
            offset = len(text) if end < 0 else end + 2
            continue
        if text[offset] in pairs:
            stack.append(pairs[text[offset]])
        elif text[offset] == stack[-1]:
            stack.pop()
        offset += 1
    return offset


def drop_patch_indices(filename: str, line: int, indices: set[int]) -> set[int]:
    """Drop resolved list entries by index, independent of their Nix type."""
    path = Path(filename)
    text = path.read_text()
    offset = sum(len(part) for part in text.splitlines(keepends=True)[: line - 1])
    assignment = text.find("patches", offset)
    if assignment < 0:
        match = re.search(r"\bpatches\s*=", text)
        assignment = -1 if match is None else match.start()
    equals = text.find("=", assignment)
    list_start = _skip_space_and_comments(text, equals + 1)
    if assignment < 0 or equals < 0 or text[list_start : list_start + 1] != "[":
        return set()

    spans: list[tuple[int, int]] = []
    cursor = list_start + 1
    while True:
        cursor = _skip_space_and_comments(text, cursor)
        if cursor >= len(text) or text[cursor] == "]":
            break
        end = _element_end(text, cursor)
        start = cursor
        line_start = text.rfind("\n", 0, start) + 1
        line_end = text.find("\n", end)
        if (
            not text[line_start:start].strip()
            and line_end >= 0
            and not text[end:line_end].strip()
        ):
            start = line_start
            end = line_end + 1
        spans.append((start, end))
        cursor = end

    removed: set[int] = set()
    for index in sorted(indices, reverse=True):
        if index < len(spans):
            start, end = spans[index]
            text = text[:start] + text[end:]
            removed.add(index)
    path.write_text(text)
    return removed


def _merged_patch_indices(opts: Options) -> set[int]:
    """Unpack the new source and find patches that apply cleanly in reverse."""
    package_expr = opts.get_package()
    expression = f"""let
      pkg = {package_expr};
      originalPatches = pkg.patches or [ ];
      patches = map (candidate:
        if builtins.isPath candidate then
          builtins.path {{ path = candidate; name = builtins.baseNameOf candidate; }}
        else candidate
      ) originalPatches;
      lib = (import <nixpkgs> {{ }}).lib;
      flagsValue = pkg.patchFlags or [ "-p1" ];
      flags = if builtins.isList flagsValue then flagsValue else [ flagsValue ];
    in pkg.overrideAttrs (old: {{
      name = "${{pkg.name}}-merged-patches";
      patches = [ ];
      patchInputs = patches;
      phases = [ "unpackPhase" "installPhase" ];
      installPhase = ''
        mkdir -p "$out"
        i=0
        for candidate in ${{lib.escapeShellArgs (map toString patches)}}; do
          if patch --force --reverse --silent --dry-run ${{lib.escapeShellArgs flags}} < "$candidate"; then
            touch "$out/$i"
          fi
          i=$((i + 1))
        done
      '';
    }})"""
    result = run(
        [
            *nix_command("build", "--no-link", "--print-out-paths"),
            *opts.extra_flags,
            "--impure",
            "--expr",
            expression,
        ],
    )
    output = Path(result.stdout.strip())
    return {int(marker.name) for marker in output.iterdir() if marker.name.isdigit()}


def drop_merged_patches(opts: Options, package: Package) -> None:
    if not package.patches or package.patches_position is None:
        return
    merged = _merged_patch_indices(opts)
    dropped = drop_patch_indices(
        package.filename, package.patches_position.line, merged
    )
    for index in sorted(dropped):
        patch = Path(str(package.patches[index]["path"])).name
        info(f"Drop patch already applied upstream: {patch}")
