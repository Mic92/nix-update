"""Syntax-aware edits of Nix files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ast_grep_py import SgRoot

if TYPE_CHECKING:
    from ast_grep_py import SgNode


Edit = tuple[int, int, str]


def parse(text: str) -> SgNode | None:
    """Parse Nix code; None for anything else, such as JSON given via --override-filename."""
    root = SgRoot(text, "nix").root()
    return None if root.find(kind="ERROR") else root


def bindings(root: SgNode, name: str, *, nested: bool = False) -> list[SgNode]:
    """All ``name = ...;`` bindings, with ``nested`` also ``name.<...> = ...;``."""
    return [
        binding
        for binding in root.find_all(kind="binding")
        if (attrpath := binding.field("attrpath"))
        and (
            attrpath.text() == name
            or (nested and attrpath.text().startswith(f"{name}."))
        )
    ]


def _find_binding(root: SgNode, name: str, line: int) -> SgNode | None:
    """Find ``name = ...;`` at the 1-based line, or the only one in the file."""
    found = bindings(root, name)
    for binding in found:
        if binding.range().start.line == line - 1:
            return binding
    return found[0] if len(found) == 1 else None


def whole_lines(text: str, start: int, end: int) -> tuple[int, int]:
    """Widen the span to full lines if nothing else is on them."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0 or text[line_start:start].strip() or text[end:line_end].strip():
        return start, end
    return line_start, line_end + 1


def apply_edits(text: str, edits: list[Edit]) -> str:
    for start, end, replacement in sorted(edits, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def replace_in_strings(
    text: str, old: str, new: str, *, whole: bool = False, line: int | None = None
) -> str:
    """Replace ``old`` inside string literals and comments, leaving code alone.

    With ``whole`` only strings that are exactly ``old`` are replaced, and
    ``line`` limits the replacement to that 1-based line.
    """
    root = parse(text)
    if root is None:
        if whole:
            old, new = f'"{old}"', f'"{new}"'
        lines = text.splitlines(keepends=True)
        return "".join(
            item.replace(old, new) if line in (None, number) else item
            for number, item in enumerate(lines, 1)
        )

    edits: list[Edit] = []
    # Comments often link to the pinned rev, so partial matches follow there too
    kinds = ["string_fragment", "uri_expression"] + ([] if whole else ["comment"])
    for kind in kinds:
        for node in root.find_all(kind=kind):
            rng = node.range()
            if line is not None and rng.start.line != line - 1:
                continue
            content = node.text()
            if whole:
                parent = node.parent()
                if parent is None or parent.text() != f'"{old}"':
                    continue
            if old in content:
                edits.append(
                    (rng.start.index, rng.end.index, content.replace(old, new))
                )
    return apply_edits(text, edits)


def remove_list_elements(
    filename: str, name: str, line: int, indices: set[int]
) -> set[int]:
    """Remove elements of the list bound to ``name`` and return those removed.

    Comments belonging to a removed element go with it.  For
    ``[ ... ] ++ ...`` only the leading list is considered.
    """
    path = Path(filename)
    text = path.read_text()
    root = parse(text)
    binding = _find_binding(root, name, line) if root else None
    value = binding.field("expression") if binding else None
    while value and value.kind() == "binary_expression":
        value = value.field("left")
    if value is None or value.kind() != "list_expression":
        return set()

    # An element owns the comment block directly above it and a comment
    # trailing it on the same line.
    spans: list[tuple[int, int]] = []
    comment_start = None
    comment_line = element_line = -1
    for child in value.children():
        if not child.is_named():
            continue
        rng = child.range()
        if child.kind() != "comment":
            start = rng.start.index
            if comment_start is not None and rng.start.line <= comment_line + 1:
                start = comment_start
            spans.append((start, rng.end.index))
            comment_start = None
            element_line = rng.end.line
        elif rng.start.line == element_line:
            spans[-1] = (spans[-1][0], rng.end.index)
        else:
            if comment_start is None or rng.start.line > comment_line + 1:
                comment_start = rng.start.index
            comment_line = rng.end.line
    spans = [whole_lines(text, *span) for span in spans]

    removed = {index for index in indices if index < len(spans)}
    if removed:
        path.write_text(apply_edits(text, [(*spans[i], "") for i in removed]))
    return removed
