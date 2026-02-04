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

    # Names differ: GDML uses "Wrap", Python uses "wrap"
    assert wrap_lv_gdml.name == "Wrap"
    assert wrap_lv_python.name == "wrap"

    # Both should have the same material
    assert wrap_lv_gdml.material.name == wrap_lv_python.material.name == "HD1000"

    # Both solids should be polycone types (GDML creates Polycone, Python creates GenericPolycone)
    assert "Polycone" in type(wrap_lv_gdml.solid).__name__
    assert "Polycone" in type(wrap_lv_python.solid).__name__

    # Check polycone geometry parameters
    gdml_solid = wrap_lv_gdml.solid
    python_solid = wrap_lv_python.solid

    # GDML Polycone uses z-planes with RMin/RMax, GenericPolycone uses explicit R-Z points
    # Evaluate GDML expressions to get numeric values
    gdml_z = [float(z.eval()) for z in gdml_solid.pZpl]
    gdml_rmin = [float(r.eval()) for r in gdml_solid.pRMin]
    gdml_rmax = [float(r.eval()) for r in gdml_solid.pRMax]

    # Python GenericPolycone has explicit R and Z arrays
    python_r = python_solid.pR
    python_z = python_solid.pZ

    # Verify both representations describe the same geometry
    # Check that start and end z-coordinates match
    assert abs(min(python_z) - min(gdml_z)) < 1e-6, f"Start Z mismatch: {min(python_z)} vs {min(gdml_z)}"
    assert abs(max(python_z) - max(gdml_z)) < 1e-6, f"End Z mismatch: {max(python_z)} vs {max(gdml_z)}"

    # Verify radii: check that max radius in Python matches GDML RMax
    max_python_r = max(python_r)
    max_gdml_r = max(gdml_rmax)
    assert abs(max_python_r - max_gdml_r) < 1e-6, f"Max radius mismatch: {max_python_r} vs {max_gdml_r}"

    # Check inner radii match (for hollow polycones)
    non_zero_python_r = [r for r in python_r if r > 0]
    non_zero_gdml_rmin = [r for r in gdml_rmin if r > 0]
    if non_zero_python_r and non_zero_gdml_rmin:
        assert abs(min(non_zero_python_r) - min(non_zero_gdml_rmin)) < 1e-6, (
            f"Min inner radius mismatch: {min(non_zero_python_r)} vs {min(non_zero_gdml_rmin)}"
        )


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

    # Both solids should be polycone types
    assert "Polycone" in type(cryo_lv_gdml.solid).__name__
    assert "Polycone" in type(cryo_lv_python.solid).__name__

    # Check polycone geometry parameters
    gdml_solid = cryo_lv_gdml.solid
    python_solid = cryo_lv_python.solid

    # GDML Polycone uses z-planes with RMin/RMax, GenericPolycone uses explicit R-Z points
    # Evaluate GDML expressions to get numeric values
    gdml_z = [float(z.eval()) for z in gdml_solid.pZpl]
    gdml_rmin = [float(r.eval()) for r in gdml_solid.pRMin]
    gdml_rmax = [float(r.eval()) for r in gdml_solid.pRMax]

    # Python GenericPolycone has explicit R and Z arrays
    python_r = python_solid.pR
    python_z = python_solid.pZ

    # Verify both representations describe the same geometry
    # Check that start and end z-coordinates match
    assert abs(min(python_z) - min(gdml_z)) < 1e-6, f"Start Z mismatch: {min(python_z)} vs {min(gdml_z)}"
    assert abs(max(python_z) - max(gdml_z)) < 1e-6, f"End Z mismatch: {max(python_z)} vs {max(gdml_z)}"

    # Verify radii: check that max radius in Python matches GDML RMax
    max_python_r = max(python_r)
    max_gdml_r = max(gdml_rmax)
    assert abs(max_python_r - max_gdml_r) < 1e-6, f"Max radius mismatch: {max_python_r} vs {max_gdml_r}"

    # Verify the cavity radius (min inner radius)
    non_zero_gdml_rmin = [r for r in gdml_rmin if r > 0]
    non_zero_python_r = [r for r in python_r if r > 0]
    if non_zero_gdml_rmin and non_zero_python_r:
        assert abs(min(non_zero_python_r) - min(non_zero_gdml_rmin)) < 1e-6, (
            f"Min cavity radius mismatch: {min(non_zero_python_r)} vs {min(non_zero_gdml_rmin)}"
        )


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

    # Both solids should be the same type (Subtraction)
    assert type(plate_lv_gdml.solid).__name__ == type(plate_lv_python.solid).__name__
    assert "Subtraction" in type(plate_lv_gdml.solid).__name__

    # Check subtraction components - both should be boxes
    solid_gdml = plate_lv_gdml.solid
    solid_python = plate_lv_python.solid

    # The obj1 (main plate) should be a Box
    assert "Box" in type(solid_gdml.obj1).__name__
    assert "Box" in type(solid_python.obj1).__name__

    # The obj2 (cavity) should also be a Box
    assert "Box" in type(solid_gdml.obj2).__name__
    assert "Box" in type(solid_python.obj2).__name__

    # Check dimensions of the main plate box
    assert float(solid_gdml.obj1.pX) == float(solid_python.obj1.pX) == plate_metadata.width
    assert float(solid_gdml.obj1.pY) == float(solid_python.obj1.pY) == plate_metadata.depth
    assert float(solid_gdml.obj1.pZ) == float(solid_python.obj1.pZ) == plate_metadata.height

    # Check dimensions of the cavity box
    assert float(solid_gdml.obj2.pX) == float(solid_python.obj2.pX) == plate_metadata.cavity.width
    assert float(solid_gdml.obj2.pY) == float(solid_python.obj2.pY) == plate_metadata.cavity.depth
    assert float(solid_gdml.obj2.pZ) == float(solid_python.obj2.pZ) == plate_metadata.cavity.height


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

    # Both solids should be tube types (Tubs)
    assert "Tubs" in type(th_plate_lv_gdml.solid).__name__
    assert "Tubs" in type(th_plate_lv_python.solid).__name__

    # Check tube parameters (rmin, rmax, z)
    # Note: GDML may use expression objects, so we check the evaluated values
    solid_gdml = th_plate_lv_gdml.solid
    solid_python = th_plate_lv_python.solid

    # Both should have the same inner and outer radii (compare as floats)
    assert float(solid_gdml.pRMin.eval() if hasattr(solid_gdml.pRMin, "eval") else solid_gdml.pRMin) == float(
        solid_python.pRMin
    )
    assert float(solid_gdml.pRMax.eval() if hasattr(solid_gdml.pRMax, "eval") else solid_gdml.pRMax) == float(
        solid_python.pRMax
    )
    assert float(solid_gdml.pDz.eval() if hasattr(solid_gdml.pDz, "eval") else solid_gdml.pDz) == float(
        solid_python.pDz
    )


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

    # Names differ: GDML uses "Holder", Python uses "holder"
    assert lv_gdml.name == "Holder"
    assert lv_python.name == "holder"
    assert lv_gdml.material.name == lv_python.material.name == "EN_AW-2011T8"

    # Both solids should be polycone types
    assert "Polycone" in type(lv_gdml.solid).__name__
    assert "Polycone" in type(lv_python.solid).__name__

    # Check polycone geometry parameters
    gdml_solid = lv_gdml.solid
    python_solid = lv_python.solid

    # GDML Polycone uses z-planes with RMin/RMax, GenericPolycone uses explicit R-Z points
    # Evaluate GDML expressions to get numeric values
    gdml_z = [float(z.eval()) for z in gdml_solid.pZpl]
    gdml_rmax = [float(r.eval()) for r in gdml_solid.pRMax]

    # Python GenericPolycone has explicit R and Z arrays
    python_r = python_solid.pR
    python_z = python_solid.pZ

    # Verify both representations describe the same geometry
    # Check that start and end z-coordinates match
    assert abs(min(python_z) - min(gdml_z)) < 1e-6, f"Start Z mismatch: {min(python_z)} vs {min(gdml_z)}"
    assert abs(max(python_z) - max(gdml_z)) < 1e-6, f"End Z mismatch: {max(python_z)} vs {max(gdml_z)}"

    # Verify radii: check that max radius in Python matches GDML RMax
    max_python_r = max(python_r)
    max_gdml_r = max(gdml_rmax)
    assert abs(max_python_r - max_gdml_r) < 1e-6, f"Max radius mismatch: {max_python_r} vs {max_gdml_r}"


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

    # Both solids should be the same type (Union for lead castle)
    assert type(castle_lv_gdml.solid).__name__ == type(castle_lv_python.solid).__name__
    assert "Union" in type(castle_lv_gdml.solid).__name__
