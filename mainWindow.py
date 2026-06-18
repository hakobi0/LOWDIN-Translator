import os
import sys
import subprocess

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PyQt6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFileDialog, QInputDialog,
    QLabel, QMainWindow, QMessageBox, QWidget, QHBoxLayout, QComboBox, QDoubleSpinBox
)
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor

from model import parserclass, primerinicio, variablesglobales
from model.formateargeometria_c import formatear_geometria
from model.inputvalidator import suggest_method, validation_summary
from model.basisnormalizer import resolve_basis, validate_basis
from UI.conversiondialog_test import Ui_Dialog
from UI.mainwindow_test import Ui_MainWindow
from UI.addElectrons import Ui_addParticlesDialog
from view.geometrydialog import GeometryDialogStudy


import re as _re

# ---------------------------------------------------------------------------
# UI Theme stylesheets
# ---------------------------------------------------------------------------

DARK_STYLESHEET = """
QWidget {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}
QMainWindow, QDialog {
    background-color: #1e1e1e;
}
QMenuBar {
    background-color: #252526;
    color: #cccccc;
    border-bottom: 1px solid #3c3c3c;
}
QMenuBar::item:selected {
    background-color: #094771;
}
QMenu {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3c3c3c;
}
QMenu::item:selected {
    background-color: #094771;
}
QTabWidget::pane {
    border: 1px solid #3c3c3c;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d2d;
    color: #aaaaaa;
    padding: 5px 14px;
    border: 1px solid #3c3c3c;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #ffffff;
    border-bottom: 2px solid #007acc;
}
QTabBar::tab:hover:!selected {
    background-color: #3a3a3a;
}
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    selection-background-color: #264f78;
}
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 5px;
    margin-top: 8px;
    padding-top: 4px;
    color: #9cdcfe;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}
QComboBox {
    background-color: #2d2d2d;
    color: #d4d4d4;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 3px 8px;
    selection-background-color: #094771;
}
QComboBox:hover { border-color: #007acc; }
QComboBox::drop-down { border: none; width: 20px; }
QComboBox QAbstractItemView {
    background-color: #252526;
    color: #d4d4d4;
    selection-background-color: #094771;
    border: 1px solid #3c3c3c;
}
QPushButton {
    background-color: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 5px 14px;
}
QPushButton:hover    { background-color: #4a4a4a; border-color: #888; }
QPushButton:pressed  { background-color: #2d2d2d; }
QPushButton:checked  { background-color: #094771; border-color: #007acc; }
QPushButton:disabled { color: #666; border-color: #3c3c3c; }
QCommandLinkButton {
    background-color: #0e639c;
    color: #ffffff;
    border: 1px solid #1177bb;
    border-radius: 4px;
    padding: 5px 14px;
    font-weight: bold;
}
QCommandLinkButton:hover  { background-color: #1177bb; }
QCommandLinkButton:pressed { background-color: #0a4f7e; }
QCheckBox { color: #d4d4d4; spacing: 6px; }
QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #555; border-radius: 3px;
    background-color: #2d2d2d;
}
QCheckBox::indicator:checked { background-color: #007acc; border-color: #007acc; }
QLabel { color: #d4d4d4; }
QScrollBar:vertical {
    background: #252526; width: 10px; border: none;
}
QScrollBar::handle:vertical {
    background: #424242; border-radius: 5px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #555; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #252526; height: 10px; border: none;
}
QScrollBar::handle:horizontal {
    background: #424242; border-radius: 5px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #555; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QStatusBar {
    background-color: #007acc;
    color: #ffffff;
    font-size: 12px;
}
QDialogButtonBox QPushButton {
    min-width: 70px;
}
QMessageBox { background-color: #1e1e1e; color: #d4d4d4; }
"""

LIGHT_STYLESHEET = ""  # Empty = Qt default system style

# ---------------------------------------------------------------------------
# Each scheme: (keyword, atom, particle, number, string_, comment, param)
# keyword = block keywords bold
# atom    = element symbols in GEOMETRY
# particle= e-(X) / e+(X) lines
# number  = float coordinates
# string_ = quoted strings
# comment = # comments
# param   = parameter names (method=, multiplicity=, …)

HIGHLIGHT_SCHEMES = {
    "Dark (VS Code)": {
        "keyword":  ("#569CD6", True),
        "atom":     ("#4EC9B0", False),
        "particle": ("#CE9178", False),
        "number":   ("#B5CEA8", False),
        "string_":  ("#CE9178", False),
        "comment":  ("#6A9955", False),
        "param":    ("#9CDCFE", False),
    },
    "Light (GitHub)": {
        "keyword":  ("#0550AE", True),
        "atom":     ("#116329", False),
        "particle": ("#953800", False),
        "number":   ("#0550AE", False),
        "string_":  ("#0A3069", False),
        "comment":  ("#57606A", False),
        "param":    ("#6639BA", False),
    },
    "Solarized Dark": {
        "keyword":  ("#268BD2", True),
        "atom":     ("#2AA198", False),
        "particle": ("#CB4B16", False),
        "number":   ("#859900", False),
        "string_":  ("#2AA198", False),
        "comment":  ("#657B83", False),
        "param":    ("#6C71C4", False),
    },
    "Monokai": {
        "keyword":  ("#F92672", True),
        "atom":     ("#A6E22E", False),
        "particle": ("#FD971F", False),
        "number":   ("#AE81FF", False),
        "string_":  ("#E6DB74", False),
        "comment":  ("#75715E", False),
        "param":    ("#66D9E8", False),
    },
}

_KEYWORDS = ["GEOMETRY", "END GEOMETRY", "TASKS", "END TASKS",
             "CONTROL", "END CONTROL", "SYSTEM_DESCRIPTION"]
_PARAM_RE = _re.compile(
    r'\b(method|multiplicity|addParticles|mollerPlessetCorrection|'
    r'electronExchangeCorrelationFunctional)\b'
)
_ATOM_RE    = _re.compile(r'^\s*(?!e[-+])\b([A-Z][a-z]?)\b', _re.MULTILINE)
_PARTICLE_RE = _re.compile(r'e[+-]\([A-Za-z]+\)')
_BARE_PE_RE  = _re.compile(r'\be[+-]\b')
_NUMBER_RE  = _re.compile(r'[-+]?\d+\.\d+')
_STRING_RE  = _re.compile(r"'[^']*'")
_COMMENT_RE = _re.compile(r'#.*')


class LowdinHighlighter(QSyntaxHighlighter):
    def __init__(self, document, scheme="Dark (VS Code)"):
        super().__init__(document)
        self._rules = []
        self.set_scheme(scheme)

    def set_scheme(self, name):
        palette = HIGHLIGHT_SCHEMES.get(name, HIGHLIGHT_SCHEMES["Dark (VS Code)"])

        def _fmt(color, bold=False):
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        self._rules = []
        kw_color, kw_bold = palette["keyword"]
        kw_fmt = _fmt(kw_color, kw_bold)
        for kw in _KEYWORDS:
            self._rules.append((_re.compile(rf'\b{_re.escape(kw)}\b'), kw_fmt))

        self._rules += [
            (_ATOM_RE,     _fmt(*palette["atom"])),
            (_PARTICLE_RE, _fmt(*palette["particle"])),
            (_BARE_PE_RE,  _fmt(*palette["particle"])),
            (_NUMBER_RE,   _fmt(*palette["number"])),
            (_STRING_RE,   _fmt(*palette["string_"])),
            (_COMMENT_RE,  _fmt(*palette["comment"])),
            (_PARAM_RE,    _fmt(*palette["param"])),
        ]
        self.rehighlight()

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for m in pattern.finditer(text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class AddParticlesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_addParticlesDialog()
        self.ui.setupUi(self)

        self.rows = []

        # Connections
        self.ui.addbutton.clicked.connect(self.add_row)
        self.ui.removebutton.clicked.connect(self.remove_row)

        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)

        # Add initial row
        self.add_row()

    def add_row(self):
        row_widget = QWidget()
        layout = QHBoxLayout(row_widget)

        tipo = QComboBox()
        tipo.addItems(["e-", "e+", "U-", "U+"])

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

        # Add to scroll layout
        self.ui.verticalLayout_2.addWidget(row_widget)

        # Save reference
        self.rows.append((row_widget, tipo, x, y, z))

    def remove_row(self):
        if not self.rows:
            return

        row_widget, *_ = self.rows.pop()
        row_widget.setParent(None)
        row_widget.deleteLater()

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


class ConversionDialogStudy(QDialog, Ui_Dialog):
    def __init__(self, metodo, base, carga, mult, atomos,
                 geometria_bruta="", titulo="", parent=None, **kwargs):
        super().__init__(parent)
        self.setupUi(self)

        self.geometria_bruta = geometria_bruta
        self.titulo = titulo
        self.atomos = atomos or []
        self.available_basis = kwargs.get("basis", [])
        self.lowdin_input = ""

        self.setWindowTitle("Conversion Options Study")

        self.metodo_combobox.addItems(list(variablesglobales.valid_methods.values()))
        self.metodo_combobox.setCurrentText(metodo)

        self.charge_qcombobox.addItems([str(i) for i in range(-10, 11)])
        self.charge_qcombobox.setCurrentText(str(carga))
        self.charge_qcombobox.currentTextChanged.connect(self._update_multiplicity)

        self._update_multiplicity(str(carga))
        self.mult_qcombobox.setCurrentText(str(mult))

        self.electronic_qcombox.addItems(sorted(self.available_basis))
        self.electronic_qcombox.setEditable(True)
        self.electronic_qcombox.setCurrentText(base)

        self.positronic_qcombox.addItems(variablesglobales.positron_basis)
        if kwargs.get("base_positron"):
            self.positronic_qcombox.setCurrentText(kwargs["base_positron"])
        self.nuclear_qcombobox.addItems(variablesglobales.nuclear_basis)
        if kwargs.get("base_proton"):
            self.nuclear_qcombobox.setCurrentText(kwargs["base_proton"])

        self.control_comboBox.addItem("")
        self.control_comboBox.addItems(variablesglobales.tareas_integrales)

        # --- Validation panel (inserted above OK/Cancel) ---
        self._validation_label = QLabel()
        self._validation_label.setWordWrap(True)
        self._validation_label.setStyleSheet("padding: 4px;")
        # verticalLayout is the main layout from Ui_Dialog; insert before the last item (buttonBox)
        idx = self.verticalLayout.count() - 1
        self.verticalLayout.insertWidget(idx, self._validation_label)

        self.metodo_combobox.currentTextChanged.connect(self._run_validation)
        self.charge_qcombobox.currentTextChanged.connect(self._run_validation)
        self.mult_qcombobox.currentTextChanged.connect(self._run_validation)
        self.electronic_qcombox.currentTextChanged.connect(self._run_validation)
        self._run_validation()

        self.buttonBox.accepted.connect(self._on_accept)
        self.buttonBox.rejected.connect(self.reject)

    def _update_multiplicity(self, carga_str):
        carga = int(carga_str)
        if carga % 2 == 0:
            multiplicities = ["1", "3", "5", "7", "9"]
        else:
            multiplicities = ["2", "4", "6", "8", "10"]
        self.mult_qcombobox.clear()
        self.mult_qcombobox.addItems(multiplicities)

    def _run_validation(self):
        try:
            charge = int(self.charge_qcombobox.currentText())
            mult = int(self.mult_qcombobox.currentText())
            method = self.metodo_combobox.currentText()
            basis_input = self.electronic_qcombox.currentText().strip()
        except (ValueError, AttributeError):
            return

        messages = []
        has_error = False

        # --- Basis resolution ---
        if basis_input:
            basis_result = validate_basis(basis_input)
            resolved_basis = basis_result["resolved"]

            # Auto-correct the combobox to the canonical name silently
            if basis_result["matched"] and resolved_basis != basis_input:
                self.electronic_qcombox.blockSignals(True)
                self.electronic_qcombox.setCurrentText(resolved_basis)
                self.electronic_qcombox.blockSignals(False)
            elif not basis_result["matched"]:
                messages.append(("warning", basis_result["warning"]))

        # --- Method / spin validation ---
        if self.atomos:
            result = suggest_method(method, self.atomos, charge, mult)
            spin_messages = validation_summary(self.atomos, charge, mult, method)

            corrected = result["corrected_method"]
            if corrected != method:
                self.metodo_combobox.blockSignals(True)
                self.metodo_combobox.setCurrentText(corrected)
                self.metodo_combobox.blockSignals(False)

            messages.extend(spin_messages)

        # --- Build display ---
        colors = {"error": "#cc0000", "warning": "#b36b00"}
        lines = []
        for level, msg in messages:
            if level == "info":
                continue
            if level == "error":
                has_error = True
            color = colors.get(level, "black")
            lines.append(f'<span style="color:{color};">{msg}</span>')

        self._validation_label.setText("<br>".join(lines))

        ok_btn = self.buttonBox.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setEnabled(not has_error)

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

    def _collect_control_options(self):
        """Collect control options from combobox."""
        opts = []
        val = self.control_comboBox.currentText().strip()
        if val:
            opts.append(val)
        return opts

    def _on_accept(self):
        if not self.geometria_bruta:
            QMessageBox.warning(self, "No geometry", "No geometry loaded.")
            return

        fmt = formatear_geometria(
            geometria_bruta=self.geometria_bruta,
            base_elec=self.electronic_qcombox.currentText(),
            base_proton=self.nuclear_qcombobox.currentText() or "dirac",
            base_positron=self.positronic_qcombox.currentText(),
            multiplicidad=int(self.mult_qcombobox.currentText()),
            carga=int(self.charge_qcombobox.currentText()),
            metodo_real=self.metodo_combobox.currentText(),
            titulo=self.titulo or "Molecule",
        )

        # Add control and output options
        fmt.control_options = self._collect_control_options()
        fmt.output_options = self._collect_output_options()

        fmt.agregar_protones()
        fmt.agregar_electrones_desde_atomos()

        # Add extra particles from parent
        parent = self.parent()
        if parent:
            for x, y, z in parent.extra_electrons:
                fmt.agregar_electrones("H", x, y, z)

            for x, y, z in parent.extra_positrons:
                fmt.agregar_positrones(x, y, z)

        fmt.formatear_geometria()
        self.lowdin_input = fmt.crear_input_lowdin()
        self.accept()


class MainWindowStudy(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.available_basis = []
        self.current_atoms = []
        self.last_conversion = None
        self.current_file = None  # Track current file for Save
        self.extra_electrons = []
        self.extra_positrons = []

        self._highlighter = LowdinHighlighter(self.translated_textedit.document(), scheme="Light (GitHub)")
        self._build_view_menu()

        self.first_run_check()

        # File menu actions
        self.actionOpen_File.triggered.connect(self.loadfile)
        if hasattr(self, 'actionSave'):
            self.actionSave.triggered.connect(self.save_file)
        if hasattr(self, 'actionSave_As'):
            self.actionSave_As.triggered.connect(self.save_file_as)

        # Edit/Tools menu actions
        self.actionConversion_Dialog.triggered.connect(self.opendialog)
        self.actionAdd_Geometry.triggered.connect(self.open_geometry_editor)
        self.actionPlot_Geometry.triggered.connect(self.open_geometry_editor)
        if hasattr(self, 'actionAdd_Electron'):
            self.actionAdd_Electron.triggered.connect(self.open_particles_dialog)
        if hasattr(self, 'actionZ_Matrix_Representation'):
            self.actionZ_Matrix_Representation.triggered.connect(self.show_zmatrix)

        # Multiwfn analysis actions
        if hasattr(self, 'actionElectron_Density_map'):
            self.actionElectron_Density_map.triggered.connect(
                lambda: self.run_multiwfn("electron_density.txt")
            )
        if hasattr(self, 'actionESP_map'):
            self.actionESP_map.triggered.connect(
                lambda: self.run_multiwfn("esp_map.txt")
            )
        if hasattr(self, 'actionELF_map'):
            self.actionELF_map.triggered.connect(
                lambda: self.run_multiwfn("elf_map.txt")
            )
        if hasattr(self, 'actionOrbital_plot'):
            self.actionOrbital_plot.triggered.connect(
                lambda: self.run_multiwfn("orbital_plot.txt")
            )
        if hasattr(self, 'actionLOL_map'):
            self.actionLOL_map.triggered.connect(
                lambda: self.run_multiwfn("lol_map.txt")
            )

        # Connect run button if it exists
        if hasattr(self, 'run_button'):
            self.run_button.clicked.connect(self.run_lowdin)

    def first_run_check(self):
        init = primerinicio.PrimerInicio()
        self.available_basis = init.basis

    def _build_view_menu(self):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction, QActionGroup

        view_menu = QMenu("View", self)

        # --- UI Theme ---
        theme_menu = view_menu.addMenu("UI Theme")
        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        act_light = QAction("Light (System Default)", self, checkable=True)
        act_dark  = QAction("Dark",                   self, checkable=True)
        act_light.setChecked(True)

        def _apply_theme(stylesheet, default_syntax, plotter_bg):
            QApplication.instance().setStyleSheet(stylesheet)
            self._highlighter.set_scheme(default_syntax)
            GeometryDialogStudy.plotter_background = plotter_bg
            # Sync the checked syntax action
            for a in syntax_group.actions():
                a.setChecked(a.text() == default_syntax)

        act_light.triggered.connect(lambda: _apply_theme(LIGHT_STYLESHEET, "Light (GitHub)", "white"))
        act_dark.triggered.connect( lambda: _apply_theme(DARK_STYLESHEET,  "Dark (VS Code)", "black"))

        for act in (act_light, act_dark):
            theme_group.addAction(act)
            theme_menu.addAction(act)

        view_menu.addSeparator()

        # --- Syntax Theme ---
        syntax_menu = view_menu.addMenu("Syntax Theme")
        syntax_group = QActionGroup(self)
        syntax_group.setExclusive(True)
        for name in HIGHLIGHT_SCHEMES:
            act = QAction(name, self, checkable=True)
            if name == "Light (GitHub)":
                act.setChecked(True)
            act.triggered.connect(lambda checked, n=name: self._highlighter.set_scheme(n))
            syntax_group.addAction(act)
            syntax_menu.addAction(act)

        self.menubar.addMenu(view_menu)

    def loadfile(self):
        archivo, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir archivo",
            "",
            "All Supported (*.out *.log *.txt *.xyz *.inp *.com *.zmat *.lowdin);;LOWDIN Files (*.lowdin);;Z-Matrix (*.zmat);;XYZ Files (*.xyz);;Output Files (*.out *.log *.txt);;Input Files (*.inp *.com);;All Files (*)",
        )
        if not archivo:
            return

        with open(archivo, "r") as handle:
            contenido = handle.read()

        self.input_textedit.setPlainText(contenido)

        # .lowdin files: show directly and parse for conversion dialog editing
        if archivo.endswith(".lowdin"):
            self.translated_textedit.setPlainText(contenido)
            self.current_file = archivo
            self.tabWidget.setCurrentIndex(1)
            self.last_conversion = self._parse_lowdin(contenido, archivo)
            return

        parser = parserclass.Parser(contenido)
        datos = parser.parsear()

        geometria_bruta = datos.get("geometria_bruta", "")
        atomos = datos.get("atomos", []) or []
        if not atomos and geometria_bruta and geometria_bruta != "GEOMETRY_NOT_FOUND":
            atomos = self._atoms_from_geometry_text(geometria_bruta)

        self.current_atoms = atomos

        # Handle None values from parser
        mult = datos.get("multiplicidad", 1)
        if mult is None:
            mult = 1

        carga = datos.get("carga", 0)
        if carga is None:
            carga = 0

        raw_base = datos.get("base_elec", "") or ""
        resolved_base, basis_matched = resolve_basis(raw_base) if raw_base not in ("", "NONE") else ("", False)
        basis_unknown = raw_base in ("", "NONE") or not basis_matched

        self.last_conversion = {
            "metodo": datos.get("metodo_real", "RHF") or "RHF",
            "base": resolved_base,
            "base_positron": "",
            "base_proton": "dirac",
            "carga": carga,
            "mult": mult,
            "geometria_bruta": geometria_bruta,
            "titulo": datos.get("titulo", os.path.basename(archivo)) or os.path.basename(archivo),
            "atomos": self.current_atoms[:],
        }

        if basis_unknown:
            # Basis could not be detected or resolved — open the dialog immediately
            # so the user can pick one rather than generating a broken input silently.
            if raw_base in ("", "NONE"):
                msg = "No basis set was detected in this file."
            else:
                msg = f'Basis "{raw_base}" is not in the LOWDIN library.'
            QMessageBox.warning(
                self,
                "Basis Set Required",
                f"{msg}\n\nThe Conversion Dialog will open so you can select one."
            )
            self.opendialog()
        else:
            self._rebuild_lowdin_from_state()

    def opendialog(self):
        if not self.last_conversion:
            QMessageBox.information(self, "No file", "Load a file first.")
            return

        data = self.last_conversion
        dialog = ConversionDialogStudy(
            metodo=data["metodo"],
            base=data["base"],
            carga=data["carga"],
            mult=data["mult"],
            atomos=data["atomos"],
            geometria_bruta=data["geometria_bruta"],
            titulo=data["titulo"],
            basis=self.available_basis,
            base_positron=data.get("base_positron", ""),
            base_proton=data.get("base_proton", "dirac"),
            parent=self,
        )

        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.lowdin_input:
            self.last_conversion["metodo"] = dialog.metodo_combobox.currentText()
            self.last_conversion["base"] = dialog.electronic_qcombox.currentText()
            self.last_conversion["base_positron"] = dialog.positronic_qcombox.currentText()
            self.last_conversion["base_proton"] = dialog.nuclear_qcombobox.currentText()
            self.last_conversion["carga"] = int(dialog.charge_qcombobox.currentText())
            self.last_conversion["mult"] = int(dialog.mult_qcombobox.currentText())
            self.translated_textedit.setPlainText(dialog.lowdin_input)
            self.tabWidget.setCurrentIndex(1)

    def open_particles_dialog(self):
        dialog = AddParticlesDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.extra_electrons, self.extra_positrons = dialog.get_particles()
            # Rebuild input if we have a previous conversion
            if self.last_conversion:
                self._rebuild_lowdin_from_state()

    def show_zmatrix(self):
        if not self.current_atoms:
            QMessageBox.information(self, "No geometry", "Load a geometry first.")
            return

        from model.geometryeditor import GeometryEditor
        from PyQt6.QtWidgets import QTextEdit, QPushButton, QVBoxLayout
        from PyQt6.QtGui import QFont

        editor = GeometryEditor(self.current_atoms)
        zmatrix = editor.calculate_zmatrix()

        dialog = QDialog(self)
        dialog.setWindowTitle("Z-Matrix (Internal Coordinates)")
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setPlainText(zmatrix)
        text_edit.setFont(QFont("Courier New", 10))
        layout.addWidget(text_edit)

        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)

        dialog.exec()

    def open_geometry_editor(self):
        dialog = GeometryDialogStudy(self.current_atoms, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_atoms = dialog.get_atoms()
        if not new_atoms:
            return

        self.current_atoms = new_atoms
        geometria_bruta = dialog.get_geometria_bruta()

        if self.last_conversion is not None:
            self.last_conversion["atomos"] = self.current_atoms[:]
            self.last_conversion["geometria_bruta"] = geometria_bruta
            self._rebuild_lowdin_from_state()
        else:
            # No file loaded — geometry was drawn from scratch.
            # Bootstrap last_conversion and open ConversionDialog so the user
            # can pick method, basis, charge and multiplicity.
            self.last_conversion = {
                "metodo": "RHF",
                "base": self.available_basis[0] if self.available_basis else "",
                "base_positron": "",
                "base_proton": "dirac",
                "carga": 0,
                "mult": 1,
                "geometria_bruta": geometria_bruta,
                "titulo": "Molecule",
                "atomos": self.current_atoms[:],
            }
            self.opendialog()

    def _rebuild_lowdin_from_state(self):
        if not self.last_conversion:
            return

        data = self.last_conversion
        fmt = formatear_geometria(
            geometria_bruta=data["geometria_bruta"],
            base_elec=data["base"],
            base_proton=data.get("base_proton", "dirac"),
            base_positron=data.get("base_positron", ""),
            multiplicidad=data["mult"],
            carga=data["carga"],
            metodo_real=data["metodo"],
            titulo=data["titulo"],
        )

        fmt.agregar_protones()
        fmt.agregar_electrones_desde_atomos()

        # Add extra particles
        for x, y, z in self.extra_electrons:
            fmt.agregar_electrones("H", x, y, z)

        for x, y, z in self.extra_positrons:
            fmt.agregar_positrones(x, y, z)

        fmt.formatear_geometria()
        self.translated_textedit.setPlainText(fmt.crear_input_lowdin())
        self.tabWidget.setCurrentIndex(1)

    @staticmethod
    def _atoms_from_geometry_text(geometria_bruta):
        atoms = []
        for line in geometria_bruta.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                atoms.append((
                    parts[0].capitalize(),
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                ))
        return atoms

    def _parse_lowdin(self, contenido, archivo):
        """Extract conversion parameters from a .lowdin file."""
        import re

        # Title
        titulo_match = re.search(r"SYSTEM_DESCRIPTION='([^']*)'", contenido)
        titulo = titulo_match.group(1) if titulo_match else os.path.basename(archivo)

        # Method
        metodo_match = re.search(r'method\s*=\s*"([^"]+)"', contenido)
        metodo = metodo_match.group(1) if metodo_match else "RHF"

        # Charge and multiplicity
        charge_match = re.search(r'charge\s*=\s*(-?\d+)', contenido)
        mult_match = re.search(r'multiplicity\s*=\s*(\d+)', contenido)
        carga = int(charge_match.group(1)) if charge_match else 0
        mult = int(mult_match.group(1)) if mult_match else 1

        # Parse geometry block to extract basis sets and atoms
        geom_match = re.search(r'GEOMETRY\s*(.*?)\s*END GEOMETRY', contenido, re.DOTALL)
        geometria_bruta = ""
        atomos = []
        base_elec = ""
        base_proton = "dirac"
        base_positron = ""

        if geom_match:
            geom_lines = geom_match.group(1).strip().splitlines()
            nuclear_lines = []

            for line in geom_lines:
                parts = line.split()
                if len(parts) < 5:
                    continue
                label, basis = parts[0], parts[1]
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])

                if label.startswith("e-("):
                    # Electron line: e-(SYMBOL) → extract electronic basis
                    if not base_elec:
                        base_elec = basis
                elif label.startswith("e+"):
                    if not base_positron:
                        base_positron = basis
                else:
                    # Nuclear line
                    base_proton = basis
                    symbol = label.capitalize()
                    atomos.append((symbol, x, y, z))
                    nuclear_lines.append(f"{symbol} {x} {y} {z}")

            geometria_bruta = "\n".join(nuclear_lines)

        self.current_atoms = atomos

        return {
            "metodo": metodo,
            "base": base_elec,
            "base_positron": base_positron,
            "base_proton": base_proton,
            "carga": carga,
            "mult": mult,
            "geometria_bruta": geometria_bruta,
            "titulo": titulo,
            "atomos": atomos[:],
        }

    def run_multiwfn(self, script_name):
        """Run a Multiwfn analysis using the given input script."""
        # Ask for molden file
        molden_file, _ = QFileDialog.getOpenFileName(
            self,
            "Select Molden file",
            "",
            "Molden Files (*.molden *.mld);;All Files (*)",
        )
        if not molden_file:
            return

        scripts_dir = os.path.join(os.path.dirname(__file__), "multiwfn_scripts")
        script_path = os.path.join(scripts_dir, script_name)

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Script not found:\n{script_path}")
            return

        work_dir = os.path.dirname(molden_file)

        try:
            with open(script_path, "r") as f:
                script_input = f.read()

            # Scripts that support plane + grid quality selection
            # Values: (plane_line_index, grid_quality_line_index)
            map_scripts = {
                "electron_density.txt": (4, 5),
                "esp_map.txt":          (4, 5),
                "elf_map.txt":          (4, 5),
                "lol_map.txt":          (4, 5),
                "orbital_plot.txt":     (5, 6),  # shifted by orbital selector line
            }

            lines = script_input.splitlines()

            # For orbital plot, ask which orbital and graph type
            if script_name == "orbital_plot.txt":
                orbital, accepted = QInputDialog.getText(
                    self,
                    "Orbital Selection",
                    "Enter orbital number to plot\n(or 'h' for HOMO, 'l' for LUMO):",
                    text="h",
                )
                if not accepted:
                    return
                lines[2] = orbital.strip() or "h"

                graph_type, accepted = QInputDialog.getItem(
                    self,
                    "Graph Type",
                    "Select graph type:",
                    [
                        "1 - Contour map",
                        "2 - Color-filled map",
                        "3 - Contour + color-filled",
                        "4 - Gradient lines",
                        "5 - Vector field",
                    ],
                    1,  # Default: color-filled
                    False,
                )
                if not accepted:
                    return
                lines[3] = graph_type[0]  # Extract "1"-"5"

            # For all 2D map scripts, ask plane and grid quality
            if script_name in map_scripts:
                plane_idx, grid_idx = map_scripts[script_name]

                plane, accepted = QInputDialog.getItem(
                    self,
                    "Plane Selection",
                    "Select the plane to plot:",
                    ["XY (1)", "XZ (2)", "YZ (3)"],
                    1,  # Default: XZ
                    False,
                )
                if not accepted:
                    return
                lines[plane_idx] = plane[plane.index("(") + 1]

                grid, accepted = QInputDialog.getText(
                    self,
                    "Grid Resolution",
                    "How many grid points in each dimension?\n"
                    "Enter as two numbers separated by a comma (e.g. 400,400)\n"
                    "Leave empty to use Multiwfn default (200,200):",
                    text="",
                )
                if not accepted:
                    return
                grid = grid.strip()
                if grid:
                    lines[grid_idx] = grid

            script_input = "\n".join(lines) + "\n"

            multiwfn_exe = "Multiwfn"
            for candidate in [
                "Multiwfn",
                os.path.expanduser("~/Multiwfn/Multiwfn"),
            ]:
                if os.path.isfile(candidate) or any(
                    os.path.isfile(os.path.join(p, candidate))
                    for p in os.environ.get("PATH", "").split(os.pathsep)
                ):
                    multiwfn_exe = candidate
                    break

            result = subprocess.run(
                [multiwfn_exe, molden_file, "-silent"],
                input=script_input,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Look for PNG output in the working directory
            png_candidates = ["surfdens.png", "ELF.png", "orb.png"]
            png_found = None
            for candidate in png_candidates:
                path = os.path.join(work_dir, candidate)
                if os.path.exists(path):
                    png_found = path
                    break

            if png_found:
                self._show_image(png_found, script_name)
            else:
                # No PNG - show text output instead
                output = result.stdout or result.stderr or "No output generated."
                from PyQt6.QtWidgets import QTextEdit, QPushButton, QVBoxLayout
                from PyQt6.QtGui import QFont
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Multiwfn - {script_name}")
                dialog.resize(700, 500)
                layout = QVBoxLayout(dialog)
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setPlainText(output)
                text_edit.setFont(QFont("Courier New", 9))
                layout.addWidget(text_edit)
                btn = QPushButton("Close")
                btn.clicked.connect(dialog.close)
                layout.addWidget(btn)
                dialog.exec()

        except FileNotFoundError:
            QMessageBox.critical(
                self,
                "Error",
                "Multiwfn command not found.\n\nMake sure Multiwfn is installed and in your PATH."
            )
        except subprocess.TimeoutExpired:
            QMessageBox.critical(self, "Timeout", "Multiwfn calculation timed out (>5 min)")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to run Multiwfn:\n{e}")

    def _show_image(self, image_path, title=""):
        """Display a PNG image in a resizable dialog."""
        from PyQt6.QtWidgets import QScrollArea, QLabel, QPushButton, QVBoxLayout
        from PyQt6.QtGui import QPixmap

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Multiwfn - {title}")
        dialog.resize(800, 700)

        layout = QVBoxLayout(dialog)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        label = QLabel()
        pixmap = QPixmap(image_path)
        label.setPixmap(pixmap)
        label.setScaledContents(False)

        scroll.setWidget(label)
        layout.addWidget(scroll)

        btn = QPushButton("Close")
        btn.clicked.connect(dialog.close)
        layout.addWidget(btn)

        dialog.exec()

    def save_file(self):
        """Save the translated LOWDIN input to current file."""
        if self.current_file:
            try:
                with open(self.current_file, "w") as f:
                    f.write(self.translated_textedit.toPlainText())
                self.statusBar().showMessage(f"Saved to {self.current_file}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")
        else:
            # No current file, use Save As
            self.save_file_as()

    def save_file_as(self):
        """Save the translated LOWDIN input to a new file."""
        archivo, _ = QFileDialog.getSaveFileName(
            self,
            "Save LOWDIN input file",
            "",
            "LOWDIN Files (*.lowdin);;All Files (*)"
        )

        if archivo:
            try:
                with open(archivo, "w") as f:
                    f.write(self.translated_textedit.toPlainText())
                self.current_file = archivo
                self.statusBar().showMessage(f"Saved to {archivo}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

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
                timeout=600  # 10 minute timeout
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

            # Display in output tab and switch to it
            if hasattr(self, 'output_textedit'):
                self.output_textedit.setPlainText(output)
                # Switch to output tab (usually index 2, but check your UI)
                if hasattr(self, 'tabWidget'):
                    self.tabWidget.setCurrentIndex(2)  # Adjust index if needed
            else:
                # Show in dialog if no output widget
                QMessageBox.information(self, "LOWDIN Output", output[:1000] + "...")

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("LOWDIN Translator Geometry Study")
    window = MainWindowStudy()
    window.show()
    sys.exit(app.exec())
