from __future__ import annotations

import pytest
from pyg4ometry import geant4

from pygeomhades import materials


@pytest.mark.parametrize("key", list(materials._MATERIALS))
def test_get_material(key):
    reg = geant4.Registry()
    mat = materials.get_material(key, reg)
    assert isinstance(mat, geant4.Material)
    assert materials.get_material(key, reg) is mat


def test_get_predefined_material():
    reg = geant4.Registry()
    assert materials.get_material("G4_Pb", reg).name == "G4_Pb"
