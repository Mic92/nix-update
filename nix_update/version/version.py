from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class Commit:
    sha: str
    date: datetime | None


@dataclass
class Version:
    number: str
    prerelease: bool | None = None
    rev: str | None = None
    tag: str | None = None
    commit: Commit | None = None


class VersionPreference(StrEnum):
    STABLE = auto()
    UNSTABLE = auto()
    FIXED = auto()
    SKIP = auto()
    BRANCH = auto()

    @staticmethod
    def from_str(version: str) -> VersionPreference:
        # auto is deprecated
        if version in ("auto", "stable"):
            return VersionPreference.STABLE
        if version == "unstable":
            return VersionPreference.UNSTABLE
        if version == "skip":
            return VersionPreference.SKIP
        if version == "branch" or version.startswith("branch="):
            return VersionPreference.BRANCH
        return VersionPreference.FIXED
