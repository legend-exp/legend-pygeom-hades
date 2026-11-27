from __future__ import annotations

import os

import pygeomtools
import pytest
from dbetto import AttrsDict
from legendmeta import HadesMetadata
from pyg4ometry import geant4

from pygeomhades.core import construct
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
                    "run_start_time": "191023T154500",
                    "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                }
            ),
            True,
        ),
        (
            AttrsDict(
                {
                    "detector": "V02160B",
                    "campaign": "c1",
                    "measurement": "am_HS6_top_dlt",
                    "run_start_time": "200826T092000",
                    "daq_settings": {"flashcam": {"card_interface": "efb2"}},
                }
            ),
            False,
        ),
        *[
            (
                AttrsDict(
                    {
                        "detector": "V07302A",
                        "campaign": "c1",
                        "measurement": meas,
                        "daq_settings": {
                            "flashcam": {
                                "card_interface": "efb3"
                                if meas.startswith("am_HS1")
                                else "efb2"
                            }
                        },
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
                        "daq_settings": {
                            "flashcam": {
                                "card_interface": "efb3"
                                if meas.startswith("am_HS1")
                                else "efb2"
                            }
                        },
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
                        "run_start_time": start,
                        "measurement": "th_HS2_lat_psa",
                        "daq_settings": {"flashcam": {"card_interface": card}},
                        "source_position": AttrsDict(
                            {"phi_in_deg": 0.0, "r_in_mm": 30, "z_in_mm": 60.0}
                        ),
                    }
                ),
                table2,
            )
            for run, start, card, table2 in [
                ("run0001", "191023T091515", "efb1", False),
                ("run0003", "191105T103952", "efb2", True),
            ]
        ],
    ],
    ids=[
        "bege_efb1_am_HS6_top_dlt",
        "table2_2019_gerda_castle",
        "table2_2020_legend_castle",
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

    pvs = reg.physicalVolumeDict
    assert pvs["cryostat_vacuum"].motherVolume.name == "cryostat_wall_aluminium"

    if assert_copper_plate:
        assert pvs["castle_plate_copper"].motherVolume.name == "lab_air"


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


@pytest.mark.parametrize(
    ("detector", "card", "castle"),
    [
        ("V07302A", "efb1", True),  # am_HS1 on a static table (as in 2021)
        ("V07302A", "efb3", False),  # scanning table
        ("V02160B", "efb1", False),  # listed in hardware/setup/table_exceptions
    ],
)
def test_table_from_card(detector: str, card: str, castle: bool):
    config = AttrsDict(
        {
            "detector": detector,
            "measurement": "am_HS1_top_ssh",
            "daq_settings": {"flashcam": {"card_interface": card}},
        }
    )
    reg = construct(config, public_geometry=public_geom)
    assert ("castle_lead" in reg.physicalVolumeDict) == castle


@pytest.mark.parametrize(
    ("extra", "castle"),
    [
        ({}, True),
        ({"daq_settings": {"flashcam": {"card_interface": "efb3"}}}, False),
    ],
)
def test_run_key(private_meta, extra: dict, castle: bool):
    config = AttrsDict({"run_key": "V13049A-c1-th_HS2_top_psa-run0002", **extra})
    reg = construct(config)
    assert "source_active" in reg.physicalVolumeDict
    assert ("castle_lead" in reg.physicalVolumeDict) == castle


@pytest.mark.parametrize(
    ("run_key", "error"),
    [
        ("V13049A-c1-th_HS2_top_psa", "<detector>-<campaign>-<measurement>-<run>"),
        ("V13049A-c1-th_HS2_top_psa-run0003", "run run0003 not found"),
        ("V0-c1-th_HS2_top_psa-run0001", "detector V0 not found"),
    ],
)
def test_run_key_errors(private_meta, run_key: str, error: str):
    with pytest.raises(ValueError, match=error):
        construct(AttrsDict({"run_key": run_key}))


def test_run_key_public_geometry():
    with pytest.raises(ValueError, match="private hades-metadata"):
        construct(
            AttrsDict({"run_key": "V13049A-c1-th_HS2_top_psa-run0001"}),
            public_geometry=True,
        )


@pytest.mark.parametrize(
    ("card", "x"),
    [
        ("efb1", 20.0),  # static table: r is the distance from the cryostat axis
        ("efb3", -46.0),  # scanning table: r is the arm position, axis at 66 mm
    ],
)
def test_am_hs1_top_source_x(card: str, x: float):
    config = AttrsDict(
        {
            "detector": "V07302A",
            "campaign": "c1",
            "measurement": "am_HS1_top_dlt",
            "daq_settings": {"flashcam": {"card_interface": card}},
            "source_position": {"phi_in_deg": 0.0, "r_in_mm": 20.0, "z_in_mm": 5.0},
        }
    )
    reg = construct(config, public_geometry=public_geom)
    pos = reg.physicalVolumeDict["source_collimator_copper"].position.eval()
    assert pos[0] == pytest.approx(x)
    assert pos[1] == pytest.approx(0)
