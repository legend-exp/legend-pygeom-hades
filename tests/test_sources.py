from __future__ import annotations

import pytest
from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades.materials import HadesMaterialRegistry
from pygeomhades.sources import make_th_plates, scanning_axis_in_mm, source_xyz


def test_make_th_plates():
    plates = AttrsDict(
        {"height_in_mm": 10.0, "width_in_mm": 50.0, "cavity_width_in_mm": 5.0}
    )

    reg = geant4.Registry()
    th_plates_lv = make_th_plates(plates, reg, HadesMaterialRegistry(reg))

    assert isinstance(th_plates_lv, geant4.LogicalVolume)


def test_source_xyz():
    pos = AttrsDict({"phi_in_deg": 0.0, "r_in_mm": 0.0, "z_in_mm": 38.0})
    assert source_xyz(pos) == (0.0, 0.0, 38.0)

    # arm position before the cryostat axis: opposite side
    pos = AttrsDict({"phi_in_deg": 0.0, "r_in_mm": 46.0, "z_in_mm": 5.0})
    x, y, z = source_xyz(pos, axis_in_mm=66.0)
    assert x == pytest.approx(-20)
    assert y == pytest.approx(0)
    assert z == 5.0

    pos = AttrsDict({"phi_in_deg": 90.0, "r_in_mm": 86.0, "z_in_mm": 5.0})
    x, y, _ = source_xyz(pos, axis_in_mm=66.0)
    assert x == pytest.approx(0)
    assert y == pytest.approx(-20)


def _hardware(runs: dict) -> AttrsDict:
    """Hardware metadata of detector V07302A with the given am_HS1_top_dlt runs."""
    return AttrsDict(
        {
            "setup": {"table_exceptions": {}},
            "configuration": {
                "V07302A": {
                    "c1": {
                        "am_HS1_top_dlt": {
                            f"run{i:04d}": {
                                "detector": "V07302A",
                                "measurement": "am_HS1_top_dlt",
                                "daq_settings": {"flashcam": {"card_interface": card}},
                                "source_position": {"r_in_mm": r},
                            }
                            for i, (card, r) in enumerate(runs)
                        }
                    }
                }
            },
        }
    )


@pytest.mark.parametrize(
    ("runs", "axis"),
    [
        ([("efb3", 46.0), ("efb3", 86.0), ("efb3", 66.0)], 66.0),
        ([("efb3", 40.0), ("efb3", 62.5), ("efb3", 84.0), ("efb3", 62.5)], 62.5),
        ([("efb3", 57.5), ("efb3", 77.0)], 57.5),
        # static table runs: r is the distance from the axis
        ([("efb1", 0.0), ("efb1", 0.0), ("efb3", 44.0)], 44.0),
        ([("efb1", 0.0), ("efb1", 20.0)], 66.0),
        ([], 66.0),
    ],
)
def test_scanning_axis_in_mm(runs, axis):
    assert scanning_axis_in_mm(_hardware(runs), "V07302A", "c1") == axis


def test_scanning_axis_in_mm_missing():
    hardware = _hardware([("efb3", 50.0), ("efb3", 70.0), ("efb3", 90.0)])
    assert scanning_axis_in_mm(hardware, "V07302A", "c2") == 66.0
    assert scanning_axis_in_mm(hardware, "V07302A", None) == 66.0
    assert scanning_axis_in_mm(hardware, "V99999A", "c1") == 66.0
    assert scanning_axis_in_mm(AttrsDict({"setup": {}}), "V07302A", "c1") == 66.0
