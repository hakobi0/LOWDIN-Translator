from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QShortcut, QKeySequence
from PyQt6.QtWidgets import (
    QDialog, QInputDialog, QMessageBox, QProgressDialog, QMenu,
    QPushButton, QVBoxLayout, QFormLayout, QDoubleSpinBox, QDialogButtonBox,
    QLabel,
)
from UI.geomvisualizator import Ui_Form
from model.geometryeditor import GeometryEditor
from model.variablesglobales import ATOMIC_WEIGHT


ATOM_CHOICES = [
    "H", "He",
    "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar",
    "K", "Ca", "Ti", "Fe", "Cu", "Zn", "Br", "I",
]

PARTICLE_CHOICES = ["e-", "e+", "U-", "U+"]


class GeometryDialogStudy(QDialog):
    # Set by the main window before opening the dialog to match the active theme
    plotter_background = "#1e1e2e"

    def __init__(self, atoms, parent=None, particles=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Geometry Editor")
        self.resize(1100, 750)

        self.geometry_editor = GeometryEditor(atoms, particles=particles)
        self.pending_action = None
        self.pending_symbol = None

        self.plotter = self.ui.pyvista_widget
        self.plotter.enable_trackball_style()
        self.plotter.add_camera_orientation_widget()

        self.ui.infotextbox.setFont(QFont("Monospace", 9))
        self.ui.infotextbox.setReadOnly(True)
        self.ui.infotextbox.setLineWrapMode(self.ui.infotextbox.LineWrapMode.NoWrap)

        # Selection mode state
        self._selection_mode = False
        self._rb_start = None
        self._rb_active = False
        self._sel_observer_tags = []
        self._first_draw = True
        self._saved_style = None

        # Keyboard shortcuts
        self.plotter.add_key_event('s', self._toggle_selection_mode)
        self.plotter.add_key_event('a', self._start_add_mode)
        self.plotter.add_key_event('x', self._start_remove_mode)
        self.plotter.add_key_event('p', self._start_add_particle_mode)

        # Right-click context menu
        self.plotter.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.plotter.customContextMenuRequested.connect(self._show_context_menu)

        # Make selection button checkable
        self.ui.selectionbutton.setCheckable(True)
        self.ui.selectionbutton.setToolTip("Toggle selection mode (S)")
        self.ui.selectionbutton.clicked.connect(self._toggle_selection_mode)

        self.ui.addatombutton.setToolTip("Add atom at click position (A)")
        self.ui.addatombutton.clicked.connect(self._start_add_mode)
        self.ui.removeatoms.setToolTip("Remove selected atoms (X)")
        self.ui.removeatoms.clicked.connect(self._start_remove_mode)
        self.ui.rotatebutton.setToolTip("Rotate the whole geometry by X/Y/Z angles")
        self.ui.rotatebutton.clicked.connect(self._rotate_geometry)
        self.ui.optimizebutton.setToolTip("Optimize geometry with UFF/MMFF force field")
        self.ui.optimizebutton.clicked.connect(self._optimize_geometry)
        self.ui.ok_cancel_buttonBox.accepted.connect(self.accept)
        self.ui.ok_cancel_buttonBox.rejected.connect(self.reject)

        # Add Particle button
        self._add_particle_btn = QPushButton("Add Particle")
        self._add_particle_btn.setToolTip("Place e-/e+/U-/U+ particle (P)")
        layout = self.ui.verticalLayout_2
        layout.insertWidget(layout.indexOf(self.ui.removeatoms) + 1, self._add_particle_btn)
        self._add_particle_btn.clicked.connect(self._start_add_particle_mode)

        # Undo / Redo
        QShortcut(QKeySequence.StandardKey.Undo, self).activated.connect(self._undo)
        QShortcut(QKeySequence.StandardKey.Redo, self).activated.connect(self._redo)

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

    def _undo(self):
        if self.geometry_editor.undo():
            self._redraw()

    def _redo(self):
        if self.geometry_editor.redo():
            self._redraw()

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

        # Enter selection mode so the click is intercepted by the picker
        if not self._selection_mode:
            self._toggle_selection_mode()

        self._update_info(
            f"Add mode active.\nSelected atom: {atom}\nClick anywhere in the visualizer to place it."
        )

    def _start_remove_mode(self):
        if not self.geometry_editor.get_geometry() and not self.geometry_editor.particles:
            QMessageBox.information(self, "Nothing to remove", "There are no atoms or particles to remove.")
            return

        # If anything is already selected, remove it immediately
        has_selection = (self.geometry_editor.selected_indices or
                         self.geometry_editor.selected_particle_indices)
        if has_selection:
            self.geometry_editor.remove_selected()
            self._redraw()
            return

        # Otherwise enter selection mode and ask the user to click
        self.pending_action = "remove"
        self.pending_symbol = None
        if not self._selection_mode:
            self._toggle_selection_mode()
        self._update_info("Remove mode active.\nClick an atom/particle or rubber-band select, then click Remove again.")

    def _start_add_particle_mode(self):
        ptype, accepted = QInputDialog.getItem(
            self,
            "Select Particle",
            "Particle type:",
            PARTICLE_CHOICES,
            0,
            False,
        )
        if not accepted:
            return

        self.pending_action = "add_particle"
        self.pending_symbol = ptype

        if not self._selection_mode:
            self._toggle_selection_mode()

        self._update_info(
            f"Add particle mode active.\nSelected: {ptype}\nClick anywhere in the visualizer to place it."
        )


    def get_particles(self):
        return self.geometry_editor.get_particles()

    # -------------------------------------------------------- selection mode
    def _toggle_selection_mode(self):
        self._selection_mode = not self._selection_mode
        self.ui.selectionbutton.setChecked(self._selection_mode)
        iren = self.plotter.iren.interactor

        if self._selection_mode:
            self.plotter.setCursor(Qt.CursorShape.CrossCursor)
            self._update_info("Selection mode ON  (S to exit)\nLeft-drag to rubber-band select.\nShift keeps existing selection.")
            # Swap trackball out for a null style so it never rotates
            import vtk
            self._saved_style = iren.GetInteractorStyle()
            null_style = vtk.vtkInteractorStyleUser()
            iren.SetInteractorStyle(null_style)
            self._sel_observer_tags = [
                iren.AddObserver("LeftButtonPressEvent",   self._sel_press),
                iren.AddObserver("MouseMoveEvent",         self._sel_move),
                iren.AddObserver("LeftButtonReleaseEvent", self._sel_release),
            ]
        else:
            self.plotter.setCursor(Qt.CursorShape.ArrowCursor)
            for tag in self._sel_observer_tags:
                iren.RemoveObserver(tag)
            self._sel_observer_tags = []
            # Restore trackball
            iren.SetInteractorStyle(self._saved_style)
            self._saved_style = None
            self._rb_start = None
            self._rb_active = False
            self._redraw()

    def _sel_press(self, obj, event):
        self._rb_start = self.plotter.iren.interactor.GetEventPosition()
        self._rb_active = False
        # Do NOT forward — blocks trackball rotation while in selection mode

    def _sel_move(self, obj, event):
        if self._rb_start is None:
            return
        x, y = self.plotter.iren.interactor.GetEventPosition()
        dx = x - self._rb_start[0]
        dy = y - self._rb_start[1]
        if not self._rb_active and (abs(dx) > 4 or abs(dy) > 4):
            self._rb_active = True
        # Do NOT forward — suppress all camera movement in selection mode

    def _sel_release(self, obj, event):
        if self._rb_start is None:
            return
        iren = self.plotter.iren.interactor
        x, y = iren.GetEventPosition()

        # --- add mode: place atom/particle at clicked 3-D position then exit ---
        if self.pending_action in ("add", "add_particle") and not self._rb_active:
            # Try mesh pick first; fall back to focal-plane projection
            picker = iren.GetPicker()
            picker.Pick(x, y, 0, self.plotter.renderer)
            if picker.GetActor() is not None:
                pos = picker.GetPickPosition()
            else:
                # Project screen point onto the camera focal plane
                renderer = self.plotter.renderer
                renderer.SetDisplayPoint(x, y, 0)
                renderer.DisplayToWorld()
                near = renderer.GetWorldPoint()[:3]
                renderer.SetDisplayPoint(x, y, 1)
                renderer.DisplayToWorld()
                far = renderer.GetWorldPoint()[:3]
                # Intersect ray with the plane at focal point depth
                import numpy as _np
                cam = self.plotter.camera
                focal = _np.array(cam.focal_point)
                direction = _np.array(far) - _np.array(near)
                view_dir = _np.array(cam.position) - focal
                view_dir = view_dir / (_np.linalg.norm(view_dir) + 1e-12)
                denom = _np.dot(direction, -view_dir)
                if abs(denom) > 1e-12:
                    t = _np.dot(focal - _np.array(near), -view_dir) / denom
                    pos = tuple(_np.array(near) + t * direction)
                else:
                    pos = tuple(focal)
            if self.pending_action == "add":
                self.geometry_editor.add_atom(self.pending_symbol, *pos)
            else:
                self.geometry_editor.add_particle(self.pending_symbol, *pos)
            self.pending_action = None
            self.pending_symbol = None
            self._rb_start = None
            self._rb_active = False
            self._toggle_selection_mode()  # exit selection mode
            return

        # --- normal selection ---
        if not iren.GetShiftKey():
            self.geometry_editor.clear_selection()

        if self._rb_active:
            atoms_hit, particles_hit = self.geometry_editor.indices_in_screen_rect(
                self.plotter.renderer,
                self._rb_start[0], self._rb_start[1],
                x, y,
            )
            self.geometry_editor.select_indices(atoms_hit)
            self.geometry_editor.select_particle_indices(particles_hit)
        else:
            picker = iren.GetPicker()
            picker.Pick(x, y, 0, self.plotter.renderer)
            if picker.GetActor() is not None:
                pos = picker.GetPickPosition()
                obj_type, idx = self.geometry_editor.find_nearest(*pos)
                if obj_type == "atom":
                    self.geometry_editor.toggle_selection(idx)
                elif obj_type == "particle":
                    self.geometry_editor.toggle_particle_selection(idx)

        self._rb_start = None
        self._rb_active = False
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

        # Scale iterations with molecule size; floor 2000, cap 10000
        n_atoms = len(self.geometry_editor.get_geometry())
        max_iters = min(max(2000, n_atoms * 50), 10000)

        # Run optimization
        result = self.geometry_editor.optimize_geometry(
            charge=charge,
            method=method,
            max_iters=max_iters,
        )

        # If MMFF failed (no parameters for some elements), fall back to UFF
        if not result["success"] and method == "MMFF":
            mmff_msg = result["message"]
            result = self.geometry_editor.optimize_geometry(
                charge=charge,
                method="UFF",
                max_iters=max_iters,
            )
            if result["success"]:
                result["message"] = (
                    f"MMFF not available ({mmff_msg}), fell back to UFF.\n"
                    + result["message"]
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
        self.geometry_editor.render_in_plotter(
            self.plotter,
            reset_camera=self._first_draw,
            background=GeometryDialogStudy.plotter_background,
        )
        self._first_draw = False
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
        menu = QMenu(self)

        # Edit actions
        edit_menu = menu.addMenu("Edit")
        edit_menu.addAction("Undo (Ctrl+Z)").triggered.connect(self._undo)
        edit_menu.addAction("Redo (Ctrl+Y)").triggered.connect(self._redo)
        edit_menu.addSeparator()
        edit_menu.addAction("Add Atom (A)").triggered.connect(self._start_add_mode)
        edit_menu.addAction("Add Particle (P)").triggered.connect(self._start_add_particle_mode)
        edit_menu.addAction("Remove Selected (X)").triggered.connect(self._start_remove_mode)

        menu.addSeparator()

        # Transform actions
        menu.addAction("Center at Origin").triggered.connect(self._center_at_origin)
        menu.addAction("Standard Orientation (Principal Axes)").triggered.connect(self._set_standard_orientation)
        menu.addAction("Show Center of Mass").triggered.connect(self._show_center_of_mass)

        menu.addAction("Translate...").triggered.connect(self._translate_geometry)
        menu.addAction("Rotate...").triggered.connect(self._rotate_geometry)

        plane_menu = menu.addMenu("Align to Plane")
        plane_menu.addAction("XY Plane").triggered.connect(lambda: self._set_coordinates_to_plane("xy"))
        plane_menu.addAction("XZ Plane").triggered.connect(lambda: self._set_coordinates_to_plane("xz"))
        plane_menu.addAction("YZ Plane").triggered.connect(lambda: self._set_coordinates_to_plane("yz"))

        menu.addSeparator()

        menu.addAction("Rigid Scan...").triggered.connect(self._open_scan_from_editor)

        menu.addSeparator()

        # View actions
        menu.addAction("Show Z-Matrix").triggered.connect(self._show_zmatrix)
        menu.addAction("Reset Camera").triggered.connect(lambda: self.plotter.reset_camera())

        menu.exec(self.plotter.mapToGlobal(position))

    def _center_at_origin(self):
        if not self.geometry_editor.get_geometry():
            return
        self.geometry_editor.set_coordinates_to_center()
        self._redraw()

    def _set_standard_orientation(self):
        if not self.geometry_editor.get_geometry():
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return
        self.geometry_editor.set_standard_orientation()
        self._redraw()

    def _transform_scope_label(self):
        n_atoms = len(self.geometry_editor.selected_indices)
        n_particles = len(self.geometry_editor.selected_particle_indices)
        if not n_atoms and not n_particles:
            return "whole geometry"
        parts = []
        if n_atoms:
            parts.append(f"{n_atoms} atom{'s' if n_atoms != 1 else ''}")
        if n_particles:
            parts.append(f"{n_particles} particle{'s' if n_particles != 1 else ''}")
        return "selected " + " + ".join(parts)

    def _translate_geometry(self):
        if not self.geometry_editor.get_geometry() and not self.geometry_editor.particles:
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        scope = self._transform_scope_label()
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Translate ({scope})")
        form = QFormLayout(dialog)
        form.addRow(QLabel(f"Moving: {scope}"))

        spins = []
        for axis in ("X", "Y", "Z"):
            spin = QDoubleSpinBox(dialog)
            spin.setRange(-1000.0, 1000.0)
            spin.setDecimals(3)
            spin.setSingleStep(0.1)
            spin.setSuffix(" Å")
            form.addRow(f"Shift along {axis}:", spin)
            spins.append(spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        dx, dy, dz = (s.value() for s in spins)
        if dx == 0.0 and dy == 0.0 and dz == 0.0:
            return

        self.geometry_editor.translate(dx, dy, dz)
        self._redraw()

    def _rotate_geometry(self):
        if not self.geometry_editor.get_geometry() and not self.geometry_editor.particles:
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        scope = self._transform_scope_label()
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Rotate ({scope})")
        form = QFormLayout(dialog)
        form.addRow(QLabel(f"Rotating: {scope}"))

        spins = []
        for axis in ("X", "Y", "Z"):
            spin = QDoubleSpinBox(dialog)
            spin.setRange(-360.0, 360.0)
            spin.setDecimals(1)
            spin.setSingleStep(5.0)
            spin.setSuffix(" °")
            form.addRow(f"Rotation about {axis}:", spin)
            spins.append(spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel,
            parent=dialog,
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        form.addRow(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        ax, ay, az = (s.value() for s in spins)
        if ax == 0.0 and ay == 0.0 and az == 0.0:
            return

        self.geometry_editor.rotate(ax, ay, az)
        self._redraw()

    def _set_coordinates_to_plane(self, plane):
        if not self.geometry_editor.get_geometry():
            return
        self.geometry_editor.set_coordinates_to_plane(plane)
        self._redraw()

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

    def _open_scan_from_editor(self):
        atoms = self.geometry_editor.get_geometry()
        if not atoms:
            QMessageBox.information(self, "No atoms", "Load geometry first.")
            return

        main_win = self.parent()
        if main_win is None or not hasattr(main_win, 'last_conversion'):
            QMessageBox.information(
                self, "No conversion",
                "Run a conversion first so the scan knows which\n"
                "method, basis and parameters to use.")
            return
        if not main_win.last_conversion:
            QMessageBox.information(
                self, "No conversion",
                "Run a conversion first so the scan knows which\n"
                "method, basis and parameters to use.")
            return

        from view.scandialog import ScanDialog

        conv = dict(main_win.last_conversion)
        conv.setdefault("control_options", [])
        conv.setdefault("output_options", [])

        selected = set(self.geometry_editor.selected_indices)
        particles = self.geometry_editor.get_particles()

        scan_dialog = ScanDialog(
            atoms=atoms,
            conversion_state=conv,
            parent=self,
            particles=particles,
            selected_indices=selected if selected else None,
        )
        ScanDialog.plotter_background = GeometryDialogStudy.plotter_background
        scan_dialog.exec()
