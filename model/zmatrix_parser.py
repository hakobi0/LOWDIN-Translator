"""
Z-matrix parser and converter to Cartesian coordinates.
"""

import numpy as np
import re


class ZMatrixParser:
    """Parse Z-matrix files and convert to Cartesian coordinates."""

    def __init__(self, zmatrix_text):
        self.zmatrix_text = zmatrix_text
        self.atoms = []
        self.cartesian = []

    def parse(self):
        """
        Parse Z-matrix text and convert to Cartesian coordinates.

        Returns:
            list: Cartesian coordinates [(symbol, x, y, z), ...]
        """
        lines = self.zmatrix_text.strip().split('\n')

        # Filter out empty lines and comments
        lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

        if not lines:
            return []

        # Parse Z-matrix entries
        zmatrix_entries = []
        for line in lines:
            parts = line.split()
            if not parts:
                continue

            symbol = parts[0]

            if len(parts) == 1:
                # First atom (origin)
                zmatrix_entries.append({
                    'symbol': symbol,
                    'type': 'origin'
                })
            elif len(parts) == 3:
                # Second atom (distance only)
                zmatrix_entries.append({
                    'symbol': symbol,
                    'ref1': int(parts[1]) - 1,  # Convert to 0-based index
                    'distance': float(parts[2]),
                    'type': 'distance'
                })
            elif len(parts) == 5:
                # Third atom (distance + angle)
                zmatrix_entries.append({
                    'symbol': symbol,
                    'ref1': int(parts[1]) - 1,
                    'distance': float(parts[2]),
                    'ref2': int(parts[3]) - 1,
                    'angle': float(parts[4]),
                    'type': 'angle'
                })
            elif len(parts) >= 7:
                # Fourth+ atom (distance + angle + dihedral)
                zmatrix_entries.append({
                    'symbol': symbol,
                    'ref1': int(parts[1]) - 1,
                    'distance': float(parts[2]),
                    'ref2': int(parts[3]) - 1,
                    'angle': float(parts[4]),
                    'ref3': int(parts[5]) - 1,
                    'dihedral': float(parts[6]),
                    'type': 'dihedral'
                })

        # Convert to Cartesian
        self.cartesian = self._zmatrix_to_cartesian(zmatrix_entries)
        return self.cartesian

    def _zmatrix_to_cartesian(self, entries):
        """
        Convert Z-matrix entries to Cartesian coordinates.

        Args:
            entries: List of Z-matrix entry dictionaries

        Returns:
            list: [(symbol, x, y, z), ...]
        """
        coords = []

        for i, entry in enumerate(entries):
            symbol = entry['symbol']

            if entry['type'] == 'origin':
                # First atom at origin
                coords.append((symbol, 0.0, 0.0, 0.0))

            elif entry['type'] == 'distance':
                # Second atom along +Z axis
                ref1_idx = entry['ref1']
                distance = entry['distance']

                ref1_pos = np.array(coords[ref1_idx][1:])
                new_pos = ref1_pos + np.array([0, 0, distance])

                coords.append((symbol, new_pos[0], new_pos[1], new_pos[2]))

            elif entry['type'] == 'angle':
                # Third atom with bond angle
                ref1_idx = entry['ref1']
                ref2_idx = entry['ref2']
                distance = entry['distance']
                angle = np.radians(entry['angle'])

                ref1_pos = np.array(coords[ref1_idx][1:])
                ref2_pos = np.array(coords[ref2_idx][1:])

                # Vector from ref2 to ref1
                v21 = ref1_pos - ref2_pos
                v21_norm = v21 / np.linalg.norm(v21)

                # Place new atom at specified distance and angle from ref1
                # Angle is measured from ref2-ref1 bond
                # Place in XZ plane (arbitrary choice for 3rd atom)
                x = distance * np.sin(angle)
                z = distance * np.cos(angle)

                # Rotate to align with ref2-ref1 direction
                # For simplicity with 3rd atom, place in XZ plane
                new_pos = ref1_pos + np.array([x, 0, -z])

                coords.append((symbol, new_pos[0], new_pos[1], new_pos[2]))

            elif entry['type'] == 'dihedral':
                # Fourth+ atom with full positioning
                ref1_idx = entry['ref1']
                ref2_idx = entry['ref2']
                ref3_idx = entry['ref3']
                distance = entry['distance']
                angle = np.radians(entry['angle'])
                dihedral = np.radians(entry['dihedral'])

                p1 = np.array(coords[ref3_idx][1:])
                p2 = np.array(coords[ref2_idx][1:])
                p3 = np.array(coords[ref1_idx][1:])

                # Build coordinate system
                v1 = p2 - p1  # Bond p1->p2
                v2 = p3 - p2  # Bond p2->p3

                v1_norm = v1 / np.linalg.norm(v1)

                # Normal to plane
                n = np.cross(v1, v2)
                n_norm = n / np.linalg.norm(n)

                # Third axis perpendicular to both
                v_perp = np.cross(v1_norm, n_norm)

                # Position in local coordinate system
                x_local = distance * np.cos(angle)
                y_local = distance * np.sin(angle) * np.cos(dihedral)
                z_local = distance * np.sin(angle) * np.sin(dihedral)

                # Transform to global coordinates
                new_pos = p3 + x_local * (-v1_norm) + y_local * v_perp + z_local * n_norm

                coords.append((symbol, new_pos[0], new_pos[1], new_pos[2]))

        return coords


def is_zmatrix(text):
    """
    Detect if text is a Z-matrix format.

    Args:
        text: Input text

    Returns:
        bool: True if Z-matrix format detected
    """
    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip() and not l.startswith('#')]

    if len(lines) < 2:
        return False

    # Check first few lines match Z-matrix pattern
    try:
        # Line 1: just element symbol
        parts1 = lines[0].split()
        if len(parts1) != 1:
            return False
        if not parts1[0].isalpha():
            return False

        # Line 2: element + number + number (symbol ref distance)
        if len(lines) >= 2:
            parts2 = lines[1].split()
            if len(parts2) != 3:
                return False
            if not parts2[0].isalpha():
                return False
            int(parts2[1])  # Reference index
            float(parts2[2])  # Distance

        # Line 3: element + 4 numbers (if exists)
        if len(lines) >= 3:
            parts3 = lines[2].split()
            if len(parts3) >= 5:
                if not parts3[0].isalpha():
                    return False
                int(parts3[1])
                float(parts3[2])
                int(parts3[3])
                float(parts3[4])

        return True

    except (ValueError, IndexError):
        return False
