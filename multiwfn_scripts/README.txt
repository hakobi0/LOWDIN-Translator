MULTIWFN INPUT SCRIPTS
======================
Usage: Multiwfn your_file.molden -silent < script.txt

All 2D maps save a PNG to the current folder.
All cube files save a .cub file to the current folder.

------------------------------------------------------------------------
2D PLANE MAPS (PNG output)
------------------------------------------------------------------------

electron_density.txt
    Electron density color-filled map (XZ plane, Y=0)
    Output: surfdens.png

esp_map.txt
    Electrostatic potential (ESP) color-filled map with vdW surface overlay
    Output: surfdens.png
    NOTE: ESP is slow — may take a few minutes on larger molecules.

elf_map.txt
    Electron localization function (ELF) color-filled map (XZ plane, Y=0)
    Output: surfdens.png

lol_map.txt
    Localized orbital locator (LOL) color-filled map (XZ plane, Y=0)
    Output: surfdens.png

orbital_plot.txt
    Orbital wavefunction contour map (XZ plane, Y=0)
    ** EDIT LINE 7: change "5" to the orbital number you want **
    Orbitals 1 to N_occupied are occupied; HOMO is the last occupied.
    Output: surfdens.png

------------------------------------------------------------------------
3D CUBE FILES (.cub output, use with PyVista or VMD)
------------------------------------------------------------------------

electron_density_cube.txt
    Electron density grid data
    Output: density.cub

elf_cube.txt
    ELF grid data
    Output: ELF.cub

orbital_cube.txt
    Orbital wavefunction grid data
    ** EDIT LINE 4: change "5" to the orbital number you want **
    Output: orb.cub

------------------------------------------------------------------------
TEXT ANALYSIS (terminal output, redirect with > to save)
------------------------------------------------------------------------

mulliken_charges.txt
    Mulliken population analysis and atomic charges
    Usage: Multiwfn file.molden -silent < mulliken_charges.txt > charges.txt

hirshfeld_charges.txt
    Hirshfeld atomic charges
    Usage: Multiwfn file.molden -silent < hirshfeld_charges.txt > charges.txt

mayer_bond_orders.txt
    Mayer bond order between all atom pairs
    Usage: Multiwfn file.molden -silent < mayer_bond_orders.txt > bonds.txt

------------------------------------------------------------------------
NOTES
------------------------------------------------------------------------

- All 2D maps plot the XZ plane at Y=0 by default. If your molecule is
  not in this plane, change line 6 from "2" (XZ) to:
    1 = XY plane  2 = XZ plane  3 = YZ plane

- Grid quality is set to default (200x200) for 2D maps and medium
  quality for 3D cube files. For higher quality cube files change
  line 3 from "2" to "3" (slower but finer isosurfaces).

- Output PNG filenames are controlled by Multiwfn internally.
  Common names: surfdens.png, ELF.png, orb.png
  Always check with: ls *.png after running.
