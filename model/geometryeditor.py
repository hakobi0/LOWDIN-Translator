import math
import numpy as np

import pyvista as pv

from model.variablesglobales import ATOMIC_WEIGHT

from model.geometryoptimizer import GeometryOptimizer


ELEMENT_COLORS = {
    "H": "white",
    "C": "gray",
    "N": "blue",
    "O": "red",
    "F": "green",
    "Cl": "green",
    "S": "yellow",
    "P": "orange",
    "B": "pink",
    "Si": "tan",
    "Br": "darkred",
    "I": "purple",
}

ELEMENT_RADII = {
    "H": 0.25,
    "C": 0.40,
    "N": 0.38,
    "O": 0.35,
    "F": 0.30,
    "Cl": 0.45,
    "S": 0.50,
    "P": 0.47,
    "B": 0.42,
    "Si": 0.55,
    "Br": 0.50,
    "I": 0.55,
}

BOND_THRESHOLD = 1.8


class GeometryEditor:
    def __init__(self, geometry=None):
        self.geometry = []
        self.selected_indices = set()
        self._selection_order = []   # tracks click order for angle/dihedral
        if geometry:
            self.set_geometry(geometry)

    def set_geometry(self, geometry):
        self.geometry = [
            (str(symbol).capitalize(), float(x), float(y), float(z))
            for symbol, x, y, z in geometry
        ]

    def get_geometry(self):
        return list(self.geometry)

    def add_atom(self, symbol, x, y, z):
        atom = (str(symbol).capitalize(), float(x), float(y), float(z))
        self.geometry.append(atom)
        print(self.geometry)
        return atom

    def remove_atom(self, index=-1):
        if not self.geometry:
            return None
        return self.geometry.pop(index)

    def remove_nearest_atom(self, x, y, z, max_distance=0.8):
        if not self.geometry:
            return None

        best_index = None
        best_distance = None
        picked = (float(x), float(y), float(z))

        for index, (_, atom_x, atom_y, atom_z) in enumerate(self.geometry):
            distance = math.dist(picked, (atom_x, atom_y, atom_z))
            if best_distance is None or distance < best_distance:
                best_index = index
                best_distance = distance

        if best_index is None or best_distance is None or best_distance > max_distance:
            return None

        return self.geometry.pop(best_index)

    def detect_bonds(self, threshold=BOND_THRESHOLD):
        bonds = []
        total = len(self.geometry)

        for i in range(total):
            _, x1, y1, z1 = self.geometry[i]
            for j in range(i + 1, total):
                _, x2, y2, z2 = self.geometry[j]
                distance = math.dist((x1, y1, z1), (x2, y2, z2))
                if 0.1 < distance <= threshold:
                    bonds.append((i, j))

        return bonds

    def to_geometria_bruta(self):
        return "\n".join(
            f"{symbol} {x:.6f} {y:.6f} {z:.6f}"
            for symbol, x, y, z in self.geometry
        )

    @staticmethod
    def _angle(p1, p2, p3):
        """Angle at p2 in degrees."""
        v1 = tuple(p1[k] - p2[k] for k in range(3))
        v2 = tuple(p3[k] - p2[k] for k in range(3))
        dot = sum(a * b for a, b in zip(v1, v2))
        n1 = math.sqrt(sum(a * a for a in v1))
        n2 = math.sqrt(sum(a * a for a in v2))
        if n1 < 1e-10 or n2 < 1e-10:
            return 0.0
        return math.degrees(math.acos(max(-1.0, min(1.0, dot / (n1 * n2)))))

    def summary_text(self):
        lines = [f"Atoms: {len(self.geometry)}", ""]
        for index, (symbol, x, y, z) in enumerate(self.geometry, start=1):
            marker = ">> " if (index - 1) in self.selected_indices else "   "
            lines.append(f"{marker}{index:02d}. {symbol}  {x:.6f}  {y:.6f}  {z:.6f}")

        # Use selection order so the user controls which atom is the vertex
        sel = self._selection_order

        if len(sel) == 2:
            i, j = sel
            p1 = self.geometry[i][1:]
            p2 = self.geometry[j][1:]
            dist = math.dist(p1, p2)
            s1, s2 = self.geometry[i][0], self.geometry[j][0]
            lines += [
                "",
                f"Distance  {s1}({i+1})-{s2}({j+1}): {dist:.4f} Å",
            ]

        elif len(sel) == 3:
            i, j, k = sel          # j is the vertex (selected second)
            p1 = self.geometry[i][1:]
            p2 = self.geometry[j][1:]
            p3 = self.geometry[k][1:]
            d_ij = math.dist(p1, p2)
            d_jk = math.dist(p2, p3)
            angle = self._angle(p1, p2, p3)
            s1, s2, s3 = self.geometry[i][0], self.geometry[j][0], self.geometry[k][0]
            lines += [
                "",
                f"Distance  {s1}({i+1})-{s2}({j+1}): {d_ij:.4f} Å",
                f"Distance  {s2}({j+1})-{s3}({k+1}): {d_jk:.4f} Å",
                f"Angle     {s1}({i+1})-{s2}({j+1})-{s3}({k+1}): {angle:.2f}°",
            ]

        elif len(sel) == 4:
            i, j, k, l = sel      # dihedral along j-k bond, i and l are the ends
            p1 = np.array(self.geometry[i][1:])
            p2 = np.array(self.geometry[j][1:])
            p3 = np.array(self.geometry[k][1:])
            p4 = np.array(self.geometry[l][1:])
            d_ij = math.dist(p1, p2)
            d_jk = math.dist(p2, p3)
            d_kl = math.dist(p3, p4)
            a_ijk = self._angle(p1, p2, p3)
            a_jkl = self._angle(p2, p3, p4)
            dihedral = self._calculate_dihedral(p1, p2, p3, p4)
            s1, s2 = self.geometry[i][0], self.geometry[j][0]
            s3, s4 = self.geometry[k][0], self.geometry[l][0]
            lines += [
                "",
                f"Distance  {s1}({i+1})-{s2}({j+1}): {d_ij:.4f} Å",
                f"Distance  {s2}({j+1})-{s3}({k+1}): {d_jk:.4f} Å",
                f"Distance  {s3}({k+1})-{s4}({l+1}): {d_kl:.4f} Å",
                f"Angle     {s1}({i+1})-{s2}({j+1})-{s3}({k+1}): {a_ijk:.2f}°",
                f"Angle     {s2}({j+1})-{s3}({k+1})-{s4}({l+1}): {a_jkl:.2f}°",
                f"Dihedral  {s1}({i+1})-{s2}({j+1})-{s3}({k+1})-{s4}({l+1}): {dihedral:.2f}°",
            ]

        return "\n".join(lines)

    def optimize_geometry(self, charge=0, method="UFF", max_iters=1000):
        """
        Optimize the current geometry using RDKit force fields.

        Args:
            charge: Molecular charge (default 0)
            method: "UFF" or "MMFF" (default "UFF")
            max_iters: Maximum optimization iterations

        Returns:
            dict with keys: 'success', 'message', 'energy'
        """
        if not self.geometry:
            return {
                "success": False,
                "message": "No atoms to optimize",
                "energy": None,
            }

        if len(self.geometry) < 2:
            return {
                "success": False,
                "message": "Need at least 2 atoms for optimization",
                "energy": None,
            }

        optimizer = GeometryOptimizer(self.geometry, charge=charge)
        optimized_atoms = optimizer.optimize(method=method, max_iters=max_iters)

        if optimized_atoms:
            self.set_geometry(optimized_atoms)
            energy = optimizer.get_energy()
            msg = f"Optimization successful using {method}"
            if optimizer.error_message:
                msg += f"\n\n{optimizer.error_message}"
            return {
                "success": True,
                "message": msg,
                "energy": energy,
            }
        else:
            return {
                "success": False,
                "message": optimizer.error_message or "Optimization failed",
                "energy": None,
            }

    def get_mass_center(self):
        molar_mass = 0
        x_sum = 0.0
        y_sum = 0.0
        z_sum = 0.0
        for (symbol, x, y, z) in self.geometry:
            atom_mass = ATOMIC_WEIGHT.get(symbol, 1.0)
            molar_mass += atom_mass
            x_sum += x*atom_mass
            y_sum += y*atom_mass
            z_sum += z*atom_mass

        x_center = x_sum/molar_mass
        y_center = y_sum/molar_mass
        z_center = z_sum/molar_mass

        return x_center, y_center, z_center

    def set_coordinates_to_center(self):
        """Now I want to set the center of the molecule to 0,0
              and the coordinates to the relative positions of this center of mass"""
        x_center, y_center, z_center = self.get_mass_center()
        relative_geometry = []

        for (symbol, x, y, z) in self.geometry:
            x_relative = x - x_center
            y_relative = y - y_center
            z_relative = z - z_center

            relative_atom = (symbol, x_relative, y_relative, z_relative)
            relative_geometry.append(relative_atom)
        self.geometry = relative_geometry
        return relative_geometry

    def set_coordinates_to_plane(self, plane):
        """
        Rotate geometry to align with specified plane using PCA.
        Does NOT flatten - preserves 3D structure with optimal orientation.

        Args:
            plane: "xy", "xz", or "yz" - target plane for alignment

        Returns:
            new_geometry list
        """
        if not self.geometry or len(self.geometry) < 3:
            # Not enough points for PCA, fall back to simple projection
            return self._simple_plane_projection(plane)

        # Extract coordinates as numpy array
        coords = np.array([[x, y, z] for _, x, y, z in self.geometry])

        # Center at origin
        centroid = coords.mean(axis=0)
        coords_centered = coords - centroid

        # Perform PCA to find principal axes
        covariance_matrix = np.cov(coords_centered.T)
        eigenvalues, eigenvectors = np.linalg.eig(covariance_matrix)

        # Sort by eigenvalues (largest first)
        idx = eigenvalues.argsort()[::-1]
        eigenvalues = eigenvalues[idx]
        eigenvectors = eigenvectors[:, idx]

        # Principal components (these form an orthonormal basis)
        pc1 = eigenvectors[:, 0]  # First principal component (max variance)
        pc2 = eigenvectors[:, 1]  # Second principal component
        pc3 = eigenvectors[:, 2]  # Third (smallest variance, "thin" direction)

        # Express each centered point in the PC basis
        # This gives us the coordinates in the PC coordinate system
        coords_in_pc_basis = coords_centered @ np.column_stack([pc1, pc2, pc3])

        # DON'T flatten - keep all 3 components
        # Just map the PC coordinates to the target coordinate system

        new_geometry = []

        for i, (symbol, _, _, _) in enumerate(self.geometry):
            pc1_coord = coords_in_pc_basis[i, 0]  # Component along PC1
            pc2_coord = coords_in_pc_basis[i, 1]  # Component along PC2
            pc3_coord = coords_in_pc_basis[i, 2]  # Component along PC3 (kept!)

            # Map to target coordinate system
            # PC1, PC2 (large variance) → in-plane axes
            # PC3 (small variance) → perpendicular axis
            if plane == "xy":
                # PC1 → X, PC2 → Y, PC3 → Z (thin in Z)
                new_geometry.append((symbol, pc1_coord, pc2_coord, pc3_coord))
            elif plane == "xz":
                # PC1 → X, PC2 → Z, PC3 → Y (thin in Y)
                new_geometry.append((symbol, pc1_coord, pc3_coord, pc2_coord))
            elif plane == "yz":
                # PC1 → Y, PC2 → Z, PC3 → X (thin in X)
                new_geometry.append((symbol, pc3_coord, pc1_coord, pc2_coord))

        self.geometry = new_geometry

        return new_geometry

    def _simple_plane_projection(self, plane):
        """Fallback for simple coordinate zeroing when PCA not applicable."""
        new_geometry = []

        for (symbol, x, y, z) in self.geometry:
            if plane == 'xy':
                new_geometry.append((symbol, x, y, 0.0))
            elif plane == 'xz':
                new_geometry.append((symbol, x, 0.0, z))
            elif plane == 'yz':
                new_geometry.append((symbol, 0.0, y, z))

        self.geometry = new_geometry
        return new_geometry

    def _get_camera_for_plane(self, plane):
        """Calculate camera position to view the specified plane."""
        # Get geometry bounds
        if not self.geometry:
            center = (0, 0, 0)
            distance = 10.0
        else:
            coords = np.array([[x, y, z] for _, x, y, z in self.geometry])
            center = coords.mean(axis=0)

            # Calculate appropriate distance based on molecule size
            extent = np.ptp(coords, axis=0).max()
            distance = extent * 2.5

        if plane == "xy":
            # Look down from +Z
            camera_position = (center[0], center[1], center[2] + distance)
            view_up = (0, 1, 0)
        elif plane == "xz":
            # Look from +Y
            camera_position = (center[0], center[1] + distance, center[2])
            view_up = (0, 0, 1)
        elif plane == "yz":
            # Look from +X
            camera_position = (center[0] + distance, center[1], center[2])
            view_up = (0, 1, 0)
        else:
            camera_position = (center[0], center[1], center[2] + distance)
            view_up = (0, 1, 0)

        return {
            'position': camera_position,
            'focal_point': tuple(center),
            'view_up': view_up
        }

    def calculate_zmatrix(self):
        """
        Calculate Z-matrix (internal coordinates) representation.

        Returns:
            str: Z-matrix in standard format
        """
        if not self.geometry:
            return "No atoms in geometry"

        if len(self.geometry) == 1:
            symbol = self.geometry[0][0]
            return f"{symbol}"

        coords = np.array([[x, y, z] for _, x, y, z in self.geometry])
        symbols = [symbol for symbol, _, _, _ in self.geometry]

        lines = []

        # First atom - just the symbol
        lines.append(f"{symbols[0]}")

        if len(self.geometry) >= 2:
            # Second atom - symbol and distance to first
            dist_1_2 = np.linalg.norm(coords[1] - coords[0])
            lines.append(f"{symbols[1]}  {1}  {dist_1_2:.6f}")

        if len(self.geometry) >= 3:
            # Third atom - symbol, distance, and angle
            dist_2_3 = np.linalg.norm(coords[2] - coords[1])

            # Calculate angle 1-2-3
            v1 = coords[0] - coords[1]
            v2 = coords[2] - coords[1]
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle_123 = np.degrees(np.arccos(cos_angle))

            lines.append(f"{symbols[2]}  {2}  {dist_2_3:.6f}  {1}  {angle_123:.4f}")

        # Fourth atom onwards - symbol, distance, angle, and dihedral
        for i in range(3, len(self.geometry)):
            symbol = symbols[i]

            # Distance to previous atom
            dist = np.linalg.norm(coords[i] - coords[i-1])

            # Angle with two atoms back
            v1 = coords[i-2] - coords[i-1]
            v2 = coords[i] - coords[i-1]
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.degrees(np.arccos(cos_angle))

            # Dihedral angle (torsion) with three atoms back
            dihedral = self._calculate_dihedral(
                coords[i-3], coords[i-2], coords[i-1], coords[i]
            )

            lines.append(
                f"{symbol}  {i}  {dist:.6f}  {i-1}  {angle:.4f}  {i-2}  {dihedral:.4f}"
            )

        return "\n".join(lines)

    def _calculate_dihedral(self, p1, p2, p3, p4):
        """
        Calculate dihedral angle between four points.

        Args:
            p1, p2, p3, p4: numpy arrays of 3D coordinates

        Returns:
            float: Dihedral angle in degrees
        """
        # Vectors between consecutive points
        b1 = p2 - p1
        b2 = p3 - p2
        b3 = p4 - p3

        # Normal vectors to the planes
        n1 = np.cross(b1, b2)
        n2 = np.cross(b2, b3)

        # Normalize
        n1_norm = np.linalg.norm(n1)
        n2_norm = np.linalg.norm(n2)

        if n1_norm < 1e-10 or n2_norm < 1e-10:
            # Atoms are collinear
            return 0.0

        n1 = n1 / n1_norm
        n2 = n2 / n2_norm

        # Calculate angle between normals
        cos_angle = np.dot(n1, n2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)

        # Determine sign using the scalar triple product
        m1 = np.cross(n1, b2 / np.linalg.norm(b2))
        sign = np.sign(np.dot(m1, n2))

        angle = np.degrees(np.arccos(cos_angle))

        return sign * angle

    def toggle_selection(self, index):
        if index in self.selected_indices:
            self.selected_indices.discard(index)
            self._selection_order = [i for i in self._selection_order if i != index]
        else:
            self.selected_indices.add(index)
            self._selection_order.append(index)

    def select_indices(self, indices):
        for idx in indices:
            if idx not in self.selected_indices:
                self.selected_indices.add(idx)
                self._selection_order.append(idx)

    def clear_selection(self):
        self.selected_indices.clear()
        self._selection_order.clear()

    def find_nearest_index(self, x, y, z):
        """Return the index of the atom nearest to (x, y, z), or None."""
        if not self.geometry:
            return None
        picked = (float(x), float(y), float(z))
        best_index = min(
            range(len(self.geometry)),
            key=lambda i: math.dist(picked, self.geometry[i][1:])
        )
        return best_index

    def indices_in_screen_rect(self, renderer, x1, y1, x2, y2):
        """Return atom indices whose projected screen coords fall inside the rectangle."""
        min_x, max_x = min(x1, x2), max(x1, x2)
        min_y, max_y = min(y1, y2), max(y1, y2)
        inside = []
        for idx, (_, ax, ay, az) in enumerate(self.geometry):
            renderer.SetWorldPoint(ax, ay, az, 1.0)
            renderer.WorldToDisplay()
            sx, sy, _ = renderer.GetDisplayPoint()
            if min_x <= sx <= max_x and min_y <= sy <= max_y:
                inside.append(idx)
        return inside

    def render_in_plotter(self, plotter, reset_camera=False, background="black"):
        camera = plotter.camera.copy()

        plotter.clear()
        plotter.show_grid()
        plotter.set_background(background)

        for atom_index, (symbol, x, y, z) in enumerate(self.geometry):
            sphere = pv.Sphere(
                center=(x, y, z),
                radius=ELEMENT_RADII.get(symbol, 0.35),
            )
            color = ELEMENT_COLORS.get(symbol, "lightgray")
            plotter.add_mesh(
                sphere,
                color=color,
                smooth_shading=True,
                name=f"atom-{atom_index}",
                pickable=True,
            )
            if atom_index in self.selected_indices:
                # Wireframe halo slightly larger than the atom sphere
                halo = pv.Sphere(
                    center=(x, y, z),
                    radius=ELEMENT_RADII.get(symbol, 0.35) * 1.35,
                )
                plotter.add_mesh(
                    halo,
                    color="yellow",
                    opacity=0.35,
                    name=f"sel-{atom_index}",
                    pickable=False,
                )

        for bond_index, (i, j) in enumerate(self.detect_bonds()):
            _, x1, y1, z1 = self.geometry[i]
            _, x2, y2, z2 = self.geometry[j]
            line = pv.Line((x1, y1, z1), (x2, y2, z2))
            plotter.add_mesh(
                line.tube(radius=0.06),
                color="darkgray",
                name=f"bond-{bond_index}",
                pickable=False,
            )

        if reset_camera and self.geometry:
            coords = np.array([[x, y, z] for _, x, y, z in self.geometry])
            centroid = coords.mean(axis=0)
            plotter.camera.focal_point = tuple(centroid)
            plotter.reset_camera()
        else:
            plotter.camera = camera
