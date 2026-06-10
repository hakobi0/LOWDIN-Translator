from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QInputDialog, QMessageBox, QProgressDialog, QMenu, QVBoxLayout
from UI.geomvisualizator import Ui_Form
from model.geometryeditor_study import GeometryEditor
from model.variablesglobales import ATOMIC_WEIGHT


ATOM_CHOICES = [
    "H",
    "C",
    "N",
    "O",
    "F",
    "P",
    "S",
    "Cl",
    "Br",
    "I",
]


class GeometryDialogStudy(QDialog):
    def __init__(self, atoms, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Geometry Editor Study")

        self.geometry_editor = GeometryEditor(atoms)
        self.pending_action = None
        self.pending_symbol = None

        self.plotter = self.ui.pyvista_widget
        self.plotter.setCursor(Qt.CursorShape.CrossCursor) # Sets the cursor as cross
        self.plotter.enable_point_picking( # I dont know how this work but I need to change it
            callback=self._handle_point_picked,
            show_message=False,
            show_point=True,
            point_size=14,
            color="yellow",
            use_picker=False,
            left_clicking=True,
            pickable_window=True,
        )

        self.plotter.add_camera_orientation_widget()

        # Enable context menu on right-click
        self.plotter.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.plotter.customContextMenuRequested.connect(self._show_context_menu)

        self.ui.addatombutton.clicked.connect(self._start_add_mode)
        self.ui.removeatoms.clicked.connect(self._start_remove_mode)
        self.ui.optimizebutton.clicked.connect(self._optimize_geometry)
        self.ui.ok_cancel_buttonBox.accepted.connect(self.accept)
        self.ui.ok_cancel_buttonBox.rejected.connect(self.reject)

        self._redraw()

    def accept(self):
        self.plotter.close()
        super().accept()

    def reject(self):
        self.plotter.close()
        super().reject()

    def closeEvent(self, event):
        self.plotter.close()
        super().closeEvent(event)

    def _start_add_mode(self):
        atom, accepted = QInputDialog.getItem(
            self,
            "Select Atom",
            "Atom:",
            ATOM_CHOICES,
            0,
            False,
        )
        if not accepted:
            return

        self.pending_action = "add"
        self.pending_symbol = atom
        self._update_info(
            f"Add mode active.\nSelected atom: {atom}\nClick in the visualizer to place the atom."
        )

    def _start_remove_mode(self):
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "There are no atoms to remove.")
            return

        self.pending_action = "remove"
        self.pending_symbol = None
        self._update_info("Remove mode active.\nClick near an atom to delete it.")

    def _handle_point_picked(self, point):
        if point is None or not self.pending_action:
            return

        x, y, z = point

        if self.pending_action == "add":
            self.geometry_editor.add_atom(self.pending_symbol, x, y, z)
            self.pending_action = None
            self.pending_symbol = None
            self._redraw()
            return

        if self.pending_action == "remove":
            removed = self.geometry_editor.remove_nearest_atom(x, y, z)
            if removed is None:
                QMessageBox.information(
                    self,
                    "No atom selected",
                    "Click closer to an existing atom to remove it.",
                )
            self.pending_action = None
            self._redraw()

    def _optimize_geometry(self):
        """Run RDKit optimization on current geometry."""
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        # Ask for charge
        charge, accepted = QInputDialog.getInt(
            self,
            "Molecular Charge",
            "Enter molecular charge:",
            0,
            -10,
            10,
            1,
        )
        if not accepted:
            return

        # Ask for method
        method, accepted = QInputDialog.getItem(
            self,
            "Optimization Method",
            "Force field:",
            ["UFF", "MMFF"],
            0,
            False,
        )
        if not accepted:
            return

        # Show progress dialog
        progress = QProgressDialog(
            f"Optimizing geometry with {method}...",
            None,
            0,
            0,
            self,
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setCancelButton(None)
        progress.show()

        # Run optimization
        result = self.geometry_editor.optimize_geometry(
            charge=charge,
            method=method,
            max_iters=200,
        )

        progress.close()

        # Show results
        if result["success"]:
            energy_str = f"\nEnergy: {result['energy']:.4f} kcal/mol" if result["energy"] else ""
            QMessageBox.information(
                self,
                "Success",
                f"{result['message']}{energy_str}",
            )
            self._redraw()
        else:
            QMessageBox.warning(
                self,
                "Optimization Failed",
                result["message"],
            )

    def get_atoms(self):
        return self.geometry_editor.get_geometry()

    def _redraw(self):
        self.geometry_editor.render_in_plotter(self.plotter)
        self.get_atoms()
        self._update_info()

    def _update_info(self, prefix=None):
        text = self.geometry_editor.summary_text()
        if prefix:
            text = f"{prefix}\n\n{text}"
        self.ui.infotextbox.setPlainText(text)

    def get_geometria_bruta(self):
        return self.geometry_editor.to_geometria_bruta()

    def _show_context_menu(self, position):
        """Show context menu on right-click in the plotter."""
        menu = QMenu(self)

        # Center to Origin action
        center_action = menu.addAction("Center at Origin")
        center_action.triggered.connect(self._center_at_origin)

        # Show center of mass action
        show_com_action = menu.addAction("Show Center of Mass")
        show_com_action.triggered.connect(self._show_center_of_mass)

        # Show Z-matrix action
        show_zmatrix_action = menu.addAction("Show Z-Matrix")
        show_zmatrix_action.triggered.connect(self._show_zmatrix)

        menu.addSeparator()

        # Coordinates to Plane
        plane_action_xy = menu.addAction("Coordinates to the XY Plane")
        plane_action_xy.triggered.connect(
            lambda: self._set_coordinates_to_plane("xy")
        )

        plane_action_xz = menu.addAction("Coordinates to the XZ Plane")
        plane_action_xz.triggered.connect(
            lambda: self._set_coordinates_to_plane("xz")
        )

        plane_action_yz = menu.addAction("Coordinates to the YZ Plane")
        plane_action_yz.triggered.connect(
            lambda: self._set_coordinates_to_plane("yz")
        )

        menu.addSeparator()

        # Reset camera action
        reset_camera_action = menu.addAction("Reset Camera")
        reset_camera_action.triggered.connect(lambda: self.plotter.reset_camera())

        # Show menu at cursor position
        menu.exec(self.plotter.mapToGlobal(position))

    def _center_at_origin(self):
        """Center the molecule at (0, 0, 0)."""
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        self.geometry_editor.set_coordinates_to_center()
        self._redraw()
        QMessageBox.information(self, "Success", "Molecule centered at origin.")

    def _set_coordinates_to_plane(self, plane):
        """Rotate geometry to align with plane using PCA."""
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        # Rotate geometry (no camera change)
        self.geometry_editor.set_coordinates_to_plane(plane)

        # Redraw geometry
        self._redraw()

        QMessageBox.information(self, "Success", f"Aligned to {plane.upper()} plane.")

    def _show_center_of_mass(self):
        """Display the current center of mass coordinates."""
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        x_com, y_com, z_com = self.geometry_editor.get_mass_center()
        QMessageBox.information(
            self,
            "Center of Mass",
            f"Center of Mass:\n\nX: {x_com:.6f} Å\nY: {y_com:.6f} Å\nZ: {z_com:.6f} Å"
        )

    def _show_zmatrix(self):
        """Display the Z-matrix (internal coordinates) of the molecule."""
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        zmatrix = self.geometry_editor.calculate_zmatrix()

        # Create a dialog with monospace font for better formatting
        dialog = QDialog(self)
        dialog.setWindowTitle("Z-Matrix (Internal Coordinates)")
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        # Add text display
        from PyQt6.QtWidgets import QTextEdit
        from PyQt6.QtGui import QFont

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(zmatrix)

        # Set monospace font
        font = QFont("Courier New", 10)
        text_edit.setFont(font)

        layout.addWidget(text_edit)

        # Add close button
        from PyQt6.QtWidgets import QPushButton
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec()
