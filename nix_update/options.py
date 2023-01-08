import os
from dataclasses import dataclass, field
from typing import List, Optional

from .version.version import VersionPreference


@dataclass
class Options:
    attribute: str
    flake: bool = False
    version: str = "stable"
    version_preference: VersionPreference = VersionPreference.STABLE
    version_regex: str = "(.*)"
    import_path: str = os.getcwd()
    override_filename: Optional[str] = None
    commit: bool = False
    use_update_script: bool = False
    write_commit_message: Optional[str] = None
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
    system: Optional[str] = None
    extra_flags: List[str] = field(default_factory=list)
