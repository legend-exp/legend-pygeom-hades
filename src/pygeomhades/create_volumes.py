from __future__ import annotations

from importlib import resources

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades.materials import (
    create_aluminum_material,
    create_en_aw_2011t8_material,
    create_hd1000_material,
)
from pygeomhades.utils import read_gdml_with_replacements


def create_vacuum_cavity(cryostat_metadata: AttrsDict, registry: geant4.Registry) -> geant4.LogicalVolume:
    """Construct the vacuum cavity.

    Parameters
    ----------
    cryostat_metadata
        The dimensions of the various parts of the cryostat, should have
        the following format

        .. code-block:: yaml

            cryostat:
                width: 200
                thickness: 2
                height: 200
                position_cavity_from_top: 10
                position_cavity_from_bottom: 20,
                position_from_bottom: 100

    registry
        The registry to add the geometry to.

    Returns
    -------
    The logical volume for the cavity.
    """
    vacuum_cavity_radius = (cryostat_metadata["width"] - 2 * cryostat_metadata["thickness"]) / 2
    vacuum_cavity_z = (
        cryostat_metadata["height"]
        - cryostat_metadata["position_cavity_from_top"]
        - cryostat_metadata["position_cavity_from_bottom"]
    )
    vacuum_cavity = geant4.solid.GenericPolycone(
        "vacuum_cavity",
        0.0,
        2.0 * np.pi,
        pR=([0.0, vacuum_cavity_radius, vacuum_cavity_radius, 0.0]),
        pZ=[0.0, 0.0, vacuum_cavity_z, vacuum_cavity_z],
        lunit="mm",
        aunit="rad",
        registry=registry,
    )
    return geant4.LogicalVolume(vacuum_cavity, "G4_Galactic", "cavity_lv", registry)


def create_wrap(wrap_metadata: AttrsDict, from_gdml: bool = False) -> geant4.LogicalVolume:
    """Create the mylar wrap.

    .. warning::

        The returned logical volume belongs to its own registry,
        it is necessary to call :func:`reg.addVolumeRecursive` on
        the produced PhysicalVolume to get a sane registry.

    Parameters
    ----------
    wrap_metadata
        The information on the dimensions of the mylar wrap,
        should be of the format:

        .. code-block:: yaml

            outer:
                height_in_mm: 100
                radius_in_mm: 100
            inner:
                height_in_mm: 99
                radius_in_mm: 99

    from_gdml
        whether to read the geometry from GDML or construct it directly.
    """
    if from_gdml:
        dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "wrap_dummy.gdml"

        replacements = {
            "wrap_outer_height_in_mm": wrap_metadata.outer.height_in_mm,
            "wrap_outer_radius_in_mm": wrap_metadata.outer.radius_in_mm,
            "wrap_inner_radius_in_mm": wrap_metadata.inner.radius_in_mm,
            "wrap_top_thickness_in_mm": wrap_metadata.outer.height_in_mm - wrap_metadata.inner.height_in_mm,
        }
        return read_gdml_with_replacements(dummy_gdml_path, replacements)

    # Create wrap directly with pyg4ometry
    reg = geant4.Registry()

    # Define HD1000 material (polyethylene-like)
    hd1000 = create_hd1000_material(reg)

    # Create polycone solid
    wrap_outer_height = wrap_metadata.outer.height_in_mm
    wrap_outer_radius = wrap_metadata.outer.radius_in_mm
    wrap_inner_radius = wrap_metadata.inner.radius_in_mm
    wrap_top_thickness = wrap_outer_height - wrap_metadata.inner.height_in_mm

    wrap_solid = geant4.solid.GenericPolycone(
        "wrap",
        0.0,
        2.0 * np.pi,
        pR=[0.0, wrap_outer_radius, wrap_outer_radius, wrap_inner_radius, wrap_inner_radius],
        pZ=[0.0, 0.0, wrap_top_thickness, wrap_top_thickness, wrap_outer_height],
        lunit="mm",
        aunit="rad",
        registry=reg,
    )

    return geant4.LogicalVolume(wrap_solid, hd1000, "Wrap", reg)


def create_holder(holder_meta: AttrsDict, det_type: str, from_gdml: bool = True) -> geant4.LogicalVolume:
    """Construct the holder geometry

    Parameters
    ----------
    holder_meta
        The metadata describing the holder geometry, should be of the format:

        .. code-block:: yaml

            cylinder:
                inner:
                    height_in_mm: 100
                    radius_in_mm: 100
                outer:
                    height_in_mm: 104
                    radius_in_mm: 104
            bottom_cyl:
                inner:
                    height_in_mm: 100
                    radius_in_mm: 100
                outer:
                    height_in_mm: 104
                    radius_in_mm: 104
            rings:
                position_top_ring_in_mm: 20
                position_bottom_ring_in_mm: 30
                radius_in_mm: 150
                height_in_mm: 10
            edge:
                height_in_mm: 1000

    det_type
        Detector type.
    from_gdml
        Whether to construct from a GDML file

    """

    if from_gdml:
        if det_type == "icpc":
            dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "holder_icpc_dummy.gdml"

            rings = holder_meta["rings"]
            cylinder = holder_meta["cylinder"]
            bottom_cylinder = holder_meta["bottom_cyl"]

            replacements = {
                "max_radius_in_mm": rings.radius_in_mm,
                "outer_height_in_mm": cylinder.outer.height_in_mm,
                "inner_height_in_mm": cylinder.inner.height_in_mm,
                "outer_radius_in_mm": cylinder.outer.radius_in_mm,
                "inner_radius_in_mm": cylinder.inner.radius_in_mm,
                "outer_bottom_cyl_radius_in_mm": bottom_cylinder.outer.radius_in_mm,
                "inner_bottom_cyl_radius_in_mm": bottom_cylinder.inner.radius_in_mm,
                "edge_height_in_mm": holder_meta.edge.height_in_mm,
                "pos_top_ring_in_mm": rings.position_top_ring_in_mm,
                "pos_bottom_ring_in_mm": rings.position_bottom_ring_in_mm,
                "end_top_ring_in_mm": rings.position_top_ring_in_mm + rings.height_in_mm,
                "end_bottom_ring_in_mm": rings.position_bottom_ring_in_mm + rings.height_in_mm,
                "end_bottom_cyl_outer_in_mm": cylinder.outer.height_in_mm + bottom_cylinder.outer.height_in_mm,
                "end_bottom_cyl_inner_in_mm": cylinder.inner.height_in_mm + bottom_cylinder.inner.height_in_mm,
            }

        elif det_type == "bege":
            dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "holder_bege_dummy.gdml"

            rings = holder_meta["rings"]
            cylinder = holder_meta["cylinder"]
            bottom_cylinder = holder_meta["bottom_cyl"]

            replacements = {
                "max_radius_in_mm": rings.radius_in_mm,
                "outer_height_in_mm": cylinder.outer.height_in_mm,
                "inner_height_in_mm": cylinder.inner.height_in_mm,
                "outer_radius_in_mm": cylinder.outer.radius_in_mm,
                "inner_radius_in_mm": cylinder.inner.radius_in_mm,
                "position_top_ring_in_mm": rings.position_top_ring_in_mm,
                "end_top_ring_in_mm": rings.height_in_mm + rings.position_top_ring_in_mm,
            }
        else:
            msg = "cannot construct geometry for coax or ppc"
            raise NotImplementedError(msg)

        return read_gdml_with_replacements(dummy_gdml_path, replacements)
    # Create holder directly with pyg4ometry
    reg = geant4.Registry()

    # Define EN_AW-2011T8 material (aluminum alloy)
    en_aw_2011t8 = create_en_aw_2011t8_material(reg)

    rings = holder_meta["rings"]
    cylinder = holder_meta["cylinder"]

    if det_type == "bege":
        # Create polycone for bege holder
        # Trace the outline: outer edge going up, then inner edge going down
        max_radius = rings.radius_in_mm
        outer_height = cylinder.outer.height_in_mm
        inner_height = cylinder.inner.height_in_mm
        outer_radius = cylinder.outer.radius_in_mm
        inner_radius = cylinder.inner.radius_in_mm
        pos_top_ring_z = rings.position_top_ring_in_mm
        end_top_ring_z = rings.height_in_mm + rings.position_top_ring_in_mm

        holder_solid = geant4.solid.GenericPolycone(
            "holder",
            0.0,
            2.0 * np.pi,
            pR=[outer_radius, outer_radius, max_radius, max_radius, outer_radius,
                outer_radius, outer_radius, 0.0, 0.0, inner_radius,
                inner_radius, inner_radius, inner_radius],
            pZ=[0.0, pos_top_ring_z, pos_top_ring_z, end_top_ring_z, end_top_ring_z,
                inner_height, outer_height, outer_height, inner_height, inner_height,
                end_top_ring_z, pos_top_ring_z, 0.0],
            lunit="mm",
            aunit="rad",
            registry=reg,
        )
    elif det_type == "icpc":
        msg = "ICPC holder python implementation not yet complete - use from_gdml=True"
        raise NotImplementedError(msg)
    else:
        msg = "cannot construct geometry for coax or ppc"
        raise NotImplementedError(msg)

    return geant4.LogicalVolume(holder_solid, en_aw_2011t8, "Holder", reg)


def create_bottom_plate(plate_metadata: AttrsDict, from_gdml: bool = True) -> geant4.Registry:
    """Create the bottom plate.

    Parameters
    ----------
    plate_metadata
        Metadata describing the position of the bottom plate.
        This should have the format:

        .. code-block:: yaml

            width: 100
            depth: 200
            height: 300
            cavity:
                width: 100
                depth: 200
                height: 200
    from_gdml
        Whether to construct from a GDML file

    """
    if from_gdml:
        dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "bottom_plate_dummy.gdml"

        replacements = {
            "bottom_plate_width": plate_metadata.width,
            "bottom_plate_depth": plate_metadata.depth,
            "bottom_plate_height": plate_metadata.height,
            "bottom_cavity_plate_width": plate_metadata.cavity.width,
            "bottom_cavity_plate_depth": plate_metadata.cavity.depth,
            "bottom_cavity_plate_height": plate_metadata.cavity.height,
        }
        return read_gdml_with_replacements(dummy_gdml_path, replacements)
    # Create bottom plate directly with pyg4ometry
    reg = geant4.Registry()

    # Define aluminum material
    al_mat = create_aluminum_material(reg)

    # Create bottom plate box
    bottom_plate_solid = geant4.solid.Box(
        "bottom_plate",
        plate_metadata.width,
        plate_metadata.depth,
        plate_metadata.height,
        reg,
        "mm"
    )

    # Create cavity box
    cavity_solid = geant4.solid.Box(
        "cavity_bottom_plate",
        plate_metadata.cavity.width,
        plate_metadata.cavity.depth,
        plate_metadata.cavity.height,
        reg,
        "mm"
    )

    # Create subtraction (cavity offset in y direction)
    cavity_offset = [0, plate_metadata.depth / 2.0, 0]
    final_solid = geant4.solid.Subtraction(
        "final_bottom_plate",
        bottom_plate_solid,
        cavity_solid,
        [[0, 0, 0], cavity_offset],
        reg
    )

    return geant4.LogicalVolume(final_solid, al_mat, "Bottom_plate", reg)


def create_lead_castle(
    table_num: int, castle_dimensions: AttrsDict, from_gdml: bool = True, volume_name: str = "Lead_castle"
) -> geant4.LogicalVolume:
    """Create the lead castle.

    Parameters
    ----------
    table_num
        Which table the measurements were taken on (1 or 2).
    castle_dimensions
        The metadata describing the lead castle dimensions. This should
        have the fields "base", "inner_cavity", "cavity",
        "top", "front" and "copper_plate".

        Each should have a subdictionary with this format:

        .. code-block:: yaml

            base:
                height: 100
                depth: 100
                width: 100
    volume_name
        Which volume to extract, defaults to "Lead_castle".

    from_gdml
        Whether to construct from a GDML file
    """

    if table_num not in [1, 2]:
        msg = f"Table number must be 1 or 2, not {table_num}"
        raise ValueError(msg)

    if from_gdml:
        dummy_gdml_path = (
            resources.files("pygeomhades") / "models" / "dummy" / f"lead_castle_table{table_num}_dummy.gdml"
        )

        if table_num == 1:
            replacements = {
                "base_width_1": castle_dimensions.base.width,
                "base_depth_1": castle_dimensions.base.depth,
                "base_height_1": castle_dimensions.base.height,
                "inner_cavity_width_1": castle_dimensions.inner_cavity.width,
                "inner_cavity_depth_1": castle_dimensions.inner_cavity.depth,
                "inner_cavity_height_1": castle_dimensions.inner_cavity.height,
                "cavity_width_1": castle_dimensions.cavity.width,
                "cavity_depth_1": castle_dimensions.cavity.depth,
                "cavity_height_1": castle_dimensions.cavity.height,
                "top_width_1": castle_dimensions.top.width,
                "top_depth_1": castle_dimensions.top.depth,
                "top_height_1": castle_dimensions.top.height,
                "front_width_1": castle_dimensions.front.width,
                "front_depth_1": castle_dimensions.front.depth,
                "front_height_1": castle_dimensions.front.height,
            }

        elif table_num == 2:
            replacements = {
                "base_width_2": castle_dimensions.base.width,
                "base_depth_2": castle_dimensions.base.depth,
                "base_height_2": castle_dimensions.base.height,
                "inner_cavity_width_2": castle_dimensions.inner_cavity.width,
                "inner_cavity_depth_2": castle_dimensions.inner_cavity.depth,
                "inner_cavity_height_2": castle_dimensions.inner_cavity.height,
                "top_width_2": castle_dimensions.top.width,
                "top_depth_2": castle_dimensions.top.depth,
                "top_height_2": castle_dimensions.top.height,
                "copper_plate_width": castle_dimensions.copper_plate.width,
                "copper_plate_depth": castle_dimensions.copper_plate.depth,
                "copper_plate_height": castle_dimensions.copper_plate.height,
            }

        return read_gdml_with_replacements(dummy_gdml_path, replacements, vol_name=volume_name)
    # Create lead castle directly with pyg4ometry
    reg = geant4.Registry()

    # Use predefined lead material
    pb_mat = geant4.MaterialPredefined("G4_Pb", reg)

    if table_num == 1:
        # Create all the boxes
        base_solid = geant4.solid.Box(
            "base_lead_castle_1",
            castle_dimensions.base.width,
            castle_dimensions.base.depth,
            castle_dimensions.base.height,
            reg,
            "mm"
        )

        inner_cavity_solid = geant4.solid.Box(
            "inner_cavity_base_1",
            castle_dimensions.inner_cavity.width,
            castle_dimensions.inner_cavity.depth,
            castle_dimensions.inner_cavity.height,
            reg,
            "mm"
        )

        cavity_solid = geant4.solid.Box(
            "cavity_base_1",
            castle_dimensions.cavity.width,
            castle_dimensions.cavity.depth,
            castle_dimensions.cavity.height,
            reg,
            "mm"
        )

        top_solid = geant4.solid.Box(
            "top_lead_castle_1",
            castle_dimensions.top.width,
            castle_dimensions.top.depth,
            castle_dimensions.top.height,
            reg,
            "mm"
        )

        front_solid = geant4.solid.Box(
            "front_1",
            castle_dimensions.front.width,
            castle_dimensions.front.depth,
            castle_dimensions.front.height,
            reg,
            "mm"
        )

        # Boolean operations to build the final geometry
        # pos_cavity_base: y=(inner_cavity_y/2+(base_y-inner_cavity_y)/4), z=(inner_cavity_z-cavity_z)/2
        pos_cavity_y = (castle_dimensions.inner_cavity.depth / 2.0 +
                       (castle_dimensions.base.depth - castle_dimensions.inner_cavity.depth) / 4.0)
        pos_cavity_z = (castle_dimensions.inner_cavity.height - castle_dimensions.cavity.height) / 2.0

        # Union: inner_cavity + cavity
        total_cavity = geant4.solid.Union(
            "total_cavity_1",
            inner_cavity_solid,
            cavity_solid,
            [[0, 0, 0], [0, pos_cavity_y, pos_cavity_z]],
            reg
        )

        # Subtraction: base - total_cavity
        base_cavity = geant4.solid.Subtraction(
            "base_cavity_1",
            base_solid,
            total_cavity,
            [[0, 0, 0], [0, 0, 0]],
            reg
        )

        # pos_top: z=-(base_z+top_z)/2 - 0.01
        pos_top_z = -(castle_dimensions.base.height + castle_dimensions.top.height) / 2.0 - 0.01

        # Union: base_cavity + top
        top_base = geant4.solid.Union(
            "top_base_1",
            base_cavity,
            top_solid,
            [[0, 0, 0], [0, 0, pos_top_z]],
            reg
        )

        # pos_front: y=(base_y+front_y)/2 - 0.01, z=(base_z-front_z)/2
        pos_front_y = (castle_dimensions.base.depth + castle_dimensions.front.depth) / 2.0 - 0.01
        pos_front_z = (castle_dimensions.base.height - castle_dimensions.front.height) / 2.0

        # Union: top_base + front
        final_solid = geant4.solid.Union(
            "final_lead_castle_1",
            top_base,
            front_solid,
            [[0, 0, 0], [0, pos_front_y, pos_front_z]],
            reg
        )

        return geant4.LogicalVolume(final_solid, pb_mat, "Lead_castle", reg)

    # table_num == 2
    msg = "Table 2 Python implementation not yet complete - use from_gdml=True"
    raise NotImplementedError(msg)


def create_source(
    source_type: str, source_dims: AttrsDict, holder_dims: AttrsDict | None, from_gdml: bool = False
) -> geant4.LogicalVolume:
    """Create the geometry of the source.

    Parameters
    ----------
    source_type
        The type of source (am_collimated, am, ba, co or th)
    source_dims
        Metadata describing the source geometry.
        Should be of the following format:

        .. code-block:: yaml

            height: 0.0
            width: 0.0

            foil:
                height: 0.0
                width: 0.0

            al_ring:
                height: 0.0
                width_max: 0.0
                width_min: 0.0

            capsule:
                width: 0.0
                depth: 0.0
                height: 0.0

            collimator:
                width: 0.0
                depth: 0.0
                height: 0.0
                beam_width: 0.0
                beam_height: 0.0
                window: 0.0

            epoxy:
                height: 0.0
                width: 0.0

            plates:
                height: 0.0
                width: 0.0
                cavity_width: 0.0

            offset_height: 0.0

    holder_dims
        Dimensions of the source holder (see :func:`get_source_holder`).

    from_gdml
        Whether to construct from a GDML file
    """

    if not from_gdml:
        msg = "cannot construct geometry without the gdml for now"
        raise NotImplementedError(msg)

    dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / f"source_{source_type}_dummy.gdml"

    if source_type == "am_collimated":
        replacements = {
            "source_height": source_dims.height,
            "source_width": source_dims.width,
            "source_capsule_height": source_dims.capsule.height,
            "source_capsule_width": source_dims.capsule.width,
            "window_source": source_dims.collimator.window,
            "collimator_height": source_dims.collimator.height,
            "collimator_depth": source_dims.collimator.depth,
            "collimator_width": source_dims.collimator.width,
            "collimator_beam_height": source_dims.collimator.beam_height,
            "collimator_beam_width": source_dims.collimator.beam_width,
        }

    elif source_type == "am":
        replacements = {
            "source_height": source_dims.height,
            "source_width": source_dims.width,
            "source_capsule_height": source_dims.capsule.height,
            "source_capsule_width": source_dims.capsule.width,
            "source_capsule_depth": source_dims.capsule.depth,
        }

    elif source_type in ["ba", "co"]:
        replacements = {
            "source_height": source_dims.height,
            "source_width": source_dims.width,
            "source_foil_height": source_dims.foil.height,
            "source_Alring_height": source_dims.al_ring.height,
            "source_Alring_width_min": source_dims.al_ring.width_min,
            "source_Alring_width_max": source_dims.al_ring.width_max,
        }

    elif source_type == "th":
        replacements = {
            "source_height": source_dims.height,
            "source_width": source_dims.width,
            "source_capsule_height": source_dims.capsule.height,
            "source_capsule_width": source_dims.capsule.width,
            "source_epoxy_height": source_dims.epoxy.height,
            "source_epoxy_width": source_dims.epoxy.width,
            "CuSource_holder_height": holder_dims.copper.height,
            "CuSource_holder_width": holder_dims.copper.width,
            "CuSource_holder_cavity_width": holder_dims.copper.cavity_width,
            "CuSource_holder_bottom_height": holder_dims.copper.bottom_height,
            "CuSource_holder_bottom_width": holder_dims.copper.bottom_width,
            "source_offset_height": source_dims.offset_height,
        }

    else:
        msg = f"source type of {source_type} is not defined."
        raise RuntimeError(msg)

    return read_gdml_with_replacements(dummy_gdml_path, replacements)


def create_th_plate(source_dims: AttrsDict, from_gdml: bool = False) -> geant4.LogicalVolume:
    """Construct the plate for the Th source

    Parameters
    ----------
    source_dims
        See :func:`create_source` for more information.
    from_gdml
        Whether to construct from a GDML file

    """
    if from_gdml:
        dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "source_th_plates_dummy.gdml"
        source = source_dims

        replacements = {
            "source_plates_height": source.plates.height,
            "source_plates_width": source.plates.width,
            "source_plates_cavity_width": source.plates.cavity_width,
        }

        return read_gdml_with_replacements(dummy_gdml_path, replacements)
    # Create th plate directly with pyg4ometry
    reg = geant4.Registry()

    # Use predefined lead material
    pb_mat = geant4.MaterialPredefined("G4_Pb", reg)

    # Create tube solid
    source_plates_z = source_dims.plates.height
    source_plates_radius = source_dims.plates.width / 2.0
    source_plates_cavity_radius = source_dims.plates.cavity_width / 2.0

    source_plates_solid = geant4.solid.Tubs(
        "source_plates",
        source_plates_cavity_radius,
        source_plates_radius,
        source_plates_z,
        0.0,
        2.0 * np.pi,
        reg,
        "mm",
        "rad"
    )

    return geant4.LogicalVolume(source_plates_solid, pb_mat, "Source_Plates", reg)


def create_source_holder(
    source_type: str, holder_dims: AttrsDict, source_z: float, meas_type: str = "lat", from_gdml: bool = True
) -> geant4.LogicalVolume:
    """Get the source holder geometry.

    Parameters
    ----------
    source_type
        The type of source (am_collimated, am, ba, co or th)
    holder_dims
        The dimensions of the source holder, should be of the format:

        .. code-block:: yaml

            source:
                top_plate_height: 10.0
                top_plate_width: 10.0
                top_height: 2.0
                top_inner_width: 2.0
                top_bottom_height: 2.0
                bottom_inner_width: 2.0
            outer_width: 100.0
            inner_width: 10.0


    meas_type
        The measurement type (for th only) either lat or top.
    source_z
        The z position of the source from the cryostat bottom.
    from_gdml
        Whether to construct from a GDML file
    """

    if not from_gdml:
        msg = "cannot construct geometry without the gdml for now"
        raise NotImplementedError(msg)

    source_holder = holder_dims
    dummy_path = resources.files("pygeomhades") / "models" / "dummy"

    if source_type == "th" and meas_type == "lat":
        dummy_gdml_path = dummy_path / "source_holder_th_lat_dummy.gdml"

        replacements = {
            "cavity_source_holder_height": source_holder.source.cavity_height,
            "source_holder_height": source_holder.source.height,
            "source_holder_outer_width": source_holder.outer_width,
            "source_holder_inner_width": source_holder.inner_width,
            "cavity_source_holder_width": source_holder.holder_width,
        }

    elif source_type in ["am_collimated", "ba", "co", "th"]:
        dummy_gdml_path = dummy_path / "source_holder_dummy.gdml"

        replacements = {
            "source_holder_top_plate_height": source_holder.source.top_plate_height,
            "source_holder_top_height": source_holder.source.top_height,
            "source_holder_topbottom_height": source_holder.source.top_bottom_height,
            "source_holder_top_plate_width": source_holder.source.top_plate_width,
            "source_holder_top_inner_width": source_holder.source.top_inner_width,
            "source_holder_inner_width": source_holder.inner_width,
            "source_holder_bottom_inner_width": source_holder.source.bottom_inner_width,
            "source_holder_outer_width": source_holder.outer_width,
            "position_source_fromcryostat_z": source_z,
        }

    elif source_type == "am":
        dummy_gdml_path = dummy_path / "source_holder_am_dummy.gdml"

        replacements = {
            "source_holder_top_height": source_holder.source.top_height,
            "position_source_fromcryostat_z": source_z,
            "source_holder_top_plate_height": source_holder.source.top_plate_height,
            "source_holder_top_plate_width": source_holder.source.top_plate_width,
            "source_holder_top_plate_depth": source_holder.source.top_plate_depth,
            "source_holder_topbottom_height": source_holder.source.top_bottom_height,
            "source_holder_top_inner_width": source_holder.source.top_inner_width,
            "source_holder_top_inner_depth": source_holder.source.top_inner_depth,
            "source_holder_inner_width": source_holder.inner_width,
            "source_holder_bottom_inner_width": source_holder.source.bottom_inner_width,
            "source_holder_outer_width": source_holder.outer_width,
        }

    else:
        msg = f"source type {source_type} not implemented."
        raise RuntimeError(msg)

    return read_gdml_with_replacements(dummy_gdml_path, replacements)


def create_cryostat(cryostat_meta: AttrsDict, from_gdml: bool = True) -> geant4.LogicalVolume:
    """Create the cryostat logical volume.

    Parameters
    ----------
    cryostat_meta
        Metadata describing the cryostat geometry (see :func:`create_wrap`) for details.
    from_gdml
        Whether to construct from a GDML file

    """

    if from_gdml:
        dummy_gdml_path = resources.files("pygeomhades") / "models" / "dummy" / "cryostat_dummy.gdml"

        replacements = {
            "cryostat_height": cryostat_meta.height,
            "cryostat_width": cryostat_meta.width,
            "cryostat_thickness": cryostat_meta.thickness,
            "position_cryostat_cavity_fromTop": cryostat_meta.position_cavity_from_top,
            "position_cryostat_cavity_fromBottom": cryostat_meta.position_cavity_from_bottom,
        }
        return read_gdml_with_replacements(dummy_gdml_path, replacements)
    # Create cryostat directly with pyg4ometry
    reg = geant4.Registry()

    # Define EN_AW-2011T8 material (aluminum alloy)
    en_aw_2011t8 = create_en_aw_2011t8_material(reg)

    # Calculate dimensions
    cryostat_height = cryostat_meta.height
    cryostat_radius = cryostat_meta.width / 2.0
    cryostat_cavity_radius = (cryostat_meta.width - 2 * cryostat_meta.thickness) / 2.0
    start_cavity_z = cryostat_meta.position_cavity_from_top
    end_cavity_z = cryostat_height - cryostat_meta.position_cavity_from_bottom

    # Create polycone solid
    cryostat_solid = geant4.solid.GenericPolycone(
        "cryostat",
        0.0,
        2.0 * np.pi,
        pR=[0.0, cryostat_radius, cryostat_radius, cryostat_cavity_radius,
            cryostat_cavity_radius, 0.0, 0.0, cryostat_radius, cryostat_radius, 0.0],
        pZ=[0.0, 0.0, start_cavity_z, start_cavity_z, end_cavity_z,
            end_cavity_z, end_cavity_z, end_cavity_z, cryostat_height, cryostat_height],
        lunit="mm",
        aunit="rad",
        registry=reg,
    )

    return geant4.LogicalVolume(cryostat_solid, en_aw_2011t8, "Cryostat", reg)
