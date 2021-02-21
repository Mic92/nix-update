from dataclasses import dataclass


@dataclass
class Options:
    attribute: str
    version: str = "stable"
    version_regex: str = "(.*)"
    import_path: str = "./."
    commit: bool = False
    shell: bool = False
    run: bool = False
    build: bool = False
    test: bool = False
    review: bool = False
    format: bool = False
