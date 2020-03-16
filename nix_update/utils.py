import os
import subprocess
import sys
from pathlib import Path
from typing import IO, Any, Callable, List, Optional, Union

HAS_TTY = sys.stdout.isatty()
ROOT = Path(os.path.dirname(os.path.realpath(__file__)))


def color_text(code: int, file: IO[Any] = sys.stdout) -> Callable[[str], None]:
    def wrapper(text: str) -> None:
        if HAS_TTY:
            print(f"\x1b[{code}m{text}\x1b[0m", file=file)
        else:
            print(text, file=file)

    return wrapper


warn = color_text(31, file=sys.stderr)
info = color_text(32)


def run(
    command: List[str],
    cwd: Optional[Union[Path, str]] = None,
    stdout: Union[None, int, IO[Any]] = subprocess.PIPE,
) -> subprocess.CompletedProcess:
    info("$ " + " ".join(command))
    return subprocess.run(command, cwd=cwd, check=True, text=True, stdout=stdout)
