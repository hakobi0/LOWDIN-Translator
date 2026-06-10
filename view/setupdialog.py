from PyQt6.QtWidgets import (
    QVBoxLayout,
    QPushButton, QLabel, QFileDialog, QDialog,
    QDialogButtonBox, QFormLayout, QLineEdit,  QGroupBox)
from pathlib import Path

class SetupDialog(QDialog):
    def __init__(self, config_file, bases, ejecutable, parent=None):
        super().__init__(parent)
        self.setWindowTitle("LOWDIN Translator — First Time Setup")
        self.setMinimumWidth(500)
        self.config_file = config_file
        self._build_ui(ejecutable, bases)
        self._apply_stylesheet()

    def _build_ui(self, ejecutable, bases):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        welcome = QLabel("Es la primera vez que usas LOWDIN Translator.")
        welcome.setObjectName("panelLabel")
        layout.addWidget(welcome)

        # Executable group
        exe_group = QGroupBox("openlowdin Executable")
        exe_form = QFormLayout(exe_group)

        self.exe_input = QLineEdit(ejecutable or "")
        self.exe_input.setPlaceholderText("Ruta de openlowdin executable...")
        exe_form.addRow("Path:", self.exe_input)

        if ejecutable:
            found_label = QLabel("✔ Encontrado automaticamente")
            found_label.setStyleSheet("color: #4EC9B0;")
        else:
            found_label = QLabel("✘ No encontrado — Ingrese la ruta manualmente")
            found_label.setStyleSheet("color: #F44747;")
        exe_form.addRow("", found_label)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_executable)
        exe_form.addRow("", browse_btn)
        layout.addWidget(exe_group)

        # Basis sets group
        basis_group = QGroupBox("Basis Sets Found")
        basis_layout = QVBoxLayout(basis_group)
        if bases:
            basis_label = QLabel(f"✔ Found {len(bases)} basis set(s) in ~/openLOWDIN/lib/basis")
            basis_label.setStyleSheet("color: #4EC9B0;")
        else:
            basis_label = QLabel("✘ No basis sets found at ~/openLOWDIN/lib/basis")
            basis_label.setStyleSheet("color: #F44747;")
        basis_layout.addWidget(basis_label)
        layout.addWidget(basis_group)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)

    def browse_executable(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Find openlowdin executable", str(Path.home()), "All Files (*)"
        )
        if path:
            self.exe_input.setText(path)

    def get_executable(self):
        return self.exe_input.text().strip()

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
            QLineEdit {
                background-color: #2D2D2D; border: 1px solid #3C3C3C;
                border-radius: 4px; padding: 4px 8px;
            }
            QLineEdit:focus { border-color: #007ACC; }
            QPushButton {
                background-color: #3C3C3C; color: #D4D4D4;
                border: 1px solid #555; border-radius: 4px; padding: 6px 16px;
            }
            QPushButton:hover { background-color: #4A4A4A; }
            QDialogButtonBox QPushButton {
                background-color: #0E639C; color: white;
                border-color: #1177BB; font-weight: bold; min-width: 70px;
            }
        """)
