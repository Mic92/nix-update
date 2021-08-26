from dataclasses import dataclass
from .version.version import VersionPreference


@dataclass
class Options:
    attribute: str
    version: str = "stable"
    version_preference: VersionPreference = VersionPreference.STABLE
    version_regex: str = "(.*)"
    import_path: str = "./."
    commit: bool = False
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
