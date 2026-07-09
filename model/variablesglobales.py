NUMERO_ATOMICO = {
    'H': 1,  'He': 2, 'Li': 3,  'Be': 4,  'B': 5,
    'C': 6,  'N': 7,  'O': 8,   'F': 9,   'Ne': 10,
    'Na': 11,'Mg': 12,'Al': 13, 'Si': 14, 'P': 15,
    'S': 16, 'Cl': 17,'Ar': 18, 'K': 19,  'Ca': 20,
    'Sc': 21,'Ti': 22,'V': 23,  'Cr': 24, 'Mn': 25,
    'Fe': 26,'Co': 27,'Ni': 28, 'Cu': 29, 'Zn': 30,
    'Ga': 31,'Ge': 32,'As': 33, 'Se': 34, 'Br': 35,
    'Kr': 36,'Rb': 37,'Sr': 38, 'Y': 39,  'Zr': 40,
    'Nb': 41,'Mo': 42,'Tc': 43, 'Ru': 44, 'Rh': 45,
    'Pd': 46,'Ag': 47,'Cd': 48, 'In': 49, 'Sn': 50,
    'Sb': 51,'Te': 52,'I': 53,  'Xe': 54, 'Cs': 55,
    'Ba': 56,'La': 57,'Ce': 58, 'Pr': 59, 'Nd': 60,
    'Pm': 61,'Sm': 62,'Eu': 63, 'Gd': 64, 'Tb': 65,
    'Dy': 66,'Ho': 67,'Er': 68, 'Tm': 69, 'Yb': 70,
    'Lu': 71,'Hf': 72,'Ta': 73, 'W': 74,  'Re': 75,
    'Os': 76,'Ir': 77,'Pt': 78, 'Au': 79, 'Hg': 80,
    'Tl': 81,'Pb': 82,'Bi': 83, 'Po': 84, 'At': 85,
    'Rn': 86,'Fr': 87,'Ra': 88, 'Ac': 89, 'Th': 90,
    'Pa': 91,'U': 92,
}

ATOMIC_WEIGHT = {
    'H': 1.008,    # Hidrógeno
    'He': 4.0026,  # Helio
    'Li': 6.94,    # Litio
    'B': 10.81,    # Boro
    'C': 12.011,   # Carbono
    'N': 14.007,   # Nitrógeno
    'O': 15.999,   # Oxígeno
    'F': 18.998,   # Flúor
    'Ne': 20.180,  # Neón
    'Na': 22.990,  # Sodio
    'Mg': 24.305,  # Magnesio
    'Al': 26.982,  # Aluminio
    'Si': 28.085,  # Silicio
    'P': 30.974,   # Fósforo
    'S': 32.06,    # Azufre
    'Cl': 35.45,   # Cloro
    'Ar': 39.948,  # Argón
    'K': 39.098,   # Potasio
    'Ca': 40.078,  # Calcio
    'Cr': 51.996,  # Cromo
    'Mn': 54.938,  # Manganeso
    'Fe': 55.845,  # Hierro
    'Co': 58.933,  # Cobalto
    'Ni': 58.693,  # Níquel
    'Cu': 63.546,  # Cobre
    'Zn': 65.38,   # Zinc
    'As': 74.922,  # Arsénico
    'Se': 78.971,  # Selenio
    'Br': 79.904,  # Bromo
    'Sr': 87.62,   # Estroncio
    'Zr': 91.224,  # Zirconio
    'Mo': 95.95,   # Molibdeno
    'Ru': 101.07,  # Rutenio
    'Rh': 102.91,  # Rodio
    'Pd': 106.42,  # Paladio
    'Ag': 107.87,  # Plata
    'Cd': 112.41,  # Cadmio
    'In': 114.82,  # Indio
    'Sn': 118.71,  # Estaño
    'Sb': 121.76,  # Antimonio
    'Te': 127.60,  # Telurio
    'I': 126.90,   # Yodo
    'Ba': 137.33,  # Bario
    'W': 183.84,   # Wolframio
    'Re': 186.21,  # Renio
    'Os': 190.23,  # Osmio
    'Ir': 192.22,  # Iridio
    'Pt': 195.08,  # Platino
    'Au': 196.97,  # Oro
    'Hg': 200.59,  # Mercurio
    'Pb': 207.2,   # Plomo
    'Bi': 208.98,  # Bismuto
    'Th': 232.04,  # Torio
    'U': 238.03,   # Uranio
}

ATOM_CHOICES = [
    "H",
    "C",
    "N",
    "O",
    "F",
    "P",
    "S",
    "Cl",
    "Br",
    "I",
]


valid_methods = {   # Para remplazar los métodos que son invalidos en LOWDIN pero validos en ORCA / Guassian
    "HF":"RHF",
    "UHF":"UHF",
    "RKS":"RKS",
    "UKS":"UKS",
    "FOCK":"FOCK",
    "LDA":"LDA",
    "PBE":"PBE",
    "BLYP":"BLYP",
    "B3LYP":"B3LYP",
    "PBE0":"PBE0",
    "MP2":"MP2",
    "MM":"MM"
}

valid_basis = {
    "3-21G": "3-21G",
    "3-21++G": "3-21++G",
    "3-21G(d)": "3-21G.D",
    "3-21++G(d)": "3-21++G.D",
    "4-31G": "4-31G",
    "6-31G": "6-31G",
    "6-31++G": "6-31++G",
    "6-31G(d)": "6-31G.D",
    "6-31+G(d)": "6-31+G.D",
    "6-31++G(d)": "6-31++G.D",
    "6-31G(d,p)": "6-31G.D.P",
    "6-31++G(d,p)": "6-31++G.D.P",
    "6-31G(3df,3pd)": "6-31G.3DF.3PD",
    "6-311G": "6-311G",
    "6-311+G(d)": "6-311+G.D",
    "6-311G(d)": "6-311G.D",
    "6-311G(d,p)": "6-311G.D.P",
    "6-311++G(d,p)": "6-311++G.D.P",
    "6-311++G(2d,2p)": "6-311++G.2D.2P",
    "6-311G(2df,2pd)": "6-311G.2DF.2PD",
    "6-311++G(3df,3pd)": "6-311++G.3DF.3PD",
    "ANO-RCC": "ANO-RCC",
    "aug-cc-pVDZ": "AUG-CC-PVDZ",
    "aug-cc-pVTZ": "AUG-CC-PVTZ",
    "aug-cc-pVQZ": "AUG-CC-PVQZ",
    "aug-cc-pV5Z": "AUG-CC-PV5Z",
    "aug-cc-pV6Z": "AUG-CC-PV6Z",
    "cc-pVDZ": "CC-PVDZ",
    "cc-pVTZ": "CC-PVTZ",
    "cc-pVQZ": "CC-PVQZ",
    "cc-pV5Z": "CC-PV5Z",
    "cc-pV6Z": "CC-PV6Z",
    "cc-pCVDZ": "CC-PCVDZ",
    "cc-pCVTZ": "CC-PCVTZ",
    "cc-pCVQZ": "CC-PCVQZ",
    "aug-cc-pCVDZ": "AUG-CC-PCVDZ",
    "aug-cc-pCVTZ": "AUG-CC-PCVTZ",
    "def2-TZVP": "DEF2-TZVP",
    "def2-TZVPPD": "DEF2-TZVPPD",
    "MINI": "MINI",
    "MINIS": "MINI.SCALED",
    "MIDI": "MIDI.HUZINAGA",
    "pc-0": "PC-0",
    "pc-1": "PC-1",
    "pc-2": "PC-2",
    "pc-3": "PC-3",
    "pc-4": "PC-4",
    "STO-3G": "STO-3G",
    "STO-6G": "STO-6G"
}

positron_basis = [
    # Familia E+ (AUG-CC y DEF2 adaptadas)
    "E+-AL-AUG-CC-PV5Z", "E+-AL-AUG-CC-PVDZ", "E+-AL-AUG-CC-PVTZ", "E+-AL-DEF2-TZVPPD-AUX-DIF",
    "E+-AR-AUG-CC-PV5Z", "E+-AR-AUG-CC-PVDZ", "E+-AR-AUG-CC-PVTZ", "E+-AR-DEF2-TZVPPD-AUX-DIF",
    "E+-AS-AUG-CC-PV5Z", "E+-AS-AUG-CC-PVDZ", "E+-AS-AUG-CC-PVTZ", "E+-AS-DEF2-TZVPPD-AUX-DIF",
    "E+AUG-CC-PV5Z", "E+AUG-CC-PVDZ", "E+AUG-CC-PVQZ", "E+AUG-CC-PVTZ",
    "E+-B-AUG-CC-PV5Z", "E+-B-AUG-CC-PVDZ", "E+-B-AUG-CC-PVTZ", "E+-B-D-AUG-CC-PV5Z",
    "E+-B-D-AUG-CC-PVDZ", "E+-B-D-AUG-CC-PVQZ", "E+-B-D-AUG-CC-PVTZ", "E+-B-DEF2-TZVPPD-AUX-DIF",
    "E+-B-DEF2-TZVPPTD", "E+-BE-AUG-CC-PV5Z", "E+-BE-AUG-CC-PVDZ", "E+-BE-AUG-CC-PVTZ",
    "E+-BE-DEF2-TZVPPD-AUX-DIF", "E+-BE-DEF2-TZVPPTD", "E+-BE-S-DEF2-TZVPPD-AUX-DIF",
    "E+-BR-AUG-CC-PV5Z", "E+-BR-AUG-CC-PVDZ", "E+-BR-AUG-CC-PVQZ", "E+-BR-AUG-CC-PVTZ",
    "E+-BR-DEF2-TZVPPD-AUX-DIF", "E+-CA-DEF2-TZVPPD-AUX-DIF", "E+-C-AUG-CC-PV5Z",
    "E+-C-AUG-CC-PVDZ", "E+-C-AUG-CC-PVTZ", "E+-C-D-AUG-CC-PV5Z", "E+-C-D-AUG-CC-PVDZ",
    "E+-C-D-AUG-CC-PVQZ", "E+-C-D-AUG-CC-PVTZ", "E+-C-DEF2-TZVPPD-AUX-DIF", "E+-C-DEF2-TZVPPTD",
    "E+-CL-AUG-CC-PV5Z", "E+-CL-AUG-CC-PVDZ", "E+-CL-AUG-CC-PVTZ", "E+-CL-DEF2-TZVPPD-AUX-DIF",
    "E+-CO-AUG-CC-PV5Z", "E+-CO-AUG-CC-PVDZ", "E+-CO-AUG-CC-PVTZ", "E+-CO-DEF2-TZVPPD-AUX-DIF",
    "E+-CR-AUG-CC-PV5Z", "E+-CR-AUG-CC-PVDZ", "E+-CR-AUG-CC-PVTZ", "E+-CR-DEF2-TZVPPD-AUX-DIF",
    "E+-CU-AUG-CC-PV5Z", "E+-CU-AUG-CC-PVDZ", "E+-CU-AUG-CC-PVTZ", "E+-CU-DEF2-TZVPPD-AUX-DIF",
    "E+-EA--AUG-CC-PVTZ", "E+-E+A-D-AUG-CC-PVTZ", "E+-E+B-D-AUG-CC-PVTZ", "E+-E+-D-AUG-CC-PVDZ",
    "E+-E+-D-AUG-CC-PVQZ", "E+-E+-D-AUG-CC-PVTZ", "E+-F-11S9P7D-AUG-CC-PVDZ", "E+-F-11SPD-AUG-CC-PVDZ",
    "E+-F-13SPD-AUG-CC-PVDZ", "E+-F-3SPD-AUG-CC-PVDZ", "E+-F-5SPD-AUG-CC-PVDZ", "E+-F-7S5P3D-AUG-CC-PVDZ",
    "E+-F-7SP-AUG-CC-PVDZ", "E+-F-7SPD-AUG-CC-PVDZ", "E+-F-9S7P5D-AUG-CC-PVDZ", "E+-F-9SP-AUG-CC-PVDZ",
    "E+-F-9SPD-AUG-CC-PVDZ", "E+-F-AUG-CC-PV5Z", "E+-F-AUG-CC-PVDZ", "E+-F-AUG-CC-PVQZ",
    "E+-F-AUG-CC-PVTZ", "E+-F-D-AUG-CC-PV5Z", "E+-F-D-AUG-CC-PVDZ", "E+-F-D-AUG-CC-PVQZ",
    "E+-F-D-AUG-CC-PVTZ", "E+-F-DEF2-TZVPPD-AUX-DIF", "E+-F-DEF2-TZVPPTD", "E+-FE-AUG-CC-PV5Z",
    "E+-FE-AUG-CC-PVDZ", "E+-FE-AUG-CC-PVTZ", "E+-FE-DEF2-TZVPPD-AUX-DIF", "E+-GA-AUG-CC-PV5Z",
    "E+-GA-AUG-CC-PVDZ", "E+-GA-AUG-CC-PVTZ", "E+-GA-DEF2-TZVPPD-AUX-DIF", "E+-GE-AUG-CC-PV5Z",
    "E+-GE-AUG-CC-PVDZ", "E+-GE-AUG-CC-PVTZ", "E+-GE-DEF2-TZVPPD-AUX-DIF", "E+-H-7S5P3D-AUG-CC-PVTZ",
    "E+-H-7S5P-AUG-CC-PVTZ", "E+-H-7S-AUG-CC-PVTZ", "E+-H-7SP-AUG-CC-PVTZ", "E+-H-7SPD-AUG-CC-PVTZ",
    "E+-H-AUG-CC-PV5Z", "E+-H-AUG-CC-PVDZ", "E+-H-AUG-CC-PVTZ", "E+-H-D-AUG-CC-PV5Z",
    "E+-H-D-AUG-CC-PVDZ", "E+-H-D-AUG-CC-PVQZ", "E+-H-D-AUG-CC-PVTZ", "E+-H-DEF2-TZVPPD-AUX-DIF",
    "E+-H-DEF2-TZVPPTD", "E+-HE-AUG-CC-PV5Z", "E+-HE-AUG-CC-PVDZ", "E+-HE-AUG-CC-PVTZ",
    "E+-HE-D-AUG-CC-PV5Z", "E+-HE-D-AUG-CC-PVDZ", "E+-HE-D-AUG-CC-PVQZ", "E+-HE-D-AUG-CC-PVTZ",
    "E+-HE-DEF2-TZVPPD-AUX-DIF", "E+-H-S-DEF2-TZVPPD-AUX-DIF", "E+-K-DEF2-TZVPPD-AUX-DIF",
    "E+-KR-AUG-CC-PV5Z", "E+-KR-AUG-CC-PVDZ", "E+-KR-AUG-CC-PVTZ", "E+-KR-DEF2-TZVPPD-AUX-DIF",
    "E+-LI-AUG-CC-PV5Z", "E+-LI-AUG-CC-PVDZ", "E+-LI-AUG-CC-PVTZ", "E+-LI-DEF2-TZVPPD-AUX-DIF",
    "E+-LI-DEF2-TZVPPTD", "E+-LI-S-DEF2-TZVPPD-AUX-DIF", "E+-MG-AUG-CC-PV5Z", "E+-MG-AUG-CC-PVDZ",
    "E+-MG-AUG-CC-PVTZ", "E+-MG-DEF2-TZVPPD-AUX-DIF", "E+-MN-AUG-CC-PV5Z", "E+-MN-AUG-CC-PVDZ",
    "E+-MN-AUG-CC-PVTZ", "E+-MN-DEF2-TZVPPD-AUX-DIF", "E+-NA-AUG-CC-PV5Z", "E+-NA-AUG-CC-PVDZ",
    "E+-NA-AUG-CC-PVTZ", "E+-NA-DEF2-TZVPPD-AUX-DIF", "E+-N-AUG-CC-PV5Z", "E+-N-AUG-CC-PVDZ",
    "E+-N-AUG-CC-PVTZ", "E+-N-D-AUG-CC-PV5Z", "E+-N-D-AUG-CC-PVDZ", "E+-N-D-AUG-CC-PVQZ",
    "E+-N-D-AUG-CC-PVTZ", "E+-N-DEF2-TZVPPD-AUX-DIF", "E+-N-DEF2-TZVPPTD", "E+-NE-AUG-CC-PV5Z",
    "E+-NE-AUG-CC-PVDZ", "E+-NE-AUG-CC-PVTZ", "E+-NE-D-AUG-CC-PV5Z", "E+-NE-D-AUG-CC-PVDZ",
    "E+-NE-D-AUG-CC-PVQZ", "E+-NE-D-AUG-CC-PVTZ", "E+-NE-DEF2-TZVPPD-AUX-DIF", "E+-NI-AUG-CC-PV5Z",
    "E+-NI-AUG-CC-PVDZ", "E+-NI-AUG-CC-PVTZ", "E+-NI-DEF2-TZVPPD-AUX-DIF", "E+-O-AUG-CC-PV5Z",
    "E+-O-AUG-CC-PVDZ", "E+-O-AUG-CC-PVTZ", "E+-O-D-AUG-CC-PV5Z", "E+-O-D-AUG-CC-PVDZ",
    "E+-O-D-AUG-CC-PVQZ", "E+-O-D-AUG-CC-PVTZ", "E+-O-DEF2-TZVPPD-AUX-DIF", "E+-O-DEF2-TZVPPTD",
    "E+-OXY-7SPD-AUG-CC-PVDZ", "E+-P-AUG-CC-PV5Z", "E+-P-AUG-CC-PVDZ", "E+-P-AUG-CC-PVTZ",
    "E+-P-DEF2-TZVPPD-AUX-DIF", "E+-S-AUG-CC-PV5Z", "E+-S-AUG-CC-PVDZ", "E+-S-AUG-CC-PVTZ",
    "E+-SC-AUG-CC-PV5Z", "E+-SC-AUG-CC-PVDZ", "E+-SC-AUG-CC-PVTZ", "E+-SC-DEF2-TZVPPD-AUX-DIF",
    "E+-S-DEF2-TZVPPD-AUX-DIF", "E+-SE-AUG-CC-PV5Z", "E+-SE-AUG-CC-PVDZ", "E+-SE-AUG-CC-PVTZ",
    "E+-SE-DEF2-TZVPPD-AUX-DIF", "E+-SI-AUG-CC-PV5Z", "E+-SI-AUG-CC-PVDZ", "E+-SI-AUG-CC-PVTZ",
    "E+-SI-DEF2-TZVPPD-AUX-DIF", "E+-TI-AUG-CC-PV5Z", "E+-TI-AUG-CC-PVDZ", "E+-TI-AUG-CC-PVTZ",
    "E+-TI-DEF2-TZVPPD-AUX-DIF", "E+-V-AUG-CC-PV5Z", "E+-V-AUG-CC-PVDZ", "E+-V-AUG-CC-PVTZ",
    "E+-V-DEF2-TZVPPD-AUX-DIF", "E+-ZN-AUG-CC-PV5Z", "E+-ZN-AUG-CC-PVDZ", "E+-ZN-AUG-CC-PVTZ",
    "E+-ZN-DEF2-TZVPPD-AUX-DIF", "ETE+-11-SPD",
    # Familia PSX (Polarized Species-X para positrones)
    "PSX-DZ", "PSX-QZ", "PSX-TZ",
    # Familias Sharon y Gribakin
    "SHARON-E+6S", "SHARON-E+6S2P", "SHARON-E+6S2P1D", "SHARON-E+6S3P1D",
    "GRIBAKIN", "GRIBAKIN-10S", "GRIBAKIN-10S10P", "GRIBAKIN-10S10P10D", "GRIBAKIN-10S10P7D",
    "GRIBAKIN-10S1P", "GRIBAKIN-10S3P", "GRIBAKIN-10S4P2D", "GRIBAKIN-10S5P",
    "GRIBAKIN-1S", "GRIBAKIN-4S", "GRIBAKIN-5S"
]

nuclear_basis =  [
    "dirac",
    # Familia NAKAI (Nuclear-Electronic Orbitals)
    "NAKAI-13-S", "NAKAI-17-S", "NAKAI-3-S", "NAKAI-3-SP", "NAKAI-3-SPD", "NAKAI-4-S",
    "NAKAI-4-SP", "NAKAI-4-SPD", "NAKAI-5-S", "NAKAI-5-SP", "NAKAI-5-SP-2D", "NAKAI-5-SPD",
    "NAKAI-6-S", "NAKAI-6-SP", "NAKAI-6-SPD", "NAKAI-7-S", "NAKAI-7-S-E", "NAKAI-7-SP",
    "NAKAI-7-SPD", "NAKAI-7-SPD-E", "NAKAI-7-SPD-MP2-EN", "NAKAI-AUG-CC-PVQZ", "NAKAI-CC-PVDZ",
    "NAKAI-CC-PVTZ", "NAKAI-TRF-7SP", "NAKAI-TRF-7SPD", "NAKAI-TRF-7SPD-B",
    # Familia 13S.ET (Distribuciones nucleares por elemento)
    "13S.ET.AL.U.TF", "13S.ET.AR.U.TF", "13S.ET.BE.U.TF", "13S.ET.B.U.TF", "13S.ET.CA.U.TF",
    "13S.ET.CL.U.TF", "13S.ET.C.U.TF", "13S.ET.D.U.TF", "13S.ET.F.U.TF", "13S.ET.HE.U.TF",
    "13S.ET.HLIKE.TF", "13S.ET.H.U.TF", "13S.ET.K.U.TF", "13S.ET.LI.U.TF", "13S.ET.MG.U.TF",
    "13S.ET.NA.U.TF", "13S.ET.NE.U.TF", "13S.ET.N.U.TF", "13S.ET.O.U.TF", "13S.ET.P.U.TF",
    "13S.ET.SI.U.TF", "13S.ET.S.U.TF", "13S.ET.T.U.TF",
    # Otras bases nucleares (He, H, e Ishimoto)
    "ISHIMOTO-H1-1S1P1D", "10S.HE", "25S.HE", "25S12P.HE", "1S.HE.GRID",
    "HE2-1S", "HE2-1S1P", "HE2-1S1P1D", "HE2-1S1P1D1F", "HE2-1S1P1D1F1G",
    "DZSPDN", "DZSPDN-HD", "QZSPDN", "QZSPDD"
]


# Tareas para el metodo RHF/UHF

tareas_HF = ['writeCoefficientsInBinary', 'writeEigenValuesInBinary', 'readCoefficients', 'readCoefficientsInBinary',
             'readEigenValues', 'readEigenValuesInBinary', 'noScf', 'finiteMassCorrection', 'removeTranslationalContamination',
             'buildTwoParticlesMatrixForOneParticle', 'buildMixedDensityMatrix']

tareas_integrales = ['integralStackSize', 'integralScheme']

tareas_SCF = ['scfNonElectronicEnergyTolerance', 'scfElectronicEnergyTolerance', 'nonElectronicDensityMatrixTolerance',
              'nonElectronicDensityMatrixTolerance', 'totalEnergyTolerance', 'scfNonElectronicMaxIterations', 'scfElectronicMaxIterations',
              'scfGlobalMaximumIterations', 'convergenceMethod', 'iterationScheme', 'scfElectronicTypeGuess', 'scfNonElectronicTypeGuess',
              'scfConvergenceCriterium', 'debugScfs']

# MP2 Tasks

MP2_tasks = ['propagatorTheoryCorrection=2','IonizeMO', 'ionizeSpecie', 'ptTransitionOperator', 'MOfractionOccupation']

# Control

unit_control = ['formatNumberOfColumns=', 'unitForOutputFile=', 'unitForMolecularOrbitalsFIle=', 'unitForMP2IntegralsFile=', 'printLevel=', 'units=']

general_control = ['method=', 'transformToCenterOfMass=', 'areThereDummyAtoms=',
                   'areThereQDOPotentials=', 'setQDOEnergyZero=', 'isThereExternalPotential=',
                   'isThereInterparticlePotential= ', 'isThereOutput=', 'isThereFrozenParticle=', 'dimensionality='
                   ]