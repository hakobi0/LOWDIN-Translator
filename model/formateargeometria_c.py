"""
formateargeometria.py
Genera el contenido de un archivo .lowdin para openLOWDIN.

Formato de cada línea en GEOMETRY:
  particle_name  basis_set  x  y  z  [addParticles=N]  [multiplicity=M]

Orden en GEOMETRY:
  1. Líneas de electrones  e-(SYMBOL)
  2. Líneas de positrones  e+
  3. Líneas de núcleos     SYMBOL  dirac / SYMBOL  basis (APMO)
"""

# Tabla de números atómicos para calcular addParticles correcto
ATOMIC_NUMBERS = {
    'H': 1, 'He': 2, 'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8,
    'F': 9, 'Ne': 10, 'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15,
    'S': 16, 'Cl': 17, 'Ar': 18, 'K': 19, 'Ca': 20, 'Sc': 21, 'Ti': 22,
    'V': 23, 'Cr': 24, 'Mn': 25, 'Fe': 26, 'Co': 27, 'Ni': 28, 'Cu': 29,
    'Zn': 30, 'Ga': 31, 'Ge': 32, 'As': 33, 'Se': 34, 'Br': 35, 'Kr': 36,
    'Rb': 37, 'Sr': 38, 'I': 53, 'Xe': 54,
}


class formatear_geometria():

    def __init__(self, geometria_bruta, base_elec, base_proton, base_positron,
                 multiplicidad, carga, metodo_real, titulo):
        """
        Parameters
        ----------
        geometria_bruta : str
            Geometría en formato XYZ (sin cabecera), e.g.  "O 0.0 0.0 0.11\nH ..."
        base_elec : str
            Nombre del conjunto de bases electrónico, e.g. "6-311G"
        base_proton : str
            Base para núcleos cuánticos (APMO). Usar "dirac" para núcleos clásicos.
        base_positron : str
            Base para positrones, e.g. "PSX-TZ"
        multiplicidad : int / str
            Multiplicidad global del sistema (1=singlete, 2=doblete, …)
        carga : int / str
            Carga total del sistema (entero, puede ser negativo)
        metodo_real : str
            Método computacional: "RHF", "UHF", "MP2", "RKS", "UKS",
            "LDA", "PBE", "BLYP", "B3LYP", "PBE0"
        titulo : str
            Descripción del sistema.
        """
        self.geometria_bruta  = geometria_bruta
        self.base_elec        = base_elec
        self.base_proton      = base_proton
        self.base_positron    = base_positron
        self.multiplicidad    = int(multiplicidad)
        self.carga            = int(carga)
        self.metodo_real      = metodo_real
        self.titulo           = titulo

        # Opciones adicionales
        self.control_options = []   # lista de strings "key=value"
        self.output_options  = []   # lista de strings "key=value" / flags

        # Partículas parseadas
        self.atomos    = []   # lista de tuplas (simbolo, x, y, z)
        self.electrones = []  # líneas ya formateadas
        self.positrones = []
        self.protones   = []

        self.geometria_formateada  = ""
        self.geometria_indentada   = ""

        # Método real para el bloque TASKS
        # Para DFT determinamos RKS vs UKS según multiplicidad
        self._dft_functionals = {"LDA", "PBE", "BLYP", "B3LYP", "PBE0"}
        self._metodo_tasks = self._resolver_metodo_tasks()

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    def _resolver_metodo_tasks(self):
        """Devuelve el string que va en method = "..." del bloque TASKS."""
        if self.metodo_real == "FOCK":
            return "UHF" if self.multiplicidad > 1 else "RHF"
        if self.metodo_real in self._dft_functionals:
            return "UKS" if self.multiplicidad > 1 else "RKS"
        if self.metodo_real == "MP2":
            return "UHF" if self.multiplicidad > 1 else "RHF"
        return self.metodo_real  # RHF, UHF, RKS, UKS explícitos

    def _add_particles_str(self, simbolo, add, mult):
        """
        Construye la parte opcional '  addParticles=N  multiplicity=M'
        solo cuando los valores no son los predeterminados (0 y 1).
        """
        partes = []
        if add != 0:
            partes.append(f"addParticles={add:+d}")
        if mult != 1:
            partes.append(f"multiplicity={mult}")
        return ("  " + "  ".join(partes)) if partes else ""

    # ------------------------------------------------------------------
    # API pública para agregar partículas
    # ------------------------------------------------------------------

    def agregar_protones(self):
        """
        Parsea geometria_bruta (formato XYZ sin cabecera) y genera las
        líneas de núcleos. Usa self.base_proton como base; si es 'dirac'
        los núcleos son puntuales (clásicos), de lo contrario son APMO.
        """
        lineas = self.geometria_bruta.strip().split('\n')
        contador_por_simbolo = {}  # para sufijos -a_N, -b_N en APMO

        for linea in lineas:
            partes = linea.split()
            if len(partes) < 4:
                continue
            simbolo = partes[0].capitalize()
            x, y, z = float(partes[1]), float(partes[2]), float(partes[3])
            self.atomos.append((simbolo, x, y, z))

            if self.base_proton.lower() == "dirac":
                # Núcleo puntual clásico
                linea_nuc = "{:<6} {:<20} {:>12.6f} {:>12.6f} {:>12.6f}".format(
                    simbolo, "dirac", x, y, z
                )
            else:
                # Núcleo cuántico APMO — necesita sufijo único
                cnt = contador_por_simbolo.get(simbolo, 0)
                sufijo = chr(ord('a') + cnt)
                contador_por_simbolo[simbolo] = cnt + 1
                nombre_nuc = f"{simbolo}-{sufijo}_1"
                linea_nuc = "{:<12} {:<20} {:>12.6f} {:>12.6f} {:>12.6f}".format(
                    nombre_nuc, self.base_proton, x, y, z
                )

            self.protones.append(linea_nuc)

    def agregar_electrones(self, simbolo, x, y, z, add_particles=0, multiplicidad=1):
        """
        Agrega UNA línea de electrones para el átomo con símbolo 'simbolo'.

        Parameters
        ----------
        simbolo : str
            Símbolo del elemento, e.g. "O", "H"
        x, y, z : float
            Coordenadas en Angstroms
        add_particles : int
            Corrección sobre el número atómico (negativo = quitar electrones)
        multiplicidad : int
            Multiplicidad local del centro (1 para centros cerrados)
        """
        extra = self._add_particles_str(simbolo, add_particles, multiplicidad)
        linea = "{:<10} {:<20} {:>12.6f} {:>12.6f} {:>12.6f}{}".format(
            f"e-({simbolo})", self.base_elec, float(x), float(y), float(z), extra
        )
        self.electrones.append(linea)

    def agregar_electrones_desde_atomos(self):
        """
        Método de conveniencia: genera una línea de electrones por cada átomo
        en self.atomos (que debe haberse llenado con agregar_protones() antes).

        Distribuye la carga total (self.carga) sobre el átomo más pesado,
        y ajusta la multiplicidad global si es necesario.
        """
        if not self.atomos:
            return

        # Átomo más pesado (mayor número atómico) recibe la corrección de carga
        def peso(sim):
            return ATOMIC_NUMBERS.get(sim, 0)

        atomos_ordenados = sorted(self.atomos, key=lambda a: peso(a[0]), reverse=True)
        atomo_principal = atomos_ordenados[0][0]

        # Cálculo de electrones totales y paridad
        total_e = sum(ATOMIC_NUMBERS.get(s, 0) for s, *_ in self.atomos) - self.carga
        open_shell = (total_e % 2 != 0) or (self.multiplicidad > 1)

        for i, (simbolo, x, y, z) in enumerate(self.atomos):
            add = 0
            mult_local = 1
            if simbolo == atomo_principal and i == 0:
                # Aquí aplicamos la corrección de carga total
                add = -self.carga
                if open_shell:
                    mult_local = self.multiplicidad
            self.agregar_electrones(simbolo, x, y, z,
                                    add_particles=add,
                                    multiplicidad=mult_local)

    def agregar_positrones(self, x, y, z, add_particles=0):
        """
        Agrega UNA línea de positrones en la posición dada.

        Parameters
        ----------
        add_particles : int
            Normalmente 0 (un positrón). Usar -1 para centros fantasma.
        """
        extra = self._add_particles_str("e+", add_particles, 1)
        linea = "{:<6} {:<20} {:>12.6f} {:>12.6f} {:>12.6f}{}".format(
            "e+", self.base_positron, float(x), float(y), float(z), extra
        )
        self.positrones.append(linea)

    # Alias para compatibilidad con el nombre anterior
    def agregar_particulas(self, n, x, y, z):
        """Agrega n líneas de positrones (add_particles=0 por defecto)."""
        for _ in range(n):
            self.agregar_positrones(x, y, z)

    # ------------------------------------------------------------------
    # Construcción del bloque GEOMETRY
    # ------------------------------------------------------------------

    def formatear_geometria(self):
        """
        Une electrones → positrones → protones y aplica indentación con tabs.
        Devuelve geometria_formateada (sin indentar).
        """
        partes = []
        if self.electrones:
            partes.append("\n".join(self.electrones))
        if self.positrones:
            partes.append("\n".join(self.positrones))
        if self.protones:
            partes.append("\n".join(self.protones))

        self.geometria_formateada = "\n".join(partes)

        self.geometria_indentada = "\n".join(
            "\t" + linea for linea in self.geometria_formateada.split("\n")
        )
        return self.geometria_formateada

    # ------------------------------------------------------------------
    # Bloques auxiliares
    # ------------------------------------------------------------------

    def _bloque_tasks(self):
        lines = [f'\tmethod = "{self._metodo_tasks}"']
        if self.metodo_real == "MP2":
            lines.append("\tmollerPlessetCorrection = 2")
        return "\n".join(lines)

    def _bloque_control(self):
        if not self.control_options:
            return ""
        lineas = ["\t" + opt for opt in self.control_options]
        if self.metodo_real in self._dft_functionals:
            lineas.insert(0, f'\telectronExchangeCorrelationFunctional = "{self.metodo_real}"')
        return "\n".join(lineas)

    def _bloque_outputs(self):
        if not self.output_options:
            return ""
        return "\n".join("\t" + opt for opt in self.output_options)

    # ------------------------------------------------------------------
    # Generación del archivo completo
    # ------------------------------------------------------------------

    def crear_input_lowdin(self):
        """
        Genera el string completo del archivo .lowdin.
        Llama internamente a formatear_geometria() si aún no se ha hecho.
        """
        if not self.geometria_indentada:
            self.formatear_geometria()

        bloque_ctrl = self._bloque_control()
        ctrl_section = f"\nCONTROL\n{bloque_ctrl}\nEND CONTROL" if bloque_ctrl else \
                       "\nCONTROL\nEND CONTROL"

        bloque_out = self._bloque_outputs()
        out_section = f"\nOUTPUTS\n{bloque_out}\nEND OUTPUTS" if bloque_out else ""

        # Escape title to avoid shell special characters issues (but keep quotes)
        safe_titulo = self.titulo.replace("'", "").replace('"', '').replace('!', '').replace('\\', '')

        return (
            f"SYSTEM_DESCRIPTION='{safe_titulo}'\n"
            f"\nGEOMETRY\n{self.geometria_indentada}\nEND GEOMETRY\n"
            f"\nTASKS\n{self._bloque_tasks()}\nEND TASKS\n"
            f"{ctrl_section}\n"
            f"{out_section}\n"
        ).rstrip() + "\n"
