from dataclasses import dataclass
from typing import Optional
from .version.version import VersionPreference


@dataclass
class Options:
    attribute: str
    version: str = "stable"
    version_preference: VersionPreference = VersionPreference.STABLE
    version_regex: str = "(.*)"
    import_path: str = "./."
    override_filename: Optional[str] = None
    commit: bool = False
    write_commit_message: Optional[str] = None
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
