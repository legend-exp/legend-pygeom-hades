"""Materials of the HADES setup.

Densities are in g/cm³. A material composition is given either as number of
atoms per molecule (``natoms``) or as mass fractions (``fractions``).
"""

from __future__ import annotations

from pyg4ometry import geant4

# symbol: (name, Z, molar mass in g/mol)
_ELEMENTS = {
    "H": ("Hydrogen", 1, 1.0),
    "C": ("Carbon", 6, 12.01),
    "N": ("Nitrogen", 7, 14.01),
    "O": ("Oxygen", 8, 16.0),
    "Al": ("Aluminium", 13, 26.98),
    "Si": ("Silicon", 14, 28.09),
    "Ar": ("Argon", 18, 39.95),
    "Cr": ("Chromium", 24, 51.9961),
    "Mn": ("Manganese", 25, 54.93805),
    "Fe": ("Iron", 26, 55.845),
    "Ni": ("Nickel", 28, 58.9332),
    "Cu": ("Copper", 29, 63.546),
    "Pb": ("Lead", 82, 207.2),
    "Bi": ("Bismuth", 83, 208.98),
}

# key: (Geant4 name, density, composition)
_MATERIALS = {
    "hd1000": ("HD1000", 0.93, {"natoms": {"H": 4, "C": 2}}),
    "en_aw_2011t8": (
        "EN_AW-2011T8",
        2.84,
        {"fractions": {"Cu": 0.06, "Pb": 0.004, "Bi": 0.004, "Al": 0.932}},
    ),
    "aluminium": ("Al", 2.7, {"fractions": {"Al": 1}}),
    "lead": ("Pb", 11.35, {"fractions": {"Pb": 1}}),
    "lead_table2": ("metalPb", 11.34, {"fractions": {"Pb": 1}}),
    "copper": ("metalCu", 8.96, {"fractions": {"Cu": 1}}),
    "steel": (
        "Ssteel",
        7.9,
        {"fractions": {"Si": 0.01, "Cr": 0.2, "Mn": 0.02, "Fe": 0.67, "Ni": 0.1}},
    ),
    "quartz": ("SiliconDioxide", 2.32, {"natoms": {"Si": 1, "O": 2}}),
    "air": (
        "Air",
        0.00120479,
        {"fractions": {"C": 0.000124, "N": 0.755268, "O": 0.231781, "Ar": 0.012827}},
    ),
    "acrylic": ("Acrylic", 1.15, {"natoms": {"C": 5, "H": 8, "O": 2}}),
    # FIXME: acrylic (PMMA) is C5H8O2
    "acrylic_source_holder": ("Acrylic", 1.15, {"natoms": {"C": 5, "H": 8, "O": 8}}),
    "epoxy": ("epoxy_mod", 1.129, {"natoms": {"C": 41, "H": 49, "O": 7, "N": 3}}),
    "vacuum": ("Galactic", 1e-25, {"fractions": {"H": 1}}),
}


def get_material(key: str, registry: geant4.Registry) -> geant4.Material:
    """Get a material by its key in the material table, adding it to `registry` if needed.

    Materials predefined in Geant4 (names starting with ``G4_``) are also accepted.
    """
    if key.startswith("G4_"):
        if key not in registry.materialDict:
            geant4.MaterialPredefined(key, registry)
        return registry.materialDict[key]

    name, density, comp = _MATERIALS[key]
    if name in registry.materialDict:
        return registry.materialDict[name]

    def element(symbol):
        el_name, z, a = _ELEMENTS[symbol]
        if el_name not in registry.materialDict:
            geant4.ElementSimple(el_name, symbol, z, a, registry)
        return registry.materialDict[el_name]

    parts = comp.get("natoms", comp.get("fractions"))
    mat = geant4.Material(
        name=name, density=density, number_of_components=len(parts), registry=registry
    )
    for symbol, n in parts.items():
        if "natoms" in comp:
            mat.add_element_natoms(element(symbol), n)
        else:
            mat.add_element_massfraction(element(symbol), n)
    return mat
