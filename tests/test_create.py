from __future__ import annotations

import pytest
from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades.create_volumes import (
    create_bottom_plate,
    create_cryostat,
    create_holder,
    create_lead_castle,
    create_th_plate,
    create_vacuum_cavity,
    create_wrap,
)


def test_create_cavity():
    cryostat = AttrsDict(
        {
            "width": 200,
            "thickness": 1,
            "height": 200,
            "position_cavity_from_top": 1,
            "position_cavity_from_bottom": 1,
        }
    )

    reg = geant4.Registry()
    lv = create_vacuum_cavity(cryostat, reg)
    assert isinstance(lv, geant4.LogicalVolume)


def test_create_wrap():
    wrap_metadata = AttrsDict(
        {
            "outer": {
                "height_in_mm": 100,
                "radius_in_mm": 50,
            },
            "inner": {
                "height_in_mm": 99,
                "radius_in_mm": 49,
            },
        }
    )

    # Test GDML-based creation
    wrap_lv_gdml = create_wrap(wrap_metadata, from_gdml=True)
    assert wrap_lv_gdml is not None
    assert isinstance(wrap_lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation
    wrap_lv_python = create_wrap(wrap_metadata, from_gdml=False)
    assert wrap_lv_python is not None
    assert isinstance(wrap_lv_python, geant4.LogicalVolume)


def test_create_holder():
    holder = AttrsDict(
        {
            "cylinder": {
                "inner": {
                    "height_in_mm": 100,
                    "radius_in_mm": 100,
                },
                "outer": {
                    "height_in_mm": 104,
                    "radius_in_mm": 104,
                },
            },
            "bottom_cyl": {
                "inner": {
                    "height_in_mm": 100,
                    "radius_in_mm": 100,
                },
                "outer": {
                    "height_in_mm": 104,
                    "radius_in_mm": 104,
                },
            },
            "rings": {
                "position_top_ring_in_mm": 20,
                "position_bottom_ring_in_mm": 30,
                "radius_in_mm": 150,
                "height_in_mm": 10,
            },
            "edge": {
                "height_in_mm": 1000,
            },
        }
    )

    # Test GDML-based creation for bege
    lv_gdml = create_holder(holder, "bege", from_gdml=True)
    assert isinstance(lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation for bege
    lv_python = create_holder(holder, "bege", from_gdml=False)
    assert isinstance(lv_python, geant4.LogicalVolume)

    # Test GDML-based creation for icpc
    lv_icpc = create_holder(holder, "icpc", from_gdml=True)
    assert isinstance(lv_icpc, geant4.LogicalVolume)

    # ICPC Python implementation is not yet complete
    with pytest.raises(NotImplementedError):
        _ = create_holder(holder, "icpc", from_gdml=False)


def test_create_th_plate():
    source_dims = AttrsDict({"plates": {"height": 10.0, "width": 50.0, "cavity_width": 5.0}})

    # Test GDML-based creation
    th_plate_lv_gdml = create_th_plate(source_dims, from_gdml=True)
    assert isinstance(th_plate_lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation
    th_plate_lv_python = create_th_plate(source_dims, from_gdml=False)
    assert isinstance(th_plate_lv_python, geant4.LogicalVolume)


def test_create_cryostat():
    cryostat_meta = AttrsDict(
        {
            "height": 250,
            "width": 100,
            "thickness": 2,
            "position_cavity_from_top": 10,
            "position_cavity_from_bottom": 20,
        }
    )

    # Test GDML-based creation
    cryo_lv_gdml = create_cryostat(cryostat_meta, from_gdml=True)
    assert isinstance(cryo_lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation
    cryo_lv_python = create_cryostat(cryostat_meta, from_gdml=False)
    assert isinstance(cryo_lv_python, geant4.LogicalVolume)


def test_create_bottom_plate():
    plate_metadata = AttrsDict(
        {
            "width": 300,
            "depth": 400,
            "height": 50,
            "cavity": {
                "width": 150,
                "depth": 200,
                "height": 40,
            },
        }
    )

    # Test GDML-based creation
    plate_lv_gdml = create_bottom_plate(plate_metadata, from_gdml=True)
    assert isinstance(plate_lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation
    plate_lv_python = create_bottom_plate(plate_metadata, from_gdml=False)
    assert isinstance(plate_lv_python, geant4.LogicalVolume)


def test_create_lead_castle():
    castle_dims = AttrsDict(
        {
            "base": {"width": 480, "depth": 450, "height": 500},
            "inner_cavity": {"width": 300, "depth": 250, "height": 500},
            "cavity": {"width": 120, "depth": 100, "height": 400},
            "top": {"width": 300, "depth": 300, "height": 90},
            "front": {"width": 160, "depth": 100, "height": 400},
        }
    )

    # Test GDML-based creation for table 1
    castle_lv_gdml = create_lead_castle(1, castle_dims, from_gdml=True)
    assert isinstance(castle_lv_gdml, geant4.LogicalVolume)

    # Test Python-based creation for table 1
    castle_lv_python = create_lead_castle(1, castle_dims, from_gdml=False)
    assert isinstance(castle_lv_python, geant4.LogicalVolume)

    # Table 2 Python implementation is not yet complete
    castle_dims_2 = AttrsDict(
        {
            "base": {"width": 480, "depth": 480, "height": 500},
            "inner_cavity": {"width": 300, "depth": 300, "height": 500},
            "top": {"width": 300, "depth": 300, "height": 90},
            "copper_plate": {"width": 300, "depth": 300, "height": 3},
        }
    )

    # Test GDML for table 2
    castle_lv_gdml_2 = create_lead_castle(2, castle_dims_2, from_gdml=True)
    assert isinstance(castle_lv_gdml_2, geant4.LogicalVolume)

    # Table 2 Python not implemented yet
    with pytest.raises(NotImplementedError):
        _ = create_lead_castle(2, castle_dims_2, from_gdml=False)
