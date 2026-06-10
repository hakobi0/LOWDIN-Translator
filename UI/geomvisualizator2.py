import numpy as np
from PyQt6 import QtCore, QtWidgets
from pyvistaqt import QtInteractor
import pyvista as pv

from UI.geomvisualizator import Ui_Form

ELEMENT_COLORS = {
    'H': 'white', 'C': 'gray', 'N': 'blue', 'O': 'red',
    'F': 'green', 'Cl': 'green', 'S': 'yellow', 'P': 'orange',
    'B': 'pink', 'Si': 'tan', 'Br': 'darkred', 'I': 'purple',
}

ELEMENT_RADII = {
    'H': 0.25, 'C': 0.4, 'N': 0.38, 'O': 0.35,
    'F': 0.3, 'Cl': 0.45, 'S': 0.5, 'P': 0.47,
    'B': 0.42, 'Si': 0.55, 'Br': 0.5, 'I': 0.55,
}

COVALENT_RADII = {
    'H': 0.31, 'C': 0.76, 'N': 0.71, 'O': 0.66,
    'F': 0.57, 'Cl': 0.99, 'S': 1.05, 'P': 1.07,
    'B': 0.84, 'Si': 1.11, 'Br': 1.14, 'I': 1.33,
}

BOND_TOLERANCE = 0.45


def _max_bond_distance(elem1, elem2):
    r1 = COVALENT_RADII.get(elem1, 0.77)
    r2 = COVALENT_RADII.get(elem2, 0.77)
    return r1 + r2 + BOND_TOLERANCE


class GeometryVisualizator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowTitle("Geometry Visualizer")

        self.plotter = self.ui.pyvista_widget
        self.plotter.set_background('black')

    def plot_geometry(self, geometry):
        self.plotter.clear()
        self.plotter.set_background('black')

        for element, x, y, z in geometry:
            radius = ELEMENT_RADII.get(element, 0.35)
            color = ELEMENT_COLORS.get(element, 'lightgray')
            sphere = pv.Sphere(center=(x, y, z), radius=radius)
            self.plotter.add_mesh(sphere, color=color, smooth_shading=True)

        n = len(geometry)
        for i in range(n):
            e1, x1, y1, z1 = geometry[i]
            for j in range(i + 1, n):
                e2, x2, y2, z2 = geometry[j]
                dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
                if 0.1 < dist < _max_bond_distance(e1, e2):
                    start = np.array([x1, y1, z1])
                    end = np.array([x2, y2, z2])
                    line = pv.Line(start, end)
                    self.plotter.add_mesh(line.tube(radius=0.06), color='darkgray')

        self.plotter.reset_camera()

    def closeEvent(self, event):
        self.plotter.close()
        super().closeEvent(event)
