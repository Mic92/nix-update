#!/usr/bin/env python3

import subprocess
from typing import Optional
import re


def old_version_from_diff(
    diff: str, linenumber: int, new_version: str
) -> Optional[str]:
    current_line = 0
    old_str = None
    new_str = None
    regex = re.compile(r"^@@ -(\d+),(\d+) \+(\d+),(\d+) @@$")
    for line in diff.split("\n"):
        match = regex.match(line)
        if match:
            current_line = int(match.group(3))
        elif line.startswith("~"):
            current_line += 1
            if current_line > linenumber:
                return None
        elif linenumber == current_line and line.startswith("-"):
            old_str = line[1:]
        elif linenumber == current_line and line.startswith("+"):
            if new_version not in line:
                old_str = None
            else:
                new_str = line[1:]
                break
    if not new_str or not old_str:
        return None
    idx = new_str.index(new_version)
    prefix = new_str[:idx]
    suffix = new_str[idx + len(new_version):]
    return old_str.lstrip(prefix).rstrip(suffix)


def old_version_from_git(
    filename: str, linenumber: int, new_version: str
) -> Optional[str]:
    proc = subprocess.run(
        ["git", "diff", "--color=never", "--word-diff=porcelain", "--", filename],
        text=True,
        stdout=subprocess.PIPE,
    )
    assert proc.stdout is not None
    if len(proc.stdout) == 0:
        return None
    return old_version_from_diff(proc.stdout, linenumber, new_version)
