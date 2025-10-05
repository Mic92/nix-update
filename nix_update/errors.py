from __future__ import annotations


class UpdateError(Exception):
    pass


class VersionError(UpdateError):
    pass


class AttributePathError(UpdateError):
    pass
