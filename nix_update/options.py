from dataclasses import dataclass


@dataclass
class Options:
    version: str
    import_path: str
    commit: bool
    attribute: str
    shell: bool
    run: bool
    build: bool
    test: bool
