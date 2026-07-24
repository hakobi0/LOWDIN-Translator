"""
Scan Dialog: configure and preview rigid PES scans, then generate LOWDIN inputs.

Lets the user pick a scan type (translate, rotate, or both), set parameters,
select the moving fragment directly in the 3D viewer, preview the scan
animated with a step slider, and export one .lowdin file per scan step.
"""

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QComboBox, QDoubleSpinBox, QSpinBox, QSlider, QPushButton,
    QLabel, QFileDialog, QMessageBox, QTextEdit, QDialogButtonBox,
    QWidget, QSizePolicy,
)

from pyvistaqt import QtInteractor

from model.scanmodel import (
    generate_scan, frames_to_geometria_bruta,
    SCAN_TRANSLATION, SCAN_ROTATION, SCAN_BOTH,
)
from model.geometryeditor import GeometryEditor
from model.formateargeometria_c import formatear_geometria
from model.inputvalidator import validation_summary, suggest_method


class ScanDialog(QDialog):

    plotter_background = "#1e1e2e"

    def __init__(self, atoms, conversion_state, parent=None,
                 particles=None, selected_indices=None):
        """
        Parameters
        ----------
        atoms : list of (symbol, x, y, z)
        conversion_state : dict with keys metodo, base, base_proton,
            base_positron, carga, mult, titulo, plus control_options and
            output_options lists.
        particles : list of (type, x, y, z) or None
        selected_indices : set of int or None
            Atom indices that form the "moving fragment". If None/empty, the
            user can select atoms interactively in the viewer.
        """
        super().__init__(parent)
        self.setWindowTitle("Rigid Scan")
        self.resize(1200, 750)

        self._atoms = list(atoms)
        self._particles = list(particles or [])
        self._conversion = dict(conversion_state)
        self._moving = set(selected_indices or [])

        self._frames = []
        self._current_step = 0
        self._anim_timer = QTimer(self)
        self._anim_timer.setInterval(200)
        self._anim_timer.timeout.connect(self._anim_tick)

        self._selection_mode = False
        self._sel_observer_tags = []
        self._saved_style = None
        self._rb_start = None
        self._rb_active = False

        self._build_ui()
        self._on_type_changed()

    def _build_ui(self):
        root = QHBoxLayout(self)

        # --- Left: PyVista viewer ---
        viewer_container = QWidget()
        viewer_layout = QVBoxLayout(viewer_container)
        viewer_layout.setContentsMargins(0, 0, 0, 0)

        self._plotter = QtInteractor(parent=viewer_container)
        self._plotter.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._plotter.enable_trackball_style()
        self._plotter.add_key_event('s', self._toggle_selection_mode)
        viewer_layout.addWidget(self._plotter)

        # Slider row
        slider_row = QHBoxLayout()
        self._step_label = QLabel("Step 0 / 0")
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(0)
        self._slider.valueChanged.connect(self._on_slider)
        self._play_btn = QPushButton("Play")
        self._play_btn.setCheckable(True)
        self._play_btn.setFixedWidth(60)
        self._play_btn.clicked.connect(self._toggle_play)
        slider_row.addWidget(self._step_label)
        slider_row.addWidget(self._slider, 1)
        slider_row.addWidget(self._play_btn)
        viewer_layout.addLayout(slider_row)

        root.addWidget(viewer_container, 1)

        # --- Right: controls panel ---
        panel = QWidget()
        panel.setFixedWidth(340)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(0, 0, 0, 0)

        # Selection controls
        sel_group = QGroupBox("Moving Fragment")
        sel_layout = QVBoxLayout(sel_group)

        self._sel_label = QLabel()
        self._sel_label.setWordWrap(True)
        sel_layout.addWidget(self._sel_label)

        sel_btn_row = QHBoxLayout()
        self._select_btn = QPushButton("Select Atoms")
        self._select_btn.setCheckable(True)
        self._select_btn.setToolTip("Toggle selection mode (S)")
        self._select_btn.clicked.connect(self._toggle_selection_mode)
        sel_btn_row.addWidget(self._select_btn)

        self._clear_sel_btn = QPushButton("Clear")
        self._clear_sel_btn.setToolTip("Clear selection (all atoms will move)")
        self._clear_sel_btn.clicked.connect(self._clear_selection)
        sel_btn_row.addWidget(self._clear_sel_btn)
        sel_layout.addLayout(sel_btn_row)

        panel_layout.addWidget(sel_group)
        self._update_sel_label()

        # System parameters (charge / multiplicity)
        sys_group = QGroupBox("System")
        sys_form = QFormLayout(sys_group)
        sys_form.addRow("Method:", QLabel(str(self._conversion.get("metodo", ""))))
        sys_form.addRow("Basis:", QLabel(str(self._conversion.get("base", ""))))

        self._charge_spin = QSpinBox()
        self._charge_spin.setRange(-10, 10)
        self._charge_spin.setValue(int(self._conversion.get("carga", 0)))
        self._charge_spin.valueChanged.connect(self._on_system_changed)
        sys_form.addRow("Charge:", self._charge_spin)

        self._mult_spin = QSpinBox()
        self._mult_spin.setRange(1, 10)
        self._mult_spin.setValue(int(self._conversion.get("mult", 1)))
        self._mult_spin.valueChanged.connect(self._on_system_changed)
        sys_form.addRow("Multiplicity:", self._mult_spin)

        self._valid_label = QLabel()
        self._valid_label.setWordWrap(True)
        sys_form.addRow(self._valid_label)
        panel_layout.addWidget(sys_group)
        self._on_system_changed()

        # Scan type
        type_group = QGroupBox("Scan Type")
        type_form = QFormLayout(type_group)
        self._type_combo = QComboBox()
        self._type_combo.addItems([SCAN_TRANSLATION, SCAN_ROTATION, SCAN_BOTH])
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        type_form.addRow("Type:", self._type_combo)

        self._steps_spin = QSpinBox()
        self._steps_spin.setRange(1, 500)
        self._steps_spin.setValue(10)
        type_form.addRow("Steps:", self._steps_spin)
        panel_layout.addWidget(type_group)

        # Translation parameters
        self._trans_group = QGroupBox("Translation (total)")
        trans_form = QFormLayout(self._trans_group)
        self._dx = self._make_spin(trans_form, "dX:")
        self._dy = self._make_spin(trans_form, "dY:")
        self._dz = self._make_spin(trans_form, "dZ:")
        panel_layout.addWidget(self._trans_group)

        # Rotation parameters
        self._rot_group = QGroupBox("Rotation (total, degrees)")
        rot_form = QFormLayout(self._rot_group)
        self._ax = self._make_spin(rot_form, "around X:", suffix="°",
                                   lo=-360, hi=360)
        self._ay = self._make_spin(rot_form, "around Y:", suffix="°",
                                   lo=-360, hi=360)
        self._az = self._make_spin(rot_form, "around Z:", suffix="°",
                                   lo=-360, hi=360)
        panel_layout.addWidget(self._rot_group)

        # Preview / Generate buttons
        self._preview_btn = QPushButton("Preview Scan")
        self._preview_btn.clicked.connect(self._generate_preview)
        panel_layout.addWidget(self._preview_btn)

        panel_layout.addSpacing(10)

        self._generate_btn = QPushButton("Generate Input Files...")
        self._generate_btn.setEnabled(False)
        self._generate_btn.clicked.connect(self._generate_files)
        panel_layout.addWidget(self._generate_btn)

        # Info box
        self._info = QTextEdit()
        self._info.setReadOnly(True)
        self._info.setFont(QFont("Monospace", 9))
        self._info.setMaximumHeight(180)
        panel_layout.addWidget(self._info, 1)

        # Close
        close_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close_box.rejected.connect(self.reject)
        panel_layout.addWidget(close_box)

        root.addWidget(panel)

        # Initial render
        self._editor = GeometryEditor(self._atoms, particles=self._particles)
        if self._moving:
            self._editor.select_indices(list(self._moving))
        self._render_current()

    # -------------------------------------------------------- helpers

    def _make_spin(self, form, label, suffix=" Å", lo=-1000, hi=1000):
        spin = QDoubleSpinBox()
        spin.setRange(lo, hi)
        spin.setDecimals(4)
        spin.setSingleStep(0.1)
        spin.setSuffix(suffix)
        form.addRow(label, spin)
        return spin

    def _on_type_changed(self):
        t = self._type_combo.currentText()
        self._trans_group.setVisible(t in (SCAN_TRANSLATION, SCAN_BOTH))
        self._rot_group.setVisible(t in (SCAN_ROTATION, SCAN_BOTH))

    def _update_sel_label(self):
        n_moving = len(self._moving)
        n_total = len(self._atoms)
        if n_moving == 0:
            self._sel_label.setText(
                f"No selection -- all {n_total} atoms move.\n"
                "Click 'Select Atoms' or press S to pick the moving fragment.")
        else:
            fixed = n_total - n_moving
            self._sel_label.setText(f"{n_moving} atoms move, {fixed} fixed")

    def _on_system_changed(self):
        charge = self._charge_spin.value()
        mult = self._mult_spin.value()
        self._conversion["carga"] = charge
        self._conversion["mult"] = mult
        msgs = validation_summary(
            self._atoms, charge, mult, self._conversion["metodo"])
        errors = [m for level, m in msgs if level == "error"]
        warnings = [m for level, m in msgs if level == "warning"]
        infos = [m for level, m in msgs if level == "info"]
        parts = []
        for e in errors:
            parts.append(f'<span style="color:#cc0000;">{e}</span>')
        for w in warnings:
            parts.append(f'<span style="color:#b36b00;">{w}</span>')
        for i in infos:
            parts.append(f'<span style="color:gray;">{i}</span>')
        self._valid_label.setText("<br>".join(parts))
        if hasattr(self, '_generate_btn'):
            self._generate_btn.setEnabled(bool(self._frames) and not errors)

    # -------------------------------------------------------- selection mode

    def _toggle_selection_mode(self):
        self._selection_mode = not self._selection_mode
        self._select_btn.setChecked(self._selection_mode)
        iren = self._plotter.iren.interactor

        if self._selection_mode:
            self._plotter.setCursor(Qt.CursorShape.CrossCursor)
            self._info.setPlainText(
                "Selection mode ON  (S to exit)\n"
                "Click to toggle an atom.\n"
                "Drag to rubber-band select.\n"
                "Hold Shift to extend selection.")
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
            self._plotter.setCursor(Qt.CursorShape.ArrowCursor)
            for tag in self._sel_observer_tags:
                iren.RemoveObserver(tag)
            self._sel_observer_tags = []
            if self._saved_style is not None:
                iren.SetInteractorStyle(self._saved_style)
                self._saved_style = None
            self._rb_start = None
            self._rb_active = False
            self._sync_selection_from_editor()
            self._render_current()

    def _sel_press(self, obj, event):
        self._rb_start = self._plotter.iren.interactor.GetEventPosition()
        self._rb_active = False

    def _sel_move(self, obj, event):
        if self._rb_start is None:
            return
        x, y = self._plotter.iren.interactor.GetEventPosition()
        dx = x - self._rb_start[0]
        dy = y - self._rb_start[1]
        if not self._rb_active and (abs(dx) > 4 or abs(dy) > 4):
            self._rb_active = True

    def _sel_release(self, obj, event):
        if self._rb_start is None:
            return
        iren = self._plotter.iren.interactor
        x, y = iren.GetEventPosition()

        if not iren.GetShiftKey():
            self._editor.clear_selection()

        if self._rb_active:
            atoms_hit, _ = self._editor.indices_in_screen_rect(
                self._plotter.renderer,
                self._rb_start[0], self._rb_start[1], x, y,
            )
            self._editor.select_indices(atoms_hit)
        else:
            picker = iren.GetPicker()
            picker.Pick(x, y, 0, self._plotter.renderer)
            if picker.GetActor() is not None:
                pos = picker.GetPickPosition()
                obj_type, idx = self._editor.find_nearest(*pos)
                if obj_type == "atom":
                    self._editor.toggle_selection(idx)

        self._rb_start = None
        self._rb_active = False
        self._sync_selection_from_editor()
        self._render_current()

    def _sync_selection_from_editor(self):
        self._moving = set(self._editor.selected_indices)
        self._update_sel_label()

    def _clear_selection(self):
        self._editor.clear_selection()
        self._moving.clear()
        self._update_sel_label()
        self._render_current()

    # -------------------------------------------------------- rendering

    def _render_current(self):
        if self._frames and 0 <= self._current_step < len(self._frames):
            frame = self._frames[self._current_step]
            editor = GeometryEditor(frame, particles=self._particles)
            if self._moving:
                editor.select_indices(list(self._moving))
            editor.render_in_plotter(
                self._plotter,
                reset_camera=False,
                background=self.plotter_background,
            )
        else:
            self._editor.render_in_plotter(
                self._plotter,
                reset_camera=(not self._frames),
                background=self.plotter_background,
            )

    def _render_frame(self, frame):
        editor = GeometryEditor(frame, particles=self._particles)
        if self._moving:
            editor.select_indices(list(self._moving))
        editor.render_in_plotter(
            self._plotter,
            reset_camera=(self._current_step == 0 and not self._frames),
            background=self.plotter_background,
        )

    # -------------------------------------------------------- scan preview

    def _generate_preview(self):
        if self._selection_mode:
            self._toggle_selection_mode()

        self._anim_timer.stop()
        self._play_btn.setChecked(False)

        moving = self._moving if self._moving else set(range(len(self._atoms)))

        self._frames = generate_scan(
            self._atoms, moving,
            scan_type=self._type_combo.currentText(),
            dx=self._dx.value(), dy=self._dy.value(), dz=self._dz.value(),
            ax=self._ax.value(), ay=self._ay.value(), az=self._az.value(),
            steps=self._steps_spin.value(),
        )

        self._slider.setMaximum(len(self._frames) - 1)
        self._slider.setValue(0)
        self._current_step = 0
        self._update_step_label()
        self._render_frame(self._frames[0])
        errors, _ = self._validate_input()
        self._generate_btn.setEnabled(not errors)
        self._info.setPlainText(
            f"Scan preview generated: {len(self._frames)} frames\n"
            f"Use the slider or Play to browse steps."
        )

    def _on_slider(self, value):
        if not self._frames:
            return
        self._current_step = value
        self._update_step_label()
        self._render_frame(self._frames[value])

    def _update_step_label(self):
        total = len(self._frames) - 1 if self._frames else 0
        self._step_label.setText(f"Step {self._current_step} / {total}")

    def _toggle_play(self):
        if self._play_btn.isChecked():
            if not self._frames:
                self._play_btn.setChecked(False)
                return
            self._anim_timer.start()
        else:
            self._anim_timer.stop()

    def _anim_tick(self):
        if not self._frames:
            self._anim_timer.stop()
            return
        nxt = self._current_step + 1
        if nxt >= len(self._frames):
            nxt = 0
        self._slider.setValue(nxt)

    # -------------------------------------------------------- file generation

    def _validate_input(self):
        msgs = validation_summary(
            self._atoms,
            self._charge_spin.value(),
            self._mult_spin.value(),
            self._conversion["metodo"])
        errors = [m for level, m in msgs if level == "error"]
        warnings = [m for level, m in msgs if level == "warning"]
        return errors, warnings

    def _generate_files(self):
        if not self._frames:
            QMessageBox.information(self, "No scan", "Preview a scan first.")
            return

        errors, warnings = self._validate_input()
        if errors:
            QMessageBox.critical(
                self, "Invalid input",
                "Cannot generate scan files:\n\n" + "\n".join(errors))
            return
        if warnings:
            ret = QMessageBox.warning(
                self, "Input warnings",
                "\n".join(warnings) + "\n\nGenerate files anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if ret != QMessageBox.StandardButton.Yes:
                return

        directory = QFileDialog.getExistingDirectory(
            self, "Select output directory for scan files")
        if not directory:
            return

        import os
        data = self._conversion
        base_name = data.get("titulo", "scan").replace(" ", "_")
        control_opts = data.get("control_options", [])
        output_opts = data.get("output_options", [])
        generated = []

        charge = self._charge_spin.value()
        mult = self._mult_spin.value()
        result = suggest_method(data["metodo"], self._atoms, charge, mult)
        metodo = result["corrected_method"]

        for i, frame in enumerate(self._frames):
            geom_bruta = frames_to_geometria_bruta(frame)
            fmt = formatear_geometria(
                geometria_bruta=geom_bruta,
                base_elec=data["base"],
                base_proton=data.get("base_proton", "dirac"),
                base_positron=data.get("base_positron", ""),
                multiplicidad=mult,
                carga=charge,
                metodo_real=metodo,
                titulo=f"{data.get('titulo', 'scan')} step {i}",
            )
            fmt.control_options = list(control_opts)
            fmt.output_options = list(output_opts)
            fmt.agregar_protones()
            fmt.agregar_electrones_desde_atomos()

            for ptype, x, y, z in self._particles:
                if ptype == "e-":
                    fmt.agregar_electrones("H", x, y, z)
                elif ptype in ("e+", "U-", "U+"):
                    fmt.agregar_positrones(x, y, z)

            fmt.formatear_geometria()
            content = fmt.crear_input_lowdin()

            filename = f"Scan_{i}_{base_name}.lowdin"
            filepath = os.path.join(directory, filename)
            with open(filepath, "w") as f:
                f.write(content)
            generated.append(filename)

        self._info.setPlainText(
            f"Generated {len(generated)} files in:\n{directory}\n\n"
            + "\n".join(generated)
        )
        QMessageBox.information(
            self, "Scan Files Generated",
            f"{len(generated)} LOWDIN input files written to:\n{directory}"
        )

    # -------------------------------------------------------- cleanup

    def reject(self):
        if self._selection_mode:
            self._toggle_selection_mode()
        self._anim_timer.stop()
        self._plotter.close()
        super().reject()

    def closeEvent(self, event):
        if self._selection_mode:
            self._toggle_selection_mode()
        self._anim_timer.stop()
        self._plotter.close()
        super().closeEvent(event)
