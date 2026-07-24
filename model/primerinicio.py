from pathlib import Path
import os

from model.basisclassifier import electronic_basis_names

class PrimerInicio:

    def __init__(self): # verificación inicial
        self.ruta_config = Path.home() / ".config" / "lowdintranslator"
        self.config_file = self.ruta_config / "config.ini"
        self.ruta_config.mkdir(parents=True, exist_ok=True)
        if not self.config_file.exists():
            self.config_file.touch()

        self.basis = []
        self.encontrar_openlowdin()
        self.buscar_bases()


    def encontrar_openlowdin(self):  # busca si el ejecutable de openlowdin esta instalado
        lugares_comunes = [
            "~/bin/openlowdin",
            "~/.local/bin/openlowdin",
            "/usr/bin/openlowdin",
            "/usr/local/bin/openlowdin",
            "/opt/openlowdin/bin/openlowdin",
            "/opt/lowdin/bin/openlowdin",
        ]

        contenido = self.config_file.read_text()
        if "executable_path=" in contenido:
            print("la ruta ya esta en su archivo de configuración")
        else:
            for lugar in lugares_comunes:
                ruta = Path(lugar).expanduser()
                if ruta.is_file() and os.access(ruta, os.X_OK):
                    with self.config_file.open("a") as f:
                        f.write(f"executable_path={ruta}\n")
                    break  # para de buscar al encontrar el ejecutable
            else:
                print("no se encontró el ejecutable, compruebe su instalación de openlowdin")

    def buscar_bases(self):
        ruta = Path('~/openLOWDIN/lib/basis').expanduser()

        if not ruta.exists():
            print("la ruta no existe:", ruta)
            return

        # 1. bases nuevas desde el sistema
        bases_nuevas = [archivo.name for archivo in ruta.iterdir() if archivo.is_file()]

        # 2. leer contenido actual
        contenido = self.config_file.read_text()
        bases_existentes = []

        # 3. extraer bases
        for linea in contenido.splitlines():
            if linea.startswith("bases="):
                bases_existentes = linea.split("=")[1].split(",")

        # 4. combinar y eliminar duplicados
        self.bases_finales = list(set(bases_existentes + bases_nuevas))
        self.all_basis = self.bases_finales

        # 4b. la lista electronica (para el desplegable de base electronica) se
        #     clasifica por contenido: solo bases electronicas, sin positronicas,
        #     nucleares ni muonicas
        self.basis = electronic_basis_names(ruta)
        if not self.basis:
            # si la clasificacion no encontro nada (formato inesperado), no
            # dejar el desplegable vacio: usar la lista completa como respaldo
            self.basis = self.bases_finales

        # 5. reconstruir contenido del archivo
        nuevas_lineas = []
        for linea in contenido.splitlines():
            if not linea.startswith("bases="):
                nuevas_lineas.append(linea)

        bases_str = ",".join(self.bases_finales)
        nuevas_lineas.append(f"bases={bases_str}")
        self.config_file.write_text("\n".join(nuevas_lineas) + "\n")

    def find_test(self):
        ruta = Path('~/openLOWDIN/lib/test').expanduser()
        if not ruta.exists():
            print("la carpeta de test no existe, revise que openLOWDIN este instalado:", ruta)

    def __str__(self):
        return f"Bases detectadas: {', '.join(self.basis)}"



init = PrimerInicio()