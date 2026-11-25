from __future__ import annotations

from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades.sources import make_th_plates, source_xyz


def test_make_th_plates():
    plates = AttrsDict(
        {"height_in_mm": 10.0, "width_in_mm": 50.0, "cavity_width_in_mm": 5.0}
    )

    th_plates_lv = make_th_plates(plates)

    assert isinstance(th_plates_lv, geant4.LogicalVolume)


def test_source_xyz():
    # basic test for non HS1
    pos = AttrsDict({"phi_in_deg": 0.0, "r_in_mm": 0.0, "z_in_mm": 38.0})

    x, y, z = source_xyz(pos, source_type="am_HS6")

    assert x == 0.0
    assert y == 0.0
    assert z == 38.0
