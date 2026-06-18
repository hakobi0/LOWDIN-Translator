import re
from model import variablesglobales
from model.basisnormalizer import resolve_basis
from model.zmatrix_parser import ZMatrixParser, is_zmatrix

class Parser:
    def __init__(self, contenido):
        self.contenido = contenido
        self.formato = self.detectar_formato()

    def detectar_formato(self):
        lineas = self.contenido.strip().split('\n')

        # Check for Z-matrix first (before XYZ)
        if is_zmatrix(self.contenido):
            return "zmatrix"

        try:
            int(lineas[0].strip())
            return "xyz"
        except ValueError:
            pass

        if "CARTESIAN COORDINATES (ANGSTROEM)" in self.contenido:
            return "orca"

        if "INPUT FILE" in self.contenido or "PrintBasis" in self.contenido:
            return "gaussian"

        return "unknown"

    def extraer_geometria_optimizada(self):
        # Z-matrix
        if self.formato == "zmatrix":
            try:
                parser = ZMatrixParser(self.contenido)
                cartesian = parser.parse()
                # Convert to geometry string
                geo_lines = []
                for symbol, x, y, z in cartesian:
                    geo_lines.append(f"{symbol}  {x:.6f}  {y:.6f}  {z:.6f}")
                geo = "\n".join(geo_lines)
                self.geometria_bruta = geo
                return geo
            except Exception as e:
                print(f"Error parsing Z-matrix: {e}")
                return "GEOMETRY_NOT_FOUND"

        # XYZ
        if self.formato == "xyz":
            lineas = self.contenido.strip().split("\n")
            try:
                n = int(lineas[0])
                geo = "\n".join(lineas[2:2+n])
                self.geometria_bruta = geo
                return geo
            except:
                pass

        # Gaussian
        patron_gaussian = r"CARTESIAN COORDINATES \(ANGSTROEM\).*?\n-+\n(.*?)(?:\n\s*\n|\Z)"
        matches = re.findall(patron_gaussian, self.contenido, re.DOTALL)
        if matches:
            self.geometria_bruta = matches[-1].strip()
            return matches[-1].strip()

        # ORCA
        patron_orca = r"\* xyz .*?\n(.*?)\n\*"
        matches = re.findall(patron_orca, self.contenido, re.DOTALL)
        if matches:
            self.geometria_bruta = matches[-1].strip()
            return matches[-1].strip()

        return "GEOMETRY_NOT_FOUND"

    def extraer_atomos(self):
        if self.geometria_bruta:
            atomos = []
            for linea in self.geometria_bruta.split('\n'):
                partes = linea.split()
                if len(partes) >= 4:
                    atomos.append((
                        partes[0].capitalize(),
                        float(partes[1]),
                        float(partes[2]),
                        float(partes[3])
                    ))
            return atomos

    def extraer_base(self):
        # ORCA: basis set appears on the ! keyword line, e.g. "! RHF def2-TZVP Opt"
        if self.formato == "orca":
            match = re.search(r"!\s*(.+)", self.contenido)
            if match:
                partes = match.group(1).split()
                skip = {
                    "OPT", "FREQ", "NUMFREQ", "TIGHTSCF", "LOOSEOPT",
                    "NORMALOPT", "TIGHTOPT", "VERYTIGHTSCF", "LARGEPRINT",
                    "MINIPRINT", "NOPRINT", "CPCM", "SMD", "RI", "NORI",
                    "RIJCOSX", "NOPOP", "SLOWCONV", "VERYSLOWCONV",
                }
                for p in partes:
                    upper = p.upper()
                    if upper in skip:
                        continue
                    # Skip if it looks like a method keyword
                    if upper in {k.upper() for k in variablesglobales.valid_methods}:
                        continue
                    resolved, matched = resolve_basis(p)
                    if matched:
                        return resolved

        # Gaussian: PrintBasis line
        match = re.search(r"PrintBasis\s+(.+)", self.contenido)
        if match:
            base = match.group(1).strip()
            resolved, _ = resolve_basis(base)
            return resolved

        if self.formato == "xyz":
            return "NONE"

        return "NONE"

    def extraer_multiplicidad_carga(self):
        match = re.search(r"\*\s*xyz\s+(-?\d+)\s+(\d+)", self.contenido)
        if match:
            return int(match.group(1)), int(match.group(2))

        if self.formato == "xyz":
            return 0, 1

        return None

    def extraer_metodo_real(self):
        marcador_inicio = "INPUT FILE"

        if marcador_inicio in self.contenido:
            seccion_input = self.contenido[self.contenido.find(marcador_inicio):]
        else:
            seccion_input = self.contenido

        match = re.search(r'!\s*(.+)', seccion_input)

        if match:
            partes = match.group(1).upper().split()

            for palabra in partes:
                if palabra != "OPT":   # más limpio
                    return variablesglobales.valid_methods.get(palabra, palabra)

        if self.formato == "xyz":
            return "METHOD_NOT_FOUND"

        return "METHOD_NOT_FOUND"

    def parsear(self):
        return {
            "geometria_bruta": self.extraer_geometria_optimizada(),
            "atomos": self.extraer_atomos(),
            "base_elec": self.extraer_base(),
            "base_proton": self.extraer_base(),
            "base_positron": self.extraer_base(),
            "multiplicidad": self.extraer_multiplicidad_carga()[1] if self.extraer_multiplicidad_carga() else None,
            "carga": self.extraer_multiplicidad_carga()[0] if self.extraer_multiplicidad_carga() else None,
            "metodo_real": self.extraer_metodo_real(),
            "titulo": "Input Generado con LOWDIN-Translator"
        }
