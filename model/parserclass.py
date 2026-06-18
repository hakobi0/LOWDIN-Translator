import re
from model import variablesglobales
from model.basisnormalizer import resolve_basis
from model.zmatrix_parser import ZMatrixParser, is_zmatrix

class Parser:
    def __init__(self, contenido):
        self.contenido = contenido
        self.geometria_bruta = None   # always initialised; set by extraer_geometria_optimizada
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

        # "* xyz" with a charge/mult pair is an ORCA input file
        if re.search(r'^\s*\*\s*xyz\s+-?\d+\s+\d+', self.contenido, re.MULTILINE):
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
                geo_lines = [f"{symbol}  {x:.6f}  {y:.6f}  {z:.6f}"
                             for symbol, x, y, z in cartesian]
                geo = "\n".join(geo_lines)
                self.geometria_bruta = geo
                return geo
            except Exception as e:
                print(f"Error parsing Z-matrix: {e}")
                self.geometria_bruta = "GEOMETRY_NOT_FOUND"
                return "GEOMETRY_NOT_FOUND"

        # XYZ
        if self.formato == "xyz":
            lineas = self.contenido.strip().split("\n")
            try:
                n = int(lineas[0].strip())
                geo = "\n".join(lineas[2:2+n])
                self.geometria_bruta = geo
                return geo
            except Exception:
                self.geometria_bruta = "GEOMETRY_NOT_FOUND"
                return "GEOMETRY_NOT_FOUND"

        # ORCA output: last CARTESIAN COORDINATES block (final optimised geometry)
        patron_orca_out = r"CARTESIAN COORDINATES \(ANGSTROEM\).*?\n-+\n(.*?)(?:\n\s*\n|\Z)"
        matches = re.findall(patron_orca_out, self.contenido, re.DOTALL)
        if matches:
            self.geometria_bruta = matches[-1].strip()
            return self.geometria_bruta

        # ORCA input: inline geometry between "* xyz ..." and closing "*"
        patron_orca_inp = r"\*\s*xyz\s+-?\d+\s+\d+\s*\n(.*?)\n\s*\*"
        matches = re.findall(patron_orca_inp, self.contenido, re.DOTALL)
        if matches:
            self.geometria_bruta = matches[-1].strip()
            return self.geometria_bruta

        self.geometria_bruta = "GEOMETRY_NOT_FOUND"
        return "GEOMETRY_NOT_FOUND"

    def extraer_atomos(self):
        geo = self.geometria_bruta
        if not geo or geo == "GEOMETRY_NOT_FOUND":
            return []
        atomos = []
        for linea in geo.split('\n'):
            partes = linea.split()
            if len(partes) >= 4:
                try:
                    atomos.append((
                        partes[0].capitalize(),
                        float(partes[1]),
                        float(partes[2]),
                        float(partes[3])
                    ))
                except ValueError:
                    continue
        return atomos

    def extraer_base(self):
        # ORCA: basis set appears on a "! ..." keyword line, e.g. "! RHF def2-TZVP Opt"
        # There may be multiple "!" lines; scan all of them for the first recognised basis.
        if self.formato in ("orca",):
            for m in re.finditer(r"^[^!]*!\s*(.+)", self.contenido, re.MULTILINE):
                partes = m.group(1).split()
                skip = {
                    "OPT", "FREQ", "NUMFREQ", "TIGHTSCF", "LOOSEOPT",
                    "NORMALOPT", "TIGHTOPT", "VERYTIGHTSCF", "LARGEPRINT",
                    "MINIPRINT", "NOPRINT", "CPCM", "SMD", "RI", "NORI",
                    "RIJCOSX", "NOPOP", "SLOWCONV", "VERYSLOWCONV",
                    "PRINTBASIS",
                }
                valid_methods_upper = {k.upper() for k in variablesglobales.valid_methods}
                for p in partes:
                    upper = p.upper()
                    if upper in skip or upper in valid_methods_upper:
                        continue
                    resolved, matched = resolve_basis(p)
                    if matched:
                        return resolved

        # Gaussian / ORCA-as-gaussian: "PrintBasis <name>" on its own line
        m = re.search(r"PrintBasis\s+(\S+)", self.contenido, re.IGNORECASE)
        if m:
            resolved, _ = resolve_basis(m.group(1).strip())
            return resolved

        return "NONE"

    def extraer_multiplicidad_carga(self):
        # ORCA: "* xyz <charge> <mult>"
        m = re.search(r"\*\s*xyz\s+(-?\d+)\s+(\d+)", self.contenido)
        if m:
            return int(m.group(1)), int(m.group(2))

        if self.formato in ("xyz", "zmatrix"):
            return 0, 1

        return None

    def extraer_metodo_real(self):
        # Search from "INPUT FILE" marker if present, else whole content
        if "INPUT FILE" in self.contenido:
            seccion = self.contenido[self.contenido.find("INPUT FILE"):]
        else:
            seccion = self.contenido

        # All "! ..." lines (handles both bare input and echoed input in output)
        for m in re.finditer(r"^[^!]*!\s*(.+)", seccion, re.MULTILINE):
            partes = m.group(1).upper().split()
            for palabra in partes:
                if palabra in ("OPT", "FREQ", "NUMFREQ", "PRINTBASIS"):
                    continue
                mapped = variablesglobales.valid_methods.get(palabra)
                if mapped:
                    return mapped

        if self.formato in ("xyz", "zmatrix"):
            return "METHOD_NOT_FOUND"

        return "METHOD_NOT_FOUND"

    def parsear(self):
        geo = self.extraer_geometria_optimizada()   # sets self.geometria_bruta
        charge_mult = self.extraer_multiplicidad_carga()
        carga      = charge_mult[0] if charge_mult else None
        mult       = charge_mult[1] if charge_mult else None
        base       = self.extraer_base()

        return {
            "geometria_bruta":  geo,
            "atomos":           self.extraer_atomos(),
            "base_elec":        base,
            "base_proton":      base,
            "base_positron":    base,
            "multiplicidad":    mult,
            "carga":            carga,
            "metodo_real":      self.extraer_metodo_real(),
            "titulo":           "Input Generado con LOWDIN-Translator"
        }
