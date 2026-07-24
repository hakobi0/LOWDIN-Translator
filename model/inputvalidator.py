"""
Validates LOWDIN input parameters and suggests the correct R/U method.
"""

from model.variablesglobales import NUMERO_ATOMICO

# Methods that require closed-shell (paired electrons, mult=1)
CLOSED_SHELL_METHODS = {"RHF", "RKS"}

# Methods that require open-shell (unpaired electrons, mult>1 or odd electrons)
OPEN_SHELL_METHODS = {"UHF", "UKS"}

# DFT functional names that map to RKS/UKS
DFT_FUNCTIONALS = {"B3LYP", "PBE", "BLYP", "PBE0", "LDA"}

# MP2 maps to RHF (closed) or UHF (open)
MP2_METHODS = {"MP2"}


def count_electrons(atoms, charge):
    """
    Count total electrons from atom list and charge.

    Args:
        atoms: list of (symbol, x, y, z)
        charge: molecular charge (int)

    Returns:
        int: total electron count, or None if an element is unknown
    """
    total = 0
    for symbol, *_ in atoms:
        z = NUMERO_ATOMICO.get(str(symbol).capitalize())
        if z is None:
            return None
        total += z
    return total - charge


def is_open_shell(atoms, charge, multiplicity):
    """
    Determine if the system is open-shell from electron count and multiplicity.

    Returns:
        tuple(bool, list[str]): (is_open_shell, list of error/warning messages)
    """
    issues = []
    n_elec = count_electrons(atoms, charge)

    if n_elec is None:
        issues.append("Unknown element in geometry — cannot verify electron count.")
        return None, issues

    if n_elec <= 0:
        issues.append(f"Total electron count is {n_elec}. Check charge.")
        return None, issues

    # Multiplicity consistency: mult = 2S+1, so unpaired = mult-1
    # Parity check: (n_elec - unpaired) must be even (remaining paired electrons)
    unpaired = multiplicity - 1
    remaining = n_elec - unpaired

    if remaining < 0:
        issues.append(
            f"Multiplicity {multiplicity} requires {unpaired} unpaired electrons "
            f"but the system only has {n_elec} electrons total."
        )
        return None, issues

    if remaining % 2 != 0:
        issues.append(
            f"Multiplicity {multiplicity} is inconsistent with {n_elec} electrons "
            f"and charge {charge:+d}. "
            f"({n_elec} electrons - {unpaired} unpaired = {remaining}, which is odd.)"
        )
        return None, issues

    open_shell = unpaired > 0
    return open_shell, issues


def suggest_method(current_method, atoms, charge, multiplicity):
    """
    Given the current method selection and system parameters, return:
        - corrected_method: the right method (may equal current_method if already correct)
        - warnings: list of human-readable warning strings
        - errors: list of blocking error strings

    Returns:
        dict with keys: 'corrected_method', 'warnings', 'errors'
    """
    warnings = []
    errors = []

    open_shell, spin_issues = is_open_shell(atoms, charge, multiplicity)
    errors.extend(spin_issues)

    if open_shell is None:
        return {
            "corrected_method": current_method,
            "warnings": warnings,
            "errors": errors,
        }

    # Determine the correct R/U variant
    if current_method in CLOSED_SHELL_METHODS:
        corrected = current_method
        if open_shell:
            corrected = "UHF" if current_method == "RHF" else "UKS"
            warnings.append(
                f"Method changed from {current_method} to {corrected}: "
                f"the system has unpaired electrons (mult={multiplicity})."
            )

    elif current_method in OPEN_SHELL_METHODS:
        corrected = current_method
        if not open_shell:
            corrected = "RHF" if current_method == "UHF" else "RKS"
            warnings.append(
                f"Method changed from {current_method} to {corrected}: "
                f"the system is closed-shell (mult=1, even electrons)."
            )

    elif current_method in DFT_FUNCTIONALS:
        corrected = "UKS" if open_shell else "RKS"
        warnings.append(
            f"DFT functional {current_method} → method={corrected} "
            f"with electronExchangeCorrelationFunctional=\"{current_method}\"."
        )

    elif current_method in MP2_METHODS:
        corrected = current_method
        if open_shell:
            warnings.append(
                "MP2 with open-shell system: UHF reference will be used automatically."
            )

    else:
        corrected = current_method  # MM or unknown — skip

    return {
        "corrected_method": corrected,
        "warnings": warnings,
        "errors": errors,
    }


def validation_summary(atoms, charge, multiplicity, method):
    """
    Full validation summary as a list of (level, message) tuples.
    level is 'error', 'warning', or 'info'.
    """
    result = suggest_method(method, atoms, charge, multiplicity)
    messages = []

    for e in result["errors"]:
        messages.append(("error", e))
    for w in result["warnings"]:
        messages.append(("warning", w))

    n_elec = count_electrons(atoms, charge)
    if n_elec is not None and n_elec > 0:
        open_shell, _ = is_open_shell(atoms, charge, multiplicity)
        shell_str = "open-shell" if open_shell else "closed-shell"
        messages.append(("info", f"{n_elec} electrons  |  {shell_str}  |  mult={multiplicity}  |  charge={charge:+d}"))

    return messages
