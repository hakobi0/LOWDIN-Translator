"""
MolecularAssembly: hold several molecules (fragments) in one scene, position
them rigidly relative to each other, merge them into a single LOWDIN geometry,
and generate rigid-body scan trajectories.

A Fragment is a named collection of atoms and/or particles. A "molecule + e+"
scan is expressed as one fragment of atoms plus a second fragment that holds
only the positron particle; because translate/rotate act on atoms and particles
uniformly, the mobile entity of a scan can be a full molecule or a bare
particle with no special-casing.

This module is deliberately free of any GUI / rendering dependency so it can be
unit-tested headlessly.
"""

import numpy as np

from model.transforms import rotation_matrix, apply_matrix


class Fragment:
    def __init__(self, name, atoms=None, particles=None):
        self.name = str(name)
        self.atoms = [
            (str(s).capitalize(), float(x), float(y), float(z))
            for s, x, y, z in (atoms or [])
        ]
        self.particles = [
            (str(t), float(x), float(y), float(z))
            for t, x, y, z in (particles or [])
        ]

    def is_empty(self):
        return not self.atoms and not self.particles

    def center(self):
        """Geometric center over atoms and particles (unweighted)."""
        pts = [a[1:] for a in self.atoms] + [p[1:] for p in self.particles]
        if not pts:
            return (0.0, 0.0, 0.0)
        c = np.array(pts, dtype=float).mean(axis=0)
        return (float(c[0]), float(c[1]), float(c[2]))

    def translate(self, dx, dy, dz):
        dx, dy, dz = float(dx), float(dy), float(dz)
        self.atoms = [(s, x + dx, y + dy, z + dz) for (s, x, y, z) in self.atoms]
        self.particles = [(t, x + dx, y + dy, z + dz) for (t, x, y, z) in self.particles]

    def rotate(self, ax_deg, ay_deg, az_deg, about_center=True):
        matrix = rotation_matrix(ax_deg, ay_deg, az_deg)
        pivot = self.center() if about_center else (0.0, 0.0, 0.0)
        self.atoms = [(s, *apply_matrix(x, y, z, matrix, pivot)) for (s, x, y, z) in self.atoms]
        self.particles = [(t, *apply_matrix(x, y, z, matrix, pivot)) for (t, x, y, z) in self.particles]

    def copy(self):
        return Fragment(self.name, self.atoms, self.particles)


class MolecularAssembly:
    def __init__(self):
        self.fragments = []

    # ------------------------------------------------------------------ setup
    def add_fragment(self, name, atoms=None, particles=None):
        frag = Fragment(name, atoms, particles)
        self.fragments.append(frag)
        return frag

    def remove_fragment(self, index):
        return self.fragments.pop(index)

    def translate_fragment(self, index, dx, dy, dz):
        self.fragments[index].translate(dx, dy, dz)

    def rotate_fragment(self, index, ax_deg, ay_deg, az_deg, about_center=True):
        self.fragments[index].rotate(ax_deg, ay_deg, az_deg, about_center)

    # ----------------------------------------------------------------- merge
    def merged_atoms(self):
        atoms = []
        for frag in self.fragments:
            atoms.extend(frag.atoms)
        return atoms

    def merged_particles(self):
        particles = []
        for frag in self.fragments:
            particles.extend(frag.particles)
        return particles

    def merged_geometria_bruta(self):
        """Flat coordinate string consumed by formatear_geometria."""
        return "\n".join(
            f"{s} {x:.6f} {y:.6f} {z:.6f}" for s, x, y, z in self.merged_atoms()
        )

    # ------------------------------------------------------------------ scan
    def scan_frames(self, mobile_index, n_steps,
                    translation=(0.0, 0.0, 0.0), rotation=(0.0, 0.0, 0.0),
                    include_start=True):
        """
        Step the mobile fragment through the total `translation` (Angstrom) and
        `rotation` (degrees) over `n_steps`, returning a list of assembly
        snapshots (deep copies). With include_start the first frame is the
        untouched geometry, giving n_steps + 1 frames total.

        Rotation is applied about the mobile fragment's own moving center; for a
        pure translational scan (rotation zero) that is irrelevant.
        """
        if n_steps < 1:
            raise ValueError("n_steps must be >= 1")

        tx, ty, tz = (v / n_steps for v in translation)
        rx, ry, rz = (v / n_steps for v in rotation)

        work = self.copy()
        frames = [work.copy()] if include_start else []
        for _ in range(n_steps):
            work.translate_fragment(mobile_index, tx, ty, tz)
            if rx or ry or rz:
                work.rotate_fragment(mobile_index, rx, ry, rz)
            frames.append(work.copy())
        return frames

    def copy(self):
        new = MolecularAssembly()
        new.fragments = [frag.copy() for frag in self.fragments]
        return new
