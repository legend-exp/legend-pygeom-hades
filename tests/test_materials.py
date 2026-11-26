from __future__ import annotations

from pyg4ometry import geant4

from pygeomhades.materials import HadesMaterialRegistry


def test_hades_registry():
    reg = geant4.Registry()
    mats = HadesMaterialRegistry(reg)

    assert isinstance(mats.th_source_epoxy, geant4.Material)
    assert mats.th_source_epoxy is mats.th_source_epoxy
    # no optical properties
    assert mats.pmma.properties == {}
