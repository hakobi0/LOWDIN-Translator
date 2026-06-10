from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout,
    QSpinBox,
    QComboBox, QLabel, QDoubleSpinBox
)

class ParticleRow(QWidget):
    """
    A single row representing one particle entry (electron or positron).
    The user picks either an existing atom (which fills x/y/z automatically)
    or enters coordinates manually.
    """
    def __init__(self, atomos, parent=None):
        super().__init__(parent)
        self.atomos = atomos  # list of (simbolo, x, y, z)
        self._build_ui()

    def _build_ui(self):
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 2, 0, 2)
        row.setSpacing(6)

        # Number of particles
        self.n_input = QSpinBox()
        self.n_input.setRange(1, 50)
        self.n_input.setValue(1)
        self.n_input.setFixedWidth(55)
        row.addWidget(QLabel("n:"))
        row.addWidget(self.n_input)

        # Atom selector — first option is "Manual"
        self.atom_combo = QComboBox()
        self.atom_combo.setFixedWidth(120)
        self.atom_combo.addItem("Manual")
        for i, (simbolo, x, y, z) in enumerate(self.atomos):
            self.atom_combo.addItem(f"{i+1}. {simbolo}  ({x:.3f}, {y:.3f}, {z:.3f})")
        self.atom_combo.currentIndexChanged.connect(self._on_atom_selected)
        row.addWidget(self.atom_combo)

        # x y z inputs
        self.x_input = QDoubleSpinBox()
        self.y_input = QDoubleSpinBox()
        self.z_input = QDoubleSpinBox()
        for spin in (self.x_input, self.y_input, self.z_input):
            spin.setRange(-999.0, 999.0)
            spin.setDecimals(6)
            spin.setValue(0.0)
            spin.setFixedWidth(100)

        row.addWidget(QLabel("x:"))
        row.addWidget(self.x_input)
        row.addWidget(QLabel("y:"))
        row.addWidget(self.y_input)
        row.addWidget(QLabel("z:"))
        row.addWidget(self.z_input)

        row.addStretch()

    def _on_atom_selected(self, index):
        """When an atom is picked from the combo, fill x/y/z automatically."""
        if index == 0:
            # Manual — enable editing
            for spin in (self.x_input, self.y_input, self.z_input):
                spin.setEnabled(True)
        else:
            # Atom selected — fill and lock coordinates
            simbolo, x, y, z = self.atomos[index - 1]
            self.x_input.setValue(x)
            self.y_input.setValue(y)
            self.z_input.setValue(z)
            for spin in (self.x_input, self.y_input, self.z_input):
                spin.setEnabled(False)

    def get_values(self):
        """Returns a dict with n, x, y, z and the atom symbol if one was selected."""
        atom_index = self.atom_combo.currentIndex()
        simbolo = self.atomos[atom_index - 1][0] if atom_index > 0 else "e-"
        return {
            "n":       self.n_input.value(),
            "x":       self.x_input.value(),
            "y":       self.y_input.value(),
            "z":       self.z_input.value(),
            "simbolo": simbolo,
        }

