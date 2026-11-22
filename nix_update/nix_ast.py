"""Syntax-aware edits of Nix files."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from ast_grep_py import SgRoot

if TYPE_CHECKING:
    from ast_grep_py import SgNode


def _find_binding(root: SgNode, name: str, line: int) -> SgNode | None:
    """Find ``name = ...;`` at the 1-based line, or the only one in the file."""
    bindings = [
        binding
        for binding in root.find_all(kind="binding")
        if (attrpath := binding.field("attrpath")) and attrpath.text() == name
    ]
    for binding in bindings:
        if binding.range().start.line == line - 1:
            return binding
    return bindings[0] if len(bindings) == 1 else None


def _whole_lines(text: str, start: int, end: int) -> tuple[int, int]:
    """Widen the span to full lines if nothing else is on them."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)
    if line_end < 0 or text[line_start:start].strip() or text[end:line_end].strip():
        return start, end
    return line_start, line_end + 1


def remove_list_elements(
    filename: str, name: str, line: int, indices: set[int]
) -> set[int]:
    """Remove elements of the list bound to ``name`` and return those removed.

    Comments on the lines directly above a removed element go with it.  For
    ``[ ... ] ++ ...`` only the leading list is considered.
    """
    path = Path(filename)
    text = path.read_text()
    binding = _find_binding(SgRoot(text, "nix").root(), name, line)
    value = binding.field("expression") if binding else None
    while value and value.kind() == "binary_expression":
        value = value.field("left")
    if value is None or value.kind() != "list_expression":
        return set()

    spans: list[tuple[int, int]] = []
    comment_start = None
    previous_line = -1
    for child in value.children():
        if not child.is_named():
            continue
        rng = child.range()
        if child.kind() == "comment":
            if comment_start is None and rng.start.line > previous_line:
                comment_start = rng.start.index
            continue
        start = rng.start.index if comment_start is None else comment_start
        spans.append(_whole_lines(text, start, rng.end.index))
        comment_start = None
        previous_line = rng.end.line

    removed = {index for index in indices if index < len(spans)}
    for index in sorted(removed, reverse=True):
        start, end = spans[index]
        text = text[:start] + text[end:]
    if removed:
        path.write_text(text)
    return removed
