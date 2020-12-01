#!/usr/bin/env python3

from pathlib import Path
from unittest import TestCase
from nix_update.git import old_version_from_diff


TEST_ROOT = Path(__file__).parent.resolve()


class WordDiff(TestCase):
    def test_worddiff(self) -> None:
        with open(TEST_ROOT.joinpath("consul.patch")) as f:
            diff = f.read()
        s = old_version_from_diff(diff, 5, "1.9.0")
        self.assertEqual(s, "1.8.6")
