from dataclasses import dataclass


@dataclass
class Options:
    version: str
    import_path: str
    attribute: str
    shell: bool
    run: bool
    build: bool
