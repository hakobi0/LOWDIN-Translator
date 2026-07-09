"""
Shared rigid-body transform helpers (translation and rotation).

Kept dependency-free (NumPy only) so both the interactive geometry editor and
the headless MolecularAssembly model can use the exact same math without
pulling in a rendering library.

The rotation convention matches the legacy GEN program: Euler angles in degrees
about the X, Y and Z axes, applied in that order (Rz . Ry . Rx).
"""

import numpy as np


def rotation_matrix(ax_deg, ay_deg, az_deg):
    """Return the 3x3 rotation matrix for Euler angles (degrees), order X-Y-Z."""
    tx, ty, tz = np.radians([float(ax_deg), float(ay_deg), float(az_deg)])
    rx = np.array([[1.0, 0.0, 0.0],
                   [0.0, np.cos(tx), -np.sin(tx)],
                   [0.0, np.sin(tx),  np.cos(tx)]])
    ry = np.array([[ np.cos(ty), 0.0, np.sin(ty)],
                   [0.0, 1.0, 0.0],
                   [-np.sin(ty), 0.0, np.cos(ty)]])
    rz = np.array([[np.cos(tz), -np.sin(tz), 0.0],
                   [np.sin(tz),  np.cos(tz), 0.0],
                   [0.0, 0.0, 1.0]])
    return rz @ ry @ rx


def apply_matrix(x, y, z, matrix, pivot=(0.0, 0.0, 0.0)):
    """Rotate point (x, y, z) by `matrix` about `pivot`. Returns a float tuple."""
    p = np.asarray(pivot, dtype=float)
    v = matrix @ (np.array([x, y, z], dtype=float) - p) + p
    return float(v[0]), float(v[1]), float(v[2])
