import sys
import os
import subprocess

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QFileDialog, QDialog, QMessageBox, QWidget, QHBoxLayout, QComboBox, QDoubleSpinBox
)

from model import primerinicio, parserclass, variablesglobales
from model.formateargeometria_c import formatear_geometria

from UI.mainwindow_test import Ui_MainWindow
from UI.conversiondialog_test import Ui_Dialog
from UI.addElectrons import Ui_addParticlesDialog
from UI.geomvisualizator2 import GeometryVisualizator


class AddParticlesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_addParticlesDialog()
        self.ui.setupUi(self)

        self.rows = []

        # Conexiones
        self.ui.addbutton.clicked.connect(self.add_row)
        self.ui.removebutton.clicked.connect(self.remove_row)

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Añadir una fila inicial
        self.add_row()

    # ---------------------------------------------------------
    # Crear una fila (una partícula)
    # ---------------------------------------------------------
    def add_row(self):
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)

        tipo = QComboBox()
        tipo.addItems(["e-", "e+", "U-", "U+", ])

        x = QDoubleSpinBox()
        y = QDoubleSpinBox()
        z = QDoubleSpinBox()

        for spin in (x, y, z):
            spin.setRange(-999.0, 999.0)
            spin.setDecimals(6)
            spin.setSingleStep(0.1)

        layout.addWidget(tipo)
        layout.addWidget(x)
        layout.addWidget(y)
        layout.addWidget(z)

        # Añadir al layout del scroll
        self.ui.verticalLayout_2.addWidget(row_widget)

        # Guardar referencia
        self.rows.append((row_widget, tipo, x, y, z))

    # ---------------------------------------------------------
    # Eliminar última fila
    # ---------------------------------------------------------
    def remove_row(self):
        if not self.rows:
            return

        row_widget, *_ = self.rows.pop()
        row_widget.setParent(None)
        row_widget.deleteLater()

    # ---------------------------------------------------------
    # Obtener datos del diálogo
    # ---------------------------------------------------------
    def get_particles(self):
        electrons = []
        positrons = []

        for _, tipo, x, y, z in self.rows:
            coords = (x.value(), y.value(), z.value())

            if tipo.currentText() == "e-":
                electrons.append(coords)
            else:
                positrons.append(coords)

        return electrons, positrons
# ==========================================================
# Conversion Dialog
# ==========================================================
class ConversionDialog(QDialog, Ui_Dialog):
    def __init__(self, metodo, base, carga, mult, atomos,
                 geometria_bruta="", titulo="", parent=None, **kwargs):
        super().__init__(parent)
        self.setupUi(self)

        self.geometria_bruta = geometria_bruta
        self.titulo = titulo
        self.available_basis = kwargs.get("basis", [])
        self.lowdin_input = ""

        self.setWindowTitle("Conversion Options")

        # ------------------ METHOD ------------------
        self.metodo_combobox.addItems(list(variablesglobales.valid_methods.values()))
        self.metodo_combobox.setCurrentText(metodo)
        self.metodo_combobox.currentTextChanged.connect(self._on_method_changed)

        # ------------------ CHARGE ------------------
        self.charge_qcombobox.addItems([str(i) for i in range(-10, 11)])
        self.charge_qcombobox.setCurrentText(str(carga))
        self.charge_qcombobox.currentTextChanged.connect(self._update_multiplicity)

        self._update_multiplicity(str(carga))
        self.mult_qcombobox.setCurrentText(str(mult))

        # ------------------ BASIS ------------------
        self.electronic_qcombox.addItems(sorted(self.available_basis))
        self.electronic_qcombox.setEditable(True)
        self.electronic_qcombox.setCurrentText(base)

        self.positronic_qcombox.addItems(variablesglobales.positron_basis)
        self.nuclear_qcombobox.addItems(variablesglobales.nuclear_basis)

        # ------------------ CONTROL ------------------
        self.control_comboBox.addItem("")
        self.control_comboBox.addItems(variablesglobales.tareas_integrales)
        self.Task_pushButton.clicked.connect(self._add_control_option)
        self._extra_control_widgets = []

        # ------------------ BUTTONS ------------------
        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)

    # ------------------------------------------------
    def _update_multiplicity(self, carga_str):
        try:
            carga = int(carga_str)
        except:
            carga = 0

        if carga % 2 == 0:
            mults = ["1", "3", "5", "7", "9"]
        else:
            mults = ["2", "4", "6", "8", "10"]

        self.mult_qcombobox.clear()
        self.mult_qcombobox.addItems(mults)

    def _on_method_changed(self, method):
        if method == "MP2":
            for item in variablesglobales.MP2_tasks:
                if self.control_comboBox.findText(item) == -1:
                    self.control_comboBox.addItem(item)

    def _add_control_option(self):
        combo = QtWidgets.QComboBox()
        combo.addItems(variablesglobales.tareas_integrales)
        combo.setEditable(True)
        self.verticalLayout_3.addWidget(combo)
        self._extra_control_widgets.append(combo)

    def _collect_control(self):
        opts = []
        val = self.control_comboBox.currentText().strip()
        if val:
            opts.append(val)

        for c in self._extra_control_widgets:
            val = c.currentText().strip()
            if val:
                opts.append(val)

        return opts

    def _collect_output_options(self):
        """Collect checked output options from checkboxes."""
        opts = []
        if hasattr(self, 'moldenfile_checkBox') and self.moldenfile_checkBox.isChecked():
            opts.append("moldenFile")
        if hasattr(self, 'wfn_checkBox') and self.wfn_checkBox.isChecked():
            opts.append("wfnFile")
        if hasattr(self, 'wfx_checkBox') and self.wfx_checkBox.isChecked():
            opts.append("wfxFile")
        if hasattr(self, 'NB047_checkBox') and self.NB047_checkBox.isChecked():
            opts.append("NB047File")
        return opts

    def _on_accept(self):
        if not self.geometria_bruta:
            QMessageBox.warning(self, "Error", "No geometry loaded")
            return

        fmt = formatear_geometria(
            geometria_bruta=self.geometria_bruta,
            base_elec=self.electronic_qcombox.currentText(),
            base_proton=self.nuclear_qcombobox.currentText() or "dirac",
            base_positron=self.positronic_qcombox.currentText(),
            multiplicidad=int(self.mult_qcombobox.currentText()),
            carga=int(self.charge_qcombobox.currentText()),
            metodo_real=self.metodo_combobox.currentText(),
            titulo=self.titulo or "Molecule"
        )

        fmt.control_options = self._collect_control()
        fmt.output_options = self._collect_output_options()

        # ------------------ GEOMETRY ------------------
        fmt.agregar_protones()
        fmt.agregar_electrones_desde_atomos()

        # 🔥 PARTICULAS EXTRA
        parent = self.parent()
        if parent:
            for x, y, z in parent.extra_electrons:
                fmt.agregar_electrones("H", x, y, z)

            for x, y, z in parent.extra_positrons:
                fmt.agregar_positrones(x, y, z)

        fmt.formatear_geometria()
        self.lowdin_input = fmt.crear_input_lowdin()

        self.accept()


# ==========================================================
# MAIN WINDOW
# ==========================================================
class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.available_basis = []
        self.current_file = None

        self.extra_electrons = []
        self.extra_positrons = []
        self.geometry_window = None
        self.current_atoms = []

        self.first_run_check()

        # Actions
        self.actionOpen_File.triggered.connect(self.loadfile)
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_file_as)

        self.actionAdd_Electron.triggered.connect(self.open_particles_dialog)
        self.actionPlot_Geometry.triggered.connect(self.plot_geometry)

        self.run_button.clicked.connect(self.run_lowdin)

    # ------------------------------------------------
    def first_run_check(self):
        init = primerinicio.PrimerInicio()
        self.available_basis = init.basis

    # ------------------------------------------------
    def open_particles_dialog(self):
        dialog = AddParticlesDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.extra_electrons, self.extra_positrons = dialog.get_particles()

    # ------------------------------------------------
    def plot_geometry(self):
        if not self.current_atoms:
            QMessageBox.warning(self, "Error", "No geometry loaded — open a file first.")
            return

        self.geometry_window = GeometryVisualizator()
        self.geometry_window.plot_geometry(self.current_atoms)
        self.geometry_window.show()

    # ------------------------------------------------
    def loadfile(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Open file")

        if not archivo:
            return

        with open(archivo, "r") as f:
            contenido = f.read()

        self.input_textedit.setPlainText(contenido)

        parser = parserclass.Parser(contenido)
        datos = parser.parsear()
        self.current_atoms = datos.get("atomos", []) or []

        dialog = ConversionDialog(
            metodo=datos.get("metodo_real", "RHF"),
            base=datos.get("base_elec", ""),
            carga=datos.get("carga", 0),
            mult=datos.get("multiplicidad", 1),
            atomos=datos.get("atomos", []),
            geometria_bruta=datos.get("geometria_bruta", ""),
            titulo=os.path.basename(archivo),
            basis=self.available_basis,
            parent=self
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.translated_textedit.setPlainText(dialog.lowdin_input)

    # ------------------------------------------------
    def save_file_as(self):
        archivo, _ = QFileDialog.getSaveFileName(self, "Save file")

        if archivo:
            with open(archivo, "w") as f:
                f.write(self.translated_textedit.toPlainText())

            self.current_file = archivo

    def save_file(self):
        if self.current_file:
            with open(self.current_file, "w") as f:
                f.write(self.translated_textedit.toPlainText())
        else:
            self.save_file_as()

    # ------------------------------------------------
    def run_lowdin(self):
        """Run LOWDIN calculation in an isolated directory."""
        carpeta = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not carpeta:
            return

        # Write input file
        input_path = os.path.join(carpeta, "input.lowdin")
        try:
            with open(input_path, "w") as f:
                f.write(self.translated_textedit.toPlainText())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to write input file:\n{e}")
            return

        # Run openlowdin with relative path (important!)
        try:
            result = subprocess.run(
                ["openlowdin", "-i", "input.lowdin"],  # Use relative path
                cwd=carpeta,  # Working directory
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            # Read LOWDIN output file if it exists
            output_file_path = os.path.join(carpeta, "input.out")
            lowdin_output = ""

            if os.path.exists(output_file_path):
                try:
                    with open(output_file_path, "r") as f:
                        lowdin_output = f.read()
                except Exception as e:
                    lowdin_output = f"Could not read output file: {e}"

            # Build complete output display
            output_sections = []

            if lowdin_output:
                output_sections.append("=== LOWDIN OUTPUT (input.out) ===\n" + lowdin_output)

            if result.stdout:
                output_sections.append("=== STDOUT ===\n" + result.stdout)

            if result.stderr:
                output_sections.append("=== STDERR ===\n" + result.stderr)

            output = "\n\n".join(output_sections) if output_sections else "No output generated"

            # Check exit code
            if result.returncode != 0:
                output += f"\n\n=== ERROR ===\nProcess exited with code {result.returncode}"
                QMessageBox.warning(
                    self,
                    "LOWDIN Error",
                    f"openlowdin terminated abnormally (exit code {result.returncode})\n\n"
                    f"Check output tab for details."
                )

            self.output_textedit.setPlainText(output)

            # Switch to output tab (index 2 typically)
            if hasattr(self, 'tabWidget'):
                self.tabWidget.setCurrentIndex(2)

        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Timeout", "LOWDIN calculation timed out (>5 min)")
        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Error",
                "openlowdin command not found.\n\n"
                "Make sure LOWDIN is installed and in your PATH."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run LOWDIN:\n{e}")


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())