"""Tests to verify that GDML and Python implementations produce equivalent geometries."""

from __future__ import annotations

from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades.create_volumes import (
    create_bottom_plate,
    create_cryostat,
    create_holder,
    create_lead_castle,
    create_th_plate,
    create_wrap,
)


def test_wrap_equivalence():
    """Test that wrap geometry is equivalent between GDML and Python."""
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

    wrap_lv_gdml = create_wrap(wrap_metadata, from_gdml=True)
    wrap_lv_python = create_wrap(wrap_metadata, from_gdml=False)

    # Both should be logical volumes
    assert isinstance(wrap_lv_gdml, geant4.LogicalVolume)
    assert isinstance(wrap_lv_python, geant4.LogicalVolume)

    # Both should have the same name
    assert wrap_lv_gdml.name == wrap_lv_python.name == "Wrap"

    # Both should have the same material
    assert wrap_lv_gdml.material.name == wrap_lv_python.material.name == "HD1000"


def test_cryostat_equivalence():
    """Test that cryostat geometry is equivalent between GDML and Python."""
    cryostat_meta = AttrsDict(
        {
            "height": 250,
            "width": 100,
            "thickness": 2,
            "position_cavity_from_top": 10,
            "position_cavity_from_bottom": 20,
        }
    )

    cryo_lv_gdml = create_cryostat(cryostat_meta, from_gdml=True)
    cryo_lv_python = create_cryostat(cryostat_meta, from_gdml=False)

    assert isinstance(cryo_lv_gdml, geant4.LogicalVolume)
    assert isinstance(cryo_lv_python, geant4.LogicalVolume)

    assert cryo_lv_gdml.name == cryo_lv_python.name == "Cryostat"
    assert cryo_lv_gdml.material.name == cryo_lv_python.material.name == "EN_AW-2011T8"


def test_bottom_plate_equivalence():
    """Test that bottom plate geometry is equivalent between GDML and Python."""
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

    plate_lv_gdml = create_bottom_plate(plate_metadata, from_gdml=True)
    plate_lv_python = create_bottom_plate(plate_metadata, from_gdml=False)

    assert isinstance(plate_lv_gdml, geant4.LogicalVolume)
    assert isinstance(plate_lv_python, geant4.LogicalVolume)

    assert plate_lv_gdml.name == plate_lv_python.name == "Bottom_plate"
    assert plate_lv_gdml.material.name == plate_lv_python.material.name == "Al"


def test_th_plate_equivalence():
    """Test that th plate geometry is equivalent between GDML and Python."""
    source_dims = AttrsDict({"plates": {"height": 10.0, "width": 50.0, "cavity_width": 5.0}})

    th_plate_lv_gdml = create_th_plate(source_dims, from_gdml=True)
    th_plate_lv_python = create_th_plate(source_dims, from_gdml=False)

    assert isinstance(th_plate_lv_gdml, geant4.LogicalVolume)
    assert isinstance(th_plate_lv_python, geant4.LogicalVolume)

    assert th_plate_lv_gdml.name == th_plate_lv_python.name == "Source_Plates"
    # Both should use lead material
    assert "Pb" in th_plate_lv_gdml.material.name
    assert "Pb" in th_plate_lv_python.material.name


def test_bege_holder_equivalence():
    """Test that bege holder geometry is equivalent between GDML and Python."""
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

    lv_gdml = create_holder(holder, "bege", from_gdml=True)
    lv_python = create_holder(holder, "bege", from_gdml=False)

    assert isinstance(lv_gdml, geant4.LogicalVolume)
    assert isinstance(lv_python, geant4.LogicalVolume)

    assert lv_gdml.name == lv_python.name == "Holder"
    assert lv_gdml.material.name == lv_python.material.name == "EN_AW-2011T8"


def test_lead_castle_table1_equivalence():
    """Test that lead castle table 1 geometry is equivalent between GDML and Python."""
    castle_dims = AttrsDict(
        {
            "base": {"width": 480, "depth": 450, "height": 500},
            "inner_cavity": {"width": 300, "depth": 250, "height": 500},
            "cavity": {"width": 120, "depth": 100, "height": 400},
            "top": {"width": 300, "depth": 300, "height": 90},
            "front": {"width": 160, "depth": 100, "height": 400},
        }
    )

    castle_lv_gdml = create_lead_castle(1, castle_dims, from_gdml=True)
    castle_lv_python = create_lead_castle(1, castle_dims, from_gdml=False)

    assert isinstance(castle_lv_gdml, geant4.LogicalVolume)
    assert isinstance(castle_lv_python, geant4.LogicalVolume)

    assert castle_lv_gdml.name == castle_lv_python.name == "Lead_castle"
    # Both should use lead material
    assert "Pb" in castle_lv_gdml.material.name
    assert "Pb" in castle_lv_python.material.name
