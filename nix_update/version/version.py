#!/usr/bin/env python3
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


@dataclass
class Version:
    number: str
    prerelease: Optional[bool] = None
    rev: Optional[str] = None


class VersionPreference(Enum):
    STABLE = auto()
    UNSTABLE = auto()
    FIXED = auto()
    SKIP = auto()

    @staticmethod
    def from_str(version: str) -> "VersionPreference":
        # auto is deprecated
        if version == "auto" or version == "stable":
            return VersionPreference.STABLE
        elif version == "unstable":
            return VersionPreference.UNSTABLE
        elif version == "skip":
            return VersionPreference.SKIP
        return VersionPreference.FIXED
