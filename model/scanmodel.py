"""
Rigid scan generator for PES (potential energy surface) exploration.

Given a molecular geometry and a set of moving atom indices, generates a
sequence of geometries by applying incremental translation and/or rotation
to the moving atoms while keeping the rest fixed.

Three scan types are supported, mirroring the legacy GEN4 program:
  - Translation only  (linear movement along a direction vector)
  - Rotation only     (Euler-angle rotation about the fragment center)
  - Translation + Rotation (combined, applied per step)
"""

import copy
import numpy as np

from model.transforms import rotation_matrix, apply_matrix
from model.variablesglobales import ATOMIC_WEIGHT


SCAN_TRANSLATION = "Translation"
SCAN_ROTATION = "Rotation"
SCAN_BOTH = "Translation + Rotation"


def _center_of_mass(atoms, indices):
    total_mass = 0.0
    acc = np.zeros(3)
    for i in indices:
        s, x, y, z = atoms[i]
        m = ATOMIC_WEIGHT.get(s, 1.0)
        total_mass += m
        acc += m * np.array([x, y, z])
    if total_mass > 0:
        return acc / total_mass
    return np.zeros(3)


def generate_scan(atoms, moving_indices, scan_type,
                  dx=0.0, dy=0.0, dz=0.0,
                  ax=0.0, ay=0.0, az=0.0,
                  steps=10):
    """
    Generate a list of geometry snapshots for a rigid scan.

    Parameters
    ----------
    atoms : list of (symbol, x, y, z)
        The starting geometry.
    moving_indices : set of int
        Indices of atoms that will be translated/rotated.
    scan_type : str
        One of SCAN_TRANSLATION, SCAN_ROTATION, SCAN_BOTH.
    dx, dy, dz : float
        Total translation in Angstrom (divided evenly over steps).
    ax, ay, az : float
        Total rotation in degrees (divided evenly over steps).
    steps : int
        Number of scan steps (produces steps+1 frames: initial + N steps).

    Returns
    -------
    list of list of (symbol, x, y, z)
        Each element is a complete geometry snapshot.
    """
    if steps < 1:
        steps = 1

    moving = set(moving_indices)
    frames = [list(atoms)]

    current = [list(a) for a in atoms]

    step_dx = dx / steps
    step_dy = dy / steps
    step_dz = dz / steps
    step_ax = ax / steps
    step_ay = ay / steps
    step_az = az / steps

    for _ in range(steps):
        if scan_type in (SCAN_TRANSLATION, SCAN_BOTH):
            for i in moving:
                s, x, y, z = current[i]
                current[i] = (s, x + step_dx, y + step_dy, z + step_dz)

        if scan_type in (SCAN_ROTATION, SCAN_BOTH):
            pivot = _center_of_mass(current, moving)
            mat = rotation_matrix(step_ax, step_ay, step_az)
            for i in moving:
                s, x, y, z = current[i]
                nx, ny, nz = apply_matrix(x, y, z, mat, pivot)
                current[i] = (s, nx, ny, nz)

        frames.append([tuple(a) for a in current])

    return frames


def frames_to_geometria_bruta(frame):
    """Convert a single frame [(sym, x, y, z), ...] to geometria_bruta string."""
    lines = []
    for sym, x, y, z in frame:
        lines.append(f"{sym}  {x: .10f}  {y: .10f}  {z: .10f}")
    return "\n".join(lines)
