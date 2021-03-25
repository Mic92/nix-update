#!/usr/bin/env python3

import pytest
import sys
from pathlib import Path
from typing import Type, Iterator, Any
import shutil
import tempfile
from contextlib import contextmanager


TEST_ROOT = Path(__file__).parent.resolve()
sys.path.append(str(TEST_ROOT.parent))


class Helpers:
    @staticmethod
    def root() -> Path:
        return TEST_ROOT

    @staticmethod
    @contextmanager
    def testpkgs() -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as tmpdirname:
            shutil.copytree(
                Helpers.root().joinpath("testpkgs"), tmpdirname, dirs_exist_ok=True
            )
            yield Path(tmpdirname)

@pytest.fixture # type: ignore
def helpers() -> Type[Helpers]:
    return Helpers
