from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QDialog,
    QDialogButtonBox, QFormLayout, QSpinBox,
    QComboBox, QGroupBox,
    QScrollArea, QCheckBox
)
from model import variablesglobales
from view import particlerow

class ConversionDialog(QDialog):
    def __init__(self, metodo, base, carga, mult, atomos, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Conversion Options")
        self.setMinimumWidth(750)
        self.setMinimumHeight(600)
        self.atomos = atomos
        self._build_ui(metodo, base, carga, mult)
        self._apply_stylesheet()

    def _build_ui(self, metodo, base, carga, mult):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        bases = self.parent().bases_disponibles if self.parent() else []

        # ── Molecule ──────────────────────────────────────────────
        mol_group = QGroupBox("Molecule")
        mol_form = QFormLayout(mol_group)

        self.mult_input = QSpinBox()
        self.mult_input.setRange(1, 10)
        self.mult_input.setValue(mult)
        mol_form.addRow("Multiplicity:", self.mult_input)

        self.charge_input = QSpinBox()
        self.charge_input.setRange(-10, 10)
        self.charge_input.setValue(carga)
        mol_form.addRow("Charge (addParticles):", self.charge_input)

        layout.addWidget(mol_group)

        # ── Basis sets ────────────────────────────────────────────
        basis_group = QGroupBox("Basis Sets")
        basis_form = QFormLayout(basis_group)

        self.basis_elec_input = QComboBox()
        self.basis_elec_input.setEditable(True)
        self.basis_elec_input.addItems(bases)
        self.basis_elec_input.setCurrentText(base)
        basis_form.addRow("Electronic Basis:", self.basis_elec_input)

        self.basis_positron_input = QComboBox()
        self.basis_positron_input.setEditable(True)
        self.basis_positron_input.addItems(bases)
        self.basis_positron_input.setCurrentText(base)
        basis_form.addRow("Positronic Basis:", self.basis_positron_input)

        self.basis_proton_input = QComboBox()
        self.basis_proton_input.setEditable(True)
        self.basis_proton_input.addItems(bases)
        self.basis_proton_input.setCurrentText(base)
        basis_form.addRow("Protonic Basis:", self.basis_proton_input)

        layout.addWidget(basis_group)

        # ── Task ──────────────────────────────────────────────────
        task_group = QGroupBox("Task")
        task_form = QFormLayout(task_group)

        self.method_input = QComboBox()
        self.method_input.setEditable(True)
        self.method_input.addItems(["RHF", "UHF", "MP2", "B3LYP"])
        index = self.method_input.findText(metodo)
        if index >= 0:
            self.method_input.setCurrentIndex(index)
        else:
            self.method_input.setCurrentText(metodo)
        task_form.addRow("Method:", self.method_input)

        layout.addWidget(task_group)

        # ── Electrons ─────────────────────────────────────────────
        elec_group = QGroupBox("Electrons  (by default none are added)")
        elec_layout = QVBoxLayout(elec_group)

        self.elec_scroll = QScrollArea()
        self.elec_scroll.setWidgetResizable(True)
        self.elec_scroll.setMinimumHeight(100)
        self.elec_scroll.setMaximumHeight(160)
        self.elec_container = QWidget()
        self.elec_rows_layout = QVBoxLayout(self.elec_container)
        self.elec_rows_layout.setSpacing(2)
        self.elec_rows_layout.addStretch()
        self.elec_scroll.setWidget(self.elec_container)
        elec_layout.addWidget(self.elec_scroll)

        self.elec_rows = []

        elec_btn_row = QHBoxLayout()
        btn_add_elec = QPushButton("＋ Add Electron Entry")
        btn_add_elec.clicked.connect(self.add_electron_row)
        btn_rem_elec = QPushButton("－ Remove Last")
        btn_rem_elec.clicked.connect(self.remove_electron_row)
        elec_btn_row.addWidget(btn_add_elec)
        elec_btn_row.addWidget(btn_rem_elec)
        elec_btn_row.addStretch()
        elec_layout.addLayout(elec_btn_row)

        layout.addWidget(elec_group)

        # ── Positrons ─────────────────────────────────────────────
        pos_group = QGroupBox("Positrons  (by default none are added)")
        pos_layout = QVBoxLayout(pos_group)

        self.pos_scroll = QScrollArea()
        self.pos_scroll.setWidgetResizable(True)
        self.pos_scroll.setMinimumHeight(100)
        self.pos_scroll.setMaximumHeight(160)
        self.pos_container = QWidget()
        self.pos_rows_layout = QVBoxLayout(self.pos_container)
        self.pos_rows_layout.setSpacing(2)
        self.pos_rows_layout.addStretch()
        self.pos_scroll.setWidget(self.pos_container)
        pos_layout.addWidget(self.pos_scroll)

        self.pos_rows = []

        pos_btn_row = QHBoxLayout()
        btn_add_pos = QPushButton("＋ Add Positron Entry")
        btn_add_pos.clicked.connect(self.add_positron_row)
        btn_rem_pos = QPushButton("－ Remove Last")
        btn_rem_pos.clicked.connect(self.remove_positron_row)
        pos_btn_row.addWidget(btn_add_pos)
        pos_btn_row.addWidget(btn_rem_pos)
        pos_btn_row.addStretch()
        pos_layout.addLayout(pos_btn_row)

        layout.addWidget(pos_group)

        # ── Control ───────────────────────────────────────────────
        # Stored as self so on_method_changed can show/hide it
        self.control_group = QGroupBox("Control")
        self.control_layout = QVBoxLayout(self.control_group)

        # Scrollable area so a long task list doesn't explode the dialog
        self.control_scroll = QScrollArea()
        self.control_scroll.setWidgetResizable(True)
        self.control_scroll.setMinimumHeight(80)
        self.control_scroll.setMaximumHeight(180)
        self.control_container = QWidget()
        self.control_checkboxes_layout = QVBoxLayout(self.control_container)
        self.control_checkboxes_layout.setSpacing(3)
        self.control_scroll.setWidget(self.control_container)
        self.control_layout.addWidget(self.control_scroll)

        # This dict maps checkbox label → QCheckBox widget
        # so get_values() can read them all by name
        self.control_checkboxes = {}

        layout.addWidget(self.control_group)

        # ── OK / Cancel ───────────────────────────────────────────
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        # Connect method change and set initial state
        self.method_input.currentTextChanged.connect(self.on_method_changed)
        self.on_method_changed(self.method_input.currentText())

 # ── Method change handler ─────────────────────────────────────

    def on_method_changed(self, metodo):
        """
        Rebuilds the Control checkboxes based on the selected method.
        To add a new method: add its task list to variablesglobales.py
        and add an elif here pointing to that list.
        """
        metodo = metodo.upper()

        # Determine which task list to show for the current method
        if metodo in ("RHF", "UHF"):
            tareas = variablesglobales.tareas_HF + variablesglobales.tareas_SCF
        elif metodo == "MP2":
            # MP2 uses the same HF/SCF options as a base
            tareas = variablesglobales.tareas_HF + variablesglobales.tareas_SCF
        else:
            # For methods with no specific task list yet, show nothing
            tareas = []

        # Show or hide the whole Control group depending on whether
        # there are any options to show
        self.control_group.setVisible(len(tareas) > 0)

        # Clear previous checkboxes
        self.control_checkboxes.clear()
        while self.control_checkboxes_layout.count():
            item = self.control_checkboxes_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Build new checkboxes for the current method's task list
        for tarea in tareas:
            cb = QCheckBox(tarea)
            self.control_checkboxes[tarea] = cb
            self.control_checkboxes_layout.addWidget(cb)

    # ── Electron / positron row management ───────────────────────

    def add_electron_row(self):
        row = particlerow.ParticleRow(self.atomos)
        self.elec_rows.append(row)
        self.elec_rows_layout.insertWidget(self.elec_rows_layout.count() - 1, row)

    def remove_electron_row(self):
        if self.elec_rows:
            row = self.elec_rows.pop()
            self.elec_rows_layout.removeWidget(row)
            row.deleteLater()

    def add_positron_row(self):
        row = particlerow.ParticleRow(self.atomos)
        self.pos_rows.append(row)
        self.pos_rows_layout.insertWidget(self.pos_rows_layout.count() - 1, row)

    def remove_positron_row(self):
        if self.pos_rows:
            row = self.pos_rows.pop()
            self.pos_rows_layout.removeWidget(row)
            row.deleteLater()

    # ── Read values ───────────────────────────────────────────────

    def get_values(self):
        """Returns all dialog values including checked control options."""
        return {
            "carga":               self.charge_input.value(),
            "multiplicidad":       self.mult_input.value(),
            "base_elec":           self.basis_elec_input.currentText().strip().upper(),
            "base_positron":       self.basis_positron_input.currentText().strip().upper(),
            "base_proton":         self.basis_proton_input.currentText().strip().upper(),
            "metodo":              self.method_input.currentText().strip().upper(),
            "entradas_electrones": [r.get_values() for r in self.elec_rows],
            "entradas_positrones": [r.get_values() for r in self.pos_rows],
            # Returns a list of the task names that were checked
            "control_opciones":    [
                nombre for nombre, cb in self.control_checkboxes.items()
                if cb.isChecked()
            ],
        }

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1E1E1E; color: #D4D4D4;
                font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px;
            }
            QGroupBox {
                border: 1px solid #3C3C3C; border-radius: 6px;
                margin-top: 8px; padding: 8px; font-weight: bold; color: #9CDCFE;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QLineEdit, QSpinBox, QComboBox, QDoubleSpinBox {
                background-color: #2D2D2D; border: 1px solid #3C3C3C;
                border-radius: 4px; padding: 4px 6px; color: #D4D4D4;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QDoubleSpinBox:focus {
                border-color: #007ACC;
            }
            QDoubleSpinBox:disabled, QSpinBox:disabled { color: #555; }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2D2D2D; selection-background-color: #094771;
            }
            QCheckBox { color: #D4D4D4; padding: 2px 0; }
            QCheckBox::indicator {
                width: 14px; height: 14px;
                border: 1px solid #555; border-radius: 3px; background: #2D2D2D;
            }
            QCheckBox::indicator:checked { background: #007ACC; border-color: #007ACC; }
            QScrollArea { border: 1px solid #3C3C3C; border-radius: 4px; }
            QPushButton {
                background-color: #3C3C3C; color: #D4D4D4;
                border: 1px solid #555; border-radius: 4px; padding: 5px 12px;
            }
            QPushButton:hover { background-color: #4A4A4A; }
            QDialogButtonBox QPushButton {
                background-color: #3C3C3C; color: #D4D4D4;
                border: 1px solid #555; border-radius: 4px;
                padding: 6px 16px; min-width: 70px;
            }
            QDialogButtonBox QPushButton:hover { background-color: #4A4A4A; }
        """)
