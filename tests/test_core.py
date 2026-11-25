from __future__ import annotations

import os

import pygeomtools
import pytest
from dbetto import AttrsDict
from legendmeta import HadesMetadata
from pyg4ometry import geant4

from pygeomhades.core import construct, source_xyz
from pygeomhades.metadata import PublicHadesMetadataProxy

public_geom = os.getenv("LEGEND_METADATA", "") == ""


def test_import():
    import pygeomhades  # noqa: F401


@pytest.mark.parametrize(
    ("config", "assert_copper_plate"),
    [
        (
            AttrsDict(
                {
                    "detector": "B00000B",
                    "campaign": "c1",
                    "measurement": "am_HS6_top_dlt",
                    "daq_settings": {"flashcam": {"card_interface": "efb1"}},
                }
            ),
            False,
        ),
        (
            AttrsDict(
                {
                    "detector": "V02160B",
                    "campaign": "c1",
                    "measurement": "am_HS6_top_dlt",
                    "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                }
            ),
            True,
        ),
        *[
            (
                AttrsDict(
                    {
                        "detector": "V07302A",
                        "campaign": "c1",
                        "measurement": meas,
                        "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                        "source_position": AttrsDict(
                            {"phi_in_deg": 0.0, "r_in_mm": 0.0, "z_in_mm": 38.0}
                        ),
                    }
                ),
                False,
            )
            for meas in [
                "am_HS1_top_dlt",
                "th_HS2_top_dlt",
                "ba_HS4_top_dlt",
                "co_HS5_top_dlt",
                "am_HS6_top_dlt",
            ]
        ],
        *[
            (
                AttrsDict(
                    {
                        "detector": "V07302A",
                        "campaign": "c1",
                        "measurement": meas,
                        "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                        "source_position": AttrsDict(
                            {"phi_in_deg": 0.0, "r_in_mm": 30, "z_in_mm": 60.0}
                        ),
                    }
                ),
                False,
            )
            for meas in ["am_HS1_lat_dlt", "th_HS2_lat_psa"]
        ],
        *[
            (
                AttrsDict(
                    {
                        "detector": "V02160A",
                        "run": run,
                        "measurement": "th_HS2_lat_psa",
                        "daq_settings": {"flashcam": {"card_interface": card}},
                        "source_position": AttrsDict(
                            {"phi_in_deg": 0.0, "r_in_mm": 30, "z_in_mm": 60.0}
                        ),
                    }
                ),
                table2,
            )
            for run, card, table2 in [
                ("run0001", "efb1", False),
                ("run0003", "efb2", True),
            ]
        ],
    ],
    ids=[
        "bege_efb1_am_HS6_top_dlt",
        "table2_efb2_am_HS6_top_dlt",
        "source_am_HS1_top_dlt",
        "source_th_HS2_top_dlt",
        "source_ba_HS4_top_dlt",
        "source_co_HS5_top_dlt",
        "source_am_HS6_top_dlt",
        "lateral_am_HS1_lat_dlt",
        "lateral_th_HS2_lat_psa",
        "table1_run",
        "table2_run",
    ],
)
def test_construct(config: AttrsDict, assert_copper_plate: bool):
    reg = construct(config, public_geometry=public_geom)

    assert isinstance(reg, geant4.Registry)
    pygeomtools.geometry.check_registry_sanity(reg, reg)

    if assert_copper_plate:
        assert "Copper_plate_PV" in reg.physicalVolumeDict


@pytest.mark.parametrize(
    "det",
    (
        PublicHadesMetadataProxy() if public_geom else HadesMetadata()
    ).hardware.cryostat.keys(),
)
def test_construct_am_hs6_top_dlt(det: str):
    # skip the special detectors
    if det in ["V02162B", "V02160A", "V07646A", "V06649A"] and public_geom:
        pytest.skip("public geometry: special detector not available")

    pos = AttrsDict({"phi_in_deg": 0.0, "r_in_mm": 0.0, "z_in_mm": 38.0})
    reg = construct(
        AttrsDict(
            {
                "detector": det,
                "campaign": "c1",
                "measurement": "am_HS6_top_dlt",
                "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                "source_position": pos,
            }
        ),
        public_geometry=public_geom,
    )
    assert isinstance(reg, geant4.Registry)
    pygeomtools.geometry.check_registry_sanity(reg, reg)


def test_source_xyz():
    # basic test for non HS1
    pos = AttrsDict({"phi_in_deg": 0.0, "r_in_mm": 0.0, "z_in_mm": 38.0})

    x, y, z = source_xyz(pos, source_type="am_HS6")

    assert x == 0.0
    assert y == 0.0
    assert z == 38.0
