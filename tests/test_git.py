from pathlib import Path

import conftest

from nix_update.git import old_version_from_diff

TEST_ROOT = Path(__file__).parent.resolve()


def test_worddiff(helpers: conftest.Helpers) -> None:
    with open(helpers.root().joinpath("consul.patch")) as f:
        diff = f.read()
        s = old_version_from_diff(diff, 5, "1.9.0")
        assert s == "1.8.6"
