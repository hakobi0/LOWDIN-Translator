"""
Robust basis set name normalization and lookup.

The problem: ORCA uses names like "def2-tzvp", "6-31G(d,p)", "aug-cc-pVDZ".
LOWDIN uses "DEF2-TZVP", "6-31G.D.P", "AUG-CC-PVDZ".
The valid_basis dict covers exact spellings but misses case/punctuation variants.

Solution: normalize both sides by stripping hyphens, dots, parentheses,
commas, spaces and uppercasing, then match on the normalized form.
The '+' is kept because it distinguishes e.g. 6-311G from 6-311+G.

Examples:
    "def2-tzvp"    -> "DEF2TZVP"
    "DEF2-TZVP"    -> "DEF2TZVP"   -> same -> match
    "6-31G(d,p)"   -> "631GDP"
    "6-31G.D.P"    -> "631GDP"     -> same -> match
    "aug-cc-pVDZ"  -> "AUGCCPVDZ"
    "AUG-CC-PVDZ"  -> "AUGCCPVDZ" -> same -> match
    "6-311+G(d)"   -> "6311+GD"
    "6-311+G.D"    -> "6311+GD"   -> same -> match
"""

import re
from model.variablesglobales import valid_basis
from model.basisclassifier import default_basis_dir, all_basis_names


def _normalize(name: str) -> str:
    """Strip punctuation (except +), uppercase."""
    stripped = re.sub(r"[-.()\s,/*]", "", name)
    return stripped.upper()


# Normalized index of the basis files actually present in the LOWDIN library:
#   normalized_name -> real on-disk file name
# This lets us recognize the hundreds of installed basis sets that are not in
# the curated valid_basis dict. It is filled lazily (on first use) from disk, or
# authoritatively by set_available_basis() when the app has already discovered
# the installed bases at start-up.
_AVAILABLE_NORM_TO_NAME: dict[str, str] | None = None


def set_available_basis(names) -> None:
    """
    Register the authoritative list of installed basis names (as discovered at
    start-up). Overrides the lazy on-disk scan so validation matches the user's
    real installation and any config-cached bases.
    """
    global _AVAILABLE_NORM_TO_NAME
    index: dict[str, str] = {}
    for name in names:
        index.setdefault(_normalize(name), name)
    _AVAILABLE_NORM_TO_NAME = index


def _available_basis() -> dict[str, str]:
    """Return the normalized index of installed bases, scanning disk on first use."""
    global _AVAILABLE_NORM_TO_NAME
    if _AVAILABLE_NORM_TO_NAME is None:
        set_available_basis(all_basis_names(default_basis_dir()))
    return _AVAILABLE_NORM_TO_NAME


# Build normalized lookup at import time:
#   normalized_key -> canonical LOWDIN name
_NORMALIZED_TO_LOWDIN: dict[str, str] = {}

for _orca_name, _lowdin_name in valid_basis.items():
    _norm_key = _normalize(_orca_name)
    # If two ORCA names normalize to the same key, keep the first mapping.
    # (Collisions are extremely rare in practice.)
    if _norm_key not in _NORMALIZED_TO_LOWDIN:
        _NORMALIZED_TO_LOWDIN[_norm_key] = _lowdin_name

# Also index by normalized LOWDIN names so we recognize inputs already in
# LOWDIN format (e.g. "AUG-CC-PVDZ" passed straight through).
for _lowdin_name in valid_basis.values():
    _norm_key = _normalize(_lowdin_name)
    if _norm_key not in _NORMALIZED_TO_LOWDIN:
        _NORMALIZED_TO_LOWDIN[_norm_key] = _lowdin_name


def resolve_basis(name: str) -> tuple[str, bool]:
    """
    Resolve an arbitrary basis set name to its canonical LOWDIN spelling.

    Args:
        name: basis set name in any format/case

    Returns:
        (lowdin_name, matched)
            lowdin_name: canonical LOWDIN name if found, otherwise name.upper()
            matched: True if a known mapping was found
    """
    if not name or name.strip() == "":
        return name, False

    # 1. Exact match in the original dict (fastest path)
    if name in valid_basis:
        return valid_basis[name], True

    # 2. Normalized match against the curated ORCA/Gaussian <-> LOWDIN table
    norm = _normalize(name)
    if norm in _NORMALIZED_TO_LOWDIN:
        return _NORMALIZED_TO_LOWDIN[norm], True

    # 3. Match against the basis sets actually installed in the LOWDIN library.
    #    Return the real on-disk file name so the spelling is exactly what
    #    LOWDIN expects.
    available = _available_basis()
    if norm in available:
        return available[norm], True

    # 4. No match — return uppercased name and flag as unknown
    return name.upper(), False


def validate_basis(name: str) -> dict:
    """
    Validate a basis set name and return a result dict with:
        resolved:  canonical LOWDIN name (or uppercased original if unknown)
        matched:   True if a known mapping was found
        warning:   human-readable warning string, or None
    """
    resolved, matched = resolve_basis(name)
    warning = None

    if not matched:
        warning = (
            f'Basis "{name}" was not found in your installed LOWDIN basis library. '
            f'It will be passed as "{resolved}" — check the name or that the basis is installed.'
        )

    return {
        "resolved": resolved,
        "matched": matched,
        "warning": warning,
    }
