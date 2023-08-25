import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(TEST_ROOT.parent))


class Helpers:
    @staticmethod
    def root() -> Path:
        return TEST_ROOT

    @staticmethod
    @contextmanager
    def testpkgs(init_git: bool = False) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copytree(
                Helpers.root().joinpath("testpkgs"), tmpdirname, dirs_exist_ok=True
            )
            if init_git:
                os.environ["GIT_AUTHOR_NAME"] = "nix-update"
                os.environ["GIT_AUTHOR_EMAIL"] = "nix-update@example.com"
                os.environ["GIT_COMMITTER_NAME"] = "nix-update"
                os.environ["GIT_COMMITTER_EMAIL"] = "nix-update@example.com"

                subprocess.run(["git", "-C", tmpdirname, "init"], check=True)
                subprocess.run(["git", "-C", tmpdirname, "add", "--all"], check=True)
                subprocess.run(
                    ["git", "-C", tmpdirname, "commit", "-m", "first commit"],
                    check=True,
                )
            yield Path(tmpdirname)


@pytest.fixture  # type: ignore
def helpers() -> type[Helpers]:
    return Helpers
