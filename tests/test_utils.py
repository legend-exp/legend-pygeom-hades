from __future__ import annotations

import numpy as np
import pyg4ometry

from pygeomhades import utils
from pygeomhades.metadata import PublicLegendMetadataProxy


def test_merge_config():
    meta = PublicLegendMetadataProxy()

    hpge = utils.merge_configs(
        meta.hardware.detectors.germanium.diodes["V07302A"], {"dimensions": 1}
    )

    assert hpge.hades.dimensions == 1
    assert hpge.production.enrichment.val is not None


def test_parse_measurement_basic():
    out = utils.parse_measurement("cs_HS2_bottom_foo")

    assert out.source == "cs_HS2"
    assert out.position == "bottom"
    assert out.id == "foo"

    out = utils.parse_measurement("am_HS1_top_dlt")

    assert out.source == "am_HS1"
    assert out.position == "top"
    assert out.id == "dlt"

    out = utils.parse_measurement("am_HS6_top_dlt")

    assert out.source == "am_HS6"  # no renaming


def test_profile():
    reg = pyg4ometry.geant4.Registry()

    polycone = pyg4ometry.geant4.solid.Polycone(
        "test_polycone",
        0,
        2 * np.pi,
        [0, 10],
        [2, 10],
        [3, 10],
        lunit="mm",
        registry=reg,
    )

    profile = utils.get_profile(polycone)

    assert profile["r"] == [2, 10, 10, 3, 2]
    assert profile["z"] == [0, 10, 10, 0, 0]

    generic_polycone = pyg4ometry.geant4.solid.GenericPolycone(
        "test_generic_polycone",
        0,
        2 * np.pi,
        [0, 0, 10, 0],
        [2, 2, 5, 5],
        lunit="mm",
        registry=reg,
    )
    profile = utils.get_profile(generic_polycone)
    assert profile["r"] == [0, 0, 10, 0, 0]
    assert profile["z"] == [2, 2, 5, 5, 2]
