from dataclasses import dataclass
from enum import StrEnum, auto


@dataclass
class Version:
    number: str
    prerelease: bool | None = None
    rev: str | None = None


class VersionPreference(StrEnum):
    STABLE = auto()
    UNSTABLE = auto()
    FIXED = auto()
    SKIP = auto()
    BRANCH = auto()

    @staticmethod
    def from_str(version: str) -> "VersionPreference":
        # auto is deprecated
        if version == "auto" or version == "stable":
            return VersionPreference.STABLE
        elif version == "unstable":
            return VersionPreference.UNSTABLE
        elif version == "skip":
            return VersionPreference.SKIP
        elif version == "branch" or version.startswith("branch="):
            return VersionPreference.BRANCH
        return VersionPreference.FIXED
