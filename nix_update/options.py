import json
import os
from dataclasses import dataclass, field

from .version.version import VersionPreference


@dataclass
class Options:
    attribute: str
    flake: bool = False
    version: str = "stable"
    version_preference: VersionPreference = VersionPreference.STABLE
    version_regex: str = "(.*)"
    import_path: str = os.getcwd()
    subpackages: list[str] | None = None
    override_filename: str | None = None
    url: str | None = None
    commit: bool = False
    use_update_script: bool = False
    update_script_args: list[str] = field(default_factory=list)
    write_commit_message: str | None = None
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
    system: str | None = None
    generate_lockfile: bool = False
    lockfile_metadata_path: str = "."
    extra_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.escaped_attribute = ".".join(map(json.dumps, self.attribute.split(".")))
        self.escaped_import_path = json.dumps(self.import_path)
