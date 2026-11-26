from __future__ import annotations

import logging
from pathlib import Path

from dbetto import AttrsDict, utils
from pyg4ometry import geant4

from pygeomhades import colors
from pygeomhades.core import construct


def test_set_colors(caplog):
    reg = geant4.Registry()
    volumes = {
        "Cryostat": "metal_aluminium_2011T8_0",
        "V00000A": "EnrichedGermanium0.900",
        "Source_Alring": "metal_aluminium",
        "lab_lv": "G4_AIR",
        "Mystery": "unobtainium",
    }
    for name, material in volumes.items():
        geant4.LogicalVolume(
            geant4.solid.Box(name, 1, 1, 1, reg),
            geant4.MaterialArbitrary(material, reg),
            name,
            reg,
        )

    with caplog.at_level(logging.WARNING):
        colors.set_colors(reg)

    lvs = reg.logicalVolumeDict
    assert lvs["Cryostat"].pygeom_color_rgba == [0.80, 0.81, 0.83, 0.5]
    assert lvs["V00000A"].pygeom_color_rgba == colors.MATERIAL_COLORS["Germanium"]
    assert (
        lvs["Source_Alring"].pygeom_color_rgba
        == colors.MATERIAL_COLORS["metal_aluminium"]
    )
    assert lvs["lab_lv"].pygeom_color_rgba is False
    assert not hasattr(lvs["Mystery"], "pygeom_color_rgba")
    assert "unobtainium" in caplog.text


def test_all_volumes_colored(caplog):
    config = AttrsDict(utils.load_dict(str(Path(__file__).parent / "test.yaml")))
    with caplog.at_level(logging.WARNING):
        reg = construct(config, public_geometry=True)

    assert not [r for r in caplog.records if r.name == "pygeomhades.colors"]
    assert all(
        hasattr(lv, "pygeom_color_rgba") for lv in reg.logicalVolumeDict.values()
    )
