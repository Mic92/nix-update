"""
Version comparison for package version strings.

This module implements a sophisticated version comparison algorithm that handles
complex version strings commonly found in package managers. It supports:
- Epoch prefixes (e.g., "1:2.0.0")
- Release suffixes (e.g., "1.0.0-1")
- Mixed alphanumeric segments
- Special separator handling

The implementation is inspired by RPM-style version comparison but is an
independent implementation written specifically for nix-update.
"""


def _cmp_str(a: str, b: str) -> int:
    """Return -1, 0, or 1 comparing two strings lexicographically."""
    if a < b:
        return -1
    if a > b:
        return 1
    return 0


class VersionSegment:
    """Represents a parsed segment of a version string."""

    def __init__(self, value: str, *, is_numeric: bool) -> None:
        self.value = value
        self.is_numeric = is_numeric

    def compare_to(self, other: "VersionSegment") -> int:
        """
        Compare this segment to another.

        Returns:
            1 if self > other, -1 if self < other, 0 if equal
        """
        # Numeric segments are always considered newer than alpha segments
        if self.is_numeric != other.is_numeric:
            return 1 if self.is_numeric else -1

        if self.is_numeric:
            # For numeric comparison, strip leading zeros and compare by length first
            val1 = self.value.lstrip("0") or "0"
            val2 = other.value.lstrip("0") or "0"

            # Longer number means larger value
            if len(val1) != len(val2):
                return 1 if len(val1) > len(val2) else -1

            # Same length, compare lexicographically
            return _cmp_str(val1, val2)
        # Alphabetic comparison
        return _cmp_str(self.value, other.value)


class VersionString:
    """Represents a complete version string with epoch, version, and release."""

    def __init__(self, version_str: str) -> None:
        self.epoch, self.version, self.release = self._parse_version(version_str)

    def _parse_version(self, ver: str) -> tuple[str, str, str | None]:
        """
        Parse a version string into epoch, version, and release components.

        Format: [epoch:]version[-release]
        """
        epoch = "0"
        version = ver
        release = None

        # Extract epoch if present (numeric prefix before colon)
        colon_pos = ver.find(":")
        if colon_pos > 0 and ver[:colon_pos].isdigit():
            epoch = ver[:colon_pos]
            version = ver[colon_pos + 1 :]
        elif colon_pos == 0:
            # Empty epoch defaults to 0
            epoch = "0"
            version = ver[1:]

        # Extract release if present (suffix after last dash)
        dash_pos = version.rfind("-")
        if dash_pos >= 0:
            release = version[dash_pos + 1 :]
            version = version[:dash_pos]

        return epoch, version, release

    def _extract_segments(self, s: str) -> list[tuple[VersionSegment, int]]:
        """
        Extract alternating alpha/numeric segments with separator lengths.

        Returns list of (segment, separator_length_before) tuples.
        """
        segments: list[tuple[VersionSegment, int]] = []
        pos = 0

        while pos < len(s):
            # Skip non-alphanumeric characters
            sep_start = pos
            while pos < len(s) and not s[pos].isalnum():
                pos += 1

            if pos >= len(s):
                break

            sep_len = pos - sep_start

            # Extract segment (all digits or all letters)
            seg_start = pos
            if s[pos].isdigit():
                while pos < len(s) and s[pos].isdigit():
                    pos += 1
                segment = VersionSegment(s[seg_start:pos], is_numeric=True)
            else:
                while pos < len(s) and s[pos].isalpha():
                    pos += 1
                segment = VersionSegment(s[seg_start:pos], is_numeric=False)

            segments.append((segment, sep_len))

        return segments

    def _compare_segment_lists(
        self,
        segs1: list[tuple[VersionSegment, int]],
        segs2: list[tuple[VersionSegment, int]],
    ) -> int:
        """Compare two lists of version segments."""
        for i in range(min(len(segs1), len(segs2))):
            seg1, sep_len1 = segs1[i]
            seg2, sep_len2 = segs2[i]

            # Different separator lengths means different versions
            if i > 0 and sep_len1 != sep_len2:
                return -1 if sep_len1 < sep_len2 else 1

            # Compare the actual segments
            result = seg1.compare_to(seg2)
            if result != 0:
                return result

        # All compared segments are equal, check if one has more segments
        if len(segs1) == len(segs2):
            return 0

        # Determine which side has extra segments and the sign of the result
        longer, shorter, sign = (
            (segs1, segs2, 1) if len(segs1) > len(segs2) else (segs2, segs1, -1)
        )
        next_seg, sep_len = longer[len(shorter)]

        if next_seg.is_numeric:
            # Numeric segment always makes version newer
            return sign
        # Alpha segment behavior depends on separator:
        # - With separator (sep_len > 0): treated as new segment, makes version newer
        # - Without separator (sep_len == 0): treated as pre-release suffix, makes version older
        return sign if sep_len > 0 else -sign

    def _compare_component(self, comp1: str, comp2: str) -> int:
        """Compare two version components (epoch, version, or release)."""
        if comp1 == comp2:
            return 0

        segs1 = self._extract_segments(comp1)
        segs2 = self._extract_segments(comp2)

        return self._compare_segment_lists(segs1, segs2)

    def compare_to(self, other: "VersionString") -> int:
        """
        Compare this version to another.

        Returns:
            1 if self > other, -1 if self < other, 0 if equal
        """
        # Compare epochs first
        result = self._compare_component(self.epoch, other.epoch)
        if result != 0:
            return result

        # Compare versions
        result = self._compare_component(self.version, other.version)
        if result != 0:
            return result

        # Compare releases if both exist
        if self.release is not None and other.release is not None:
            return self._compare_component(self.release, other.release)

        # Version with release is considered newer than without
        if self.release is not None:
            return 1
        if other.release is not None:
            return -1

        return 0


def version_compare(a: str | None, b: str | None) -> int:
    """
    Compare two package version strings.

    This function handles version strings in the format:
        [epoch:]version[-release]

    Where:
        - epoch: Optional numeric prefix followed by colon (e.g., "1:")
        - version: The main version string
        - release: Optional release number after a dash (e.g., "-1")

    The comparison algorithm:
    1. Compares epochs numerically (if present)
    2. Compares version segments (numeric > alpha, longer numeric > shorter)
    3. Compares release segments (if present)
    4. Considers separator lengths when comparing

    Examples:
        >>> version_compare("1.0.0", "2.0.0")
        -1
        >>> version_compare("2.0.0", "1.0.0")
        1
        >>> version_compare("1.0.0", "1.0.0")
        0
        >>> version_compare("1:1.0.0", "2.0.0")
        1
        >>> version_compare("1.0.0-1", "1.0.0-2")
        -1

    Args:
        a: First version string (can be None)
        b: Second version string (can be None)

    Returns:
        1 if a is newer than b
        0 if a and b are the same version
        -1 if b is newer than a
    """
    # Handle None values
    if a is None and b is None:
        return 0
    if a is None:
        return -1
    if b is None:
        return 1

    # Quick shortcut for identical strings
    if a == b:
        return 0

    # Parse and compare version strings
    ver_a = VersionString(a)
    ver_b = VersionString(b)

    return ver_a.compare_to(ver_b)
