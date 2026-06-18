# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LOWDIN Translator is a PyQt6-based GUI application that converts quantum chemistry input files (ORCA, Gaussian, XYZ) into LOWDIN format. The application uses an MVC-inspired architecture and provides 3D molecular visualization via PyVista.

## Running the Application

```bash
python mainWindow.py
```

Entry point: `mainWindow.py` (not `main_notused.py`)

The application requires X11 rendering (`QT_QPA_PLATFORM=xcb` is set automatically to fix VTK/OpenGL issues on Wayland).

## Architecture

### Core Components

- `mainWindow.py`: Main application entry point and primary UI controller
  - `MainWindowStudy`: Main window class (inherits from `Ui_MainWindow`)
  - `ConversionDialogStudy`: Dialog for configuring conversion parameters
  - `AddParticlesDialog`: Dialog for adding particles to geometry
  - `LowdinHighlighter`: Syntax highlighter for the LOWDIN output editor

### Model Layer (`model/`)

- `parserclass.py`: Detects format (XYZ, ORCA, Gaussian, Z-matrix) and extracts geometry, basis sets, method, charge, multiplicity
- `formateargeometria_c.py`: Core geometry formatter that generates LOWDIN input files
  - Handles particle ordering: electrons first, then positrons, then nuclei
  - Manages basis set assignments per particle type
- `variablesglobales.py`: Global constants and mappings
  - `valid_methods`: Maps external method names to LOWDIN equivalents
  - `valid_basis`: Maps basis set name variations to LOWDIN format
  - `positron_basis`, `nuclear_basis`: Available bases for exotic particles
  - Task lists for different computational methods (HF, MP2, SCF)
- `primerinicio.py`: First-run initialization, searches for LOWDIN executable and available basis sets
- `geometryeditor.py`: 3D geometry manipulation, selection, measurement, and PyVista rendering
- `geometryoptimizer.py`: RDKit-based geometry optimization (UFF and MMFF force fields)
- `inputvalidator.py`: Validates method/charge/multiplicity consistency, suggests RHF vs UHF
- `basisnormalizer.py`: Normalizes basis set names across ORCA/Gaussian/LOWDIN conventions
- `zmatrix_parser.py`: Parses Z-matrix input format and converts to Cartesian coordinates

### View Layer (`view/`)

- `geometrydialog.py`: 3D geometry editor dialog (PyVista, selection mode, add/remove atoms, optimization)
- `particlerow.py`: UI components for particle table rows
- `setupdialog.py`: Setup dialog views

### UI Layer (`UI/`)

Contains Qt Designer `.ui` files and their auto-generated Python counterparts:
- `mainwindow_test.py` / `mainwindow.ui`: Main window UI
- `conversiondialog_test.py` / `conversiondialog.ui`: Conversion dialog UI
- `addElectrons.py` / `addElectrons.ui`: Add particles dialog UI
- `geomvisualizator.py` / `geometry_visualizator.ui`: 3D geometry editor widget UI

To regenerate a Python UI file after editing the `.ui` in Qt Designer:
```bash
python -m PyQt6.uic.pyuic UI/mainwindow.ui -o UI/mainwindow_test.py
```

## Key Data Flow

1. User loads file via `MainWindow.loadfile()` → File dialog
2. `parserclass.Parser` detects format and extracts data
3. `ConversionDialog` opens with detected parameters
4. User configures method, basis sets, charge, multiplicity, control options
5. `formateargeometria_c.formatear_geometria` generates LOWDIN input
6. Formatted input displayed in main window's translated text edit

## Important Patterns

### Method and Basis Handling

Methods like MP2 auto-adjust to RHF/UHF depending on multiplicity. Functional names (B3LYP, PBE) automatically map to RKS/UKS. All mappings are in `variablesglobales.py`.

### Particle Ordering in LOWDIN Format

LOWDIN requires strict particle ordering in GEOMETRY blocks:
1. Electrons: `e-(SYMBOL)  basis  x  y  z  addParticles=N`
2. Positrons: `e+  basis  x  y  z`
3. Nuclei: `SYMBOL  dirac  x  y  z` (classical) or `SYMBOL  basis  x  y  z` (APMO quantum nuclei)

This ordering is enforced in `formateargeometria_c.py`.

### Configuration Storage

User settings stored in `~/.config/lowdintranslator/config.ini` including LOWDIN executable path.

## File Naming Conventions

Files suffixed with `_notused` or `_test` indicate:
- `_notused`: Deprecated/replaced code, kept locally for reference but not tracked
- `_test`: Auto-generated Python from Qt Designer `.ui` files (do not edit by hand)

## Dependencies

Key packages: PyQt6, pyvista, pyvistaqt, matplotlib, numpy, scipy, rdkit

Virtual environment at `.venv/` (Python 3.14)

## Approach

- Read existing files before writing. Don't re-read unless changed.
- Thorough in reasoning, concise in output.
- Skip files over 100KB unless required.
- No sycophantic openers or closing fluff.
- No emojis or em-dashes.
- Do not guess APIs, versions, flags, commit SHAs, or package names. Verify by reading code or docs before asserting.
