"""Material definitions for pygeomhades geometry construction.

This module provides functions to create materials used in the HADES geometry.
"""

from __future__ import annotations

from pyg4ometry import geant4


def create_hd1000_material(registry: geant4.Registry) -> geant4.Material:
    """Create HD1000 material (polyethylene-like).

    Parameters
    ----------
    registry
        The pyg4ometry registry to add the material to.

    Returns
    -------
    The HD1000 material.
    """
    h = geant4.ElementSimple("Hydrogen", "H", 1, 1.0)
    c = geant4.ElementSimple("Carbon", "C", 6, 12.01)
    hd1000 = geant4.Material(name="HD1000", density=0.93, number_of_components=2, registry=registry)
    hd1000.add_element_massfraction(h, 4.0 / (4.0 + 2.0 * 12.01))
    hd1000.add_element_massfraction(c, 2.0 * 12.01 / (4.0 + 2.0 * 12.01))
    return hd1000


def create_en_aw_2011t8_material(registry: geant4.Registry) -> geant4.Material:
    """Create EN_AW-2011T8 material (aluminum alloy).

    Parameters
    ----------
    registry
        The pyg4ometry registry to add the material to.

    Returns
    -------
    The EN_AW-2011T8 material.
    """
    al = geant4.ElementSimple("Aluminium", "Al", 13, 26.98)
    cu = geant4.ElementSimple("Copper", "Cu", 29, 63.546)
    pb = geant4.ElementSimple("Lead", "Pb", 82, 207.2)
    bi = geant4.ElementSimple("Bismuth", "Bi", 83, 208.98)

    en_aw_2011t8 = geant4.Material(
        name="EN_AW-2011T8", density=2.84, number_of_components=4, registry=registry
    )
    en_aw_2011t8.add_element_massfraction(al, 0.932)
    en_aw_2011t8.add_element_massfraction(cu, 0.06)
    en_aw_2011t8.add_element_massfraction(pb, 0.004)
    en_aw_2011t8.add_element_massfraction(bi, 0.004)
    return en_aw_2011t8


def create_aluminum_material(registry: geant4.Registry) -> geant4.Material:
    """Create pure aluminum material.

    Parameters
    ----------
    registry
        The pyg4ometry registry to add the material to.

    Returns
    -------
    The aluminum material.
    """
    al = geant4.ElementSimple("Aluminium", "Al", 13, 26.98)
    al_mat = geant4.Material(name="Al", density=2.7, number_of_components=1, registry=registry)
    al_mat.add_element_massfraction(al, 1.0)
    return al_mat
