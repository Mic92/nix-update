import tomllib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path


def _version() -> str:
    try:
        return version("nix-update")
    except PackageNotFoundError:
        # running from a source checkout without installed metadata
        pyproject = Path(__file__).parent.parent / "pyproject.toml"
        try:
            with pyproject.open("rb") as f:
                return str(tomllib.load(f)["project"]["version"])
        except OSError:
            return "unknown"


VERSION = _version()
