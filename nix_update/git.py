import re

from .utils import run


def old_version_from_diff(diff: str, linenumber: int, new_version: str) -> str | None:
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
    suffix = new_str[idx + len(new_version) :]
    return old_str.lstrip(prefix).rstrip(suffix)


def old_version_from_git(
    filename: str,
    linenumber: int,
    new_version: str,
) -> str | None:
    proc = run(
        ["git", "diff", "--color=never", "--word-diff=porcelain", "--", filename],
    )
    if proc.stdout is None:
        msg = "Failed to get stdout from git diff command"
        raise RuntimeError(msg)
    if len(proc.stdout) == 0:
        return None
    return old_version_from_diff(proc.stdout, linenumber, new_version)
