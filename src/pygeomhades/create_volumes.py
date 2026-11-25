from __future__ import annotations

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import get_material


def _polycone(
    name: str, planes: list[tuple[float, float, float]], registry: geant4.Registry
) -> geant4.solid.Polycone:
    """Full-turn polycone from a list of ``(z, r_min, r_max)`` planes, in mm."""
    z, r_min, r_max = zip(*planes, strict=True)
    return geant4.solid.Polycone(
        name, 0, 2 * np.pi, list(z), list(r_min), list(r_max), registry
    )


def _tube(
    name: str,
    r_max: float,
    height: float,
    registry: geant4.Registry,
    r_min: float = 0,
) -> geant4.solid.Tubs:
    """Full-turn tube, with dimensions in mm (`height` is the full length)."""
    return geant4.solid.Tubs(name, r_min, r_max, height, 0, 2 * np.pi, registry)


def _place(
    lv: geant4.LogicalVolume,
    mother: geant4.LogicalVolume,
    registry: geant4.Registry,
    z: float = 0,
) -> None:
    """Place `lv` inside `mother`, shifted by `z` mm along the z axis."""
    geant4.PhysicalVolume([0, 0, 0], [0, 0, z], lv, f"{lv.name}_PV", mother, registry)


def create_vacuum_cavity(
    cryostat_metadata: AttrsDict, registry: geant4.Registry
) -> geant4.LogicalVolume:
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
    vacuum_cavity_radius = (
        cryostat_metadata["width"] - 2 * cryostat_metadata["thickness"]
    ) / 2
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


def create_wrap(wrap_metadata: AttrsDict) -> geant4.LogicalVolume:
    """Create the detector wrap (HD1000 polyethylene).

    .. warning::

        The returned logical volume belongs to its own registry,
        it is necessary to call :func:`reg.addVolumeRecursive` on
        the produced PhysicalVolume to get a sane registry.

    Parameters
    ----------
    wrap_metadata
        The dimensions of the wrap,
        should be of the format:

        .. code-block:: yaml

            outer:
                height_in_mm: 100
                radius_in_mm: 100
            inner:
                height_in_mm: 99
                radius_in_mm: 99
    """
    # cup closed at z = 0
    reg = geant4.Registry()
    r_out = wrap_metadata.outer.radius_in_mm
    r_in = wrap_metadata.inner.radius_in_mm
    height = wrap_metadata.outer.height_in_mm
    top = height - wrap_metadata.inner.height_in_mm

    wrap = _polycone(
        "wrap",
        [(0, 0, r_out), (top, 0, r_out), (top, r_in, r_out), (height, r_in, r_out)],
        reg,
    )
    return geant4.LogicalVolume(wrap, get_material("hd1000", reg), "Wrap", reg)


def create_holder(
    holder_meta: AttrsDict, det_type: str, order: int
) -> geant4.LogicalVolume:
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
    order
        The detector batch number.

    det_type
        Detector type.
    """
    reg = geant4.Registry()
    cyl = holder_meta.cylinder
    r_in = cyl.inner.radius_in_mm
    r_out = cyl.outer.radius_in_mm
    h_in = cyl.inner.height_in_mm
    h_out = cyl.outer.height_in_mm

    if det_type == "icpc":
        # cylinder open at z = 0, with an annular bottom continued by a
        # smaller closed cylinder (the "bottom cylinder")
        bot = holder_meta.bottom_cyl
        b_in = bot.inner.radius_in_mm
        b_out = bot.outer.radius_in_mm
        bottom_planes = [
            (h_in, r_in, r_out),
            (h_in, b_in, r_out),
            (h_out, b_in, r_out),
            (h_out, b_in, b_out),
            (h_in + bot.inner.height_in_mm, b_in, b_out),
            (h_in + bot.inner.height_in_mm, 0, b_out),
            (h_out + bot.outer.height_in_mm, 0, b_out),
        ]

        if order == 6:
            # batch 6 holders have no rings
            planes = [(0, r_in, r_out), *bottom_planes]
        else:
            # a lip at z = 0 and two rings, all with the maximum radius
            rings = holder_meta.rings
            r_max = rings.radius_in_mm
            edge = holder_meta.edge.height_in_mm
            planes = [(0, r_in, r_max), (edge, r_in, r_max), (edge, r_in, r_out)]
            for start in (
                rings.position_top_ring_in_mm,
                rings.position_bottom_ring_in_mm,
            ):
                end = start + rings.height_in_mm
                planes += [
                    (start, r_in, r_out),
                    (start, r_in, r_max),
                    (end, r_in, r_max),
                    (end, r_in, r_out),
                ]
            planes += bottom_planes

    elif det_type == "bege":
        # cup open at z = 0, closed at the top, with one ring
        rings = holder_meta.rings
        r_max = rings.radius_in_mm
        start = rings.position_top_ring_in_mm
        end = start + rings.height_in_mm
        planes = [
            (0, r_in, r_out),
            (start, r_in, r_out),
            (start, r_in, r_max),
            (end, r_in, r_max),
            (end, r_in, r_out),
            (h_in, r_in, r_out),
            (h_in, 0, r_out),
            (h_out, 0, r_out),
        ]
    else:
        msg = "cannot construct geometry for coax or ppc"
        raise NotImplementedError(msg)

    holder = _polycone("holder", planes, reg)
    return geant4.LogicalVolume(
        holder, get_material("en_aw_2011t8", reg), "Holder", reg
    )


def create_bottom_plate(plate_metadata: AttrsDict) -> geant4.LogicalVolume:
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
    """
    # box with a cavity centered on its edge at y = +depth/2
    reg = geant4.Registry()
    p, cav = plate_metadata, plate_metadata.cavity
    plate = geant4.solid.Subtraction(
        "final_bottom_plate",
        geant4.solid.Box("bottom_plate", p.width, p.depth, p.height, reg),
        geant4.solid.Box("cavity_bottom_plate", cav.width, cav.depth, cav.height, reg),
        [[0, 0, 0], [0, p.depth / 2, 0]],
        reg,
    )
    return geant4.LogicalVolume(
        plate, get_material("aluminium", reg), "Bottom_plate", reg
    )


def create_lead_castle(
    table_num: int, castle_dimensions: AttrsDict
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
    """
    if table_num not in [1, 2]:
        msg = f"Table number must be 1 or 2, not {table_num}"
        raise ValueError(msg)

    reg = geant4.Registry()
    dims = castle_dimensions

    def box(name, d):
        return geant4.solid.Box(name, d.width, d.depth, d.height, reg)

    if table_num == 1:
        # the cavity is the inner cavity plus a box shifted towards +y
        cavity = geant4.solid.Union(
            "total_cavity_1",
            box("inner_cavity_base_1", dims.inner_cavity),
            box("cavity_base_1", dims.cavity),
            [
                [0, 0, 0],
                [
                    0,
                    dims.inner_cavity.depth / 2
                    + (dims.base.depth - dims.inner_cavity.depth) / 4,
                    (dims.inner_cavity.height - dims.cavity.height) / 2,
                ],
            ],
            reg,
        )
        castle = geant4.solid.Subtraction(
            "base_cavity_1",
            box("base_lead_castle_1", dims.base),
            cavity,
            [[0, 0, 0], [0, 0, 0]],
            reg,
        )
        # the top and front blocks overlap the base by 0.01 mm, so that
        # the union has no coincident surfaces
        castle = geant4.solid.Union(
            "top_base_1",
            castle,
            box("top_lead_castle_1", dims.top),
            [[0, 0, 0], [0, 0, -(dims.base.height + dims.top.height) / 2 - 0.01]],
            reg,
        )
        castle = geant4.solid.Union(
            "final_lead_castle_1",
            castle,
            box("front_1", dims.front),
            [
                [0, 0, 0],
                [
                    0,
                    (dims.base.depth + dims.front.depth) / 2 - 0.01,
                    (dims.base.height - dims.front.height) / 2,
                ],
            ],
            reg,
        )
        return geant4.LogicalVolume(
            castle, get_material("lead", reg), "Lead_castle", reg
        )

    # table 2: the top block is separated from the base by the copper plate
    cu_height = dims.copper_plate.height
    castle = geant4.solid.Subtraction(
        "base_cavity_2",
        box("base_lead_castle_2", dims.base),
        box("inner_cavity_lead_castle_2", dims.inner_cavity),
        [[0, 0, 0], [0, 0, 0]],
        reg,
    )
    castle = geant4.solid.Union(
        "final_lead_castle_2",
        castle,
        box("top_lead_castle_2", dims.top),
        [
            [0, 0, 0],
            [0, 0, -((dims.base.height + dims.top.height) / 2 + cu_height)],
        ],
        reg,
    )
    castle_lv = geant4.LogicalVolume(
        castle, get_material("lead_table2", reg), "Lead_castle", reg
    )
    # FIXME: the copper plate lies in the gap between base and top, i.e.
    # outside of its mother volume
    plate_lv = geant4.LogicalVolume(
        box("copper_plate", dims.copper_plate),
        get_material("copper", reg),
        "Copper_plate",
        reg,
    )
    _place(plate_lv, castle_lv, reg, z=-(dims.base.height + cu_height) / 2)
    return castle_lv


def create_source(
    source_type: str, source_dims: AttrsDict, holder_dims: AttrsDict | None
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
    """
    reg = geant4.Registry()
    d = source_dims

    def lv(solid, material, name):
        return geant4.LogicalVolume(solid, get_material(material, reg), name, reg)

    if source_type == "am_HS1":
        # encapsulated source inside a collimator with a cylindrical beam
        # channel above it
        col = d.collimator
        source = lv(_tube("source", d.width / 2, d.height, reg), "quartz", "Source")
        capsule = lv(
            _tube("source_capsule", d.capsule.width / 2, d.capsule.height, reg),
            "steel",
            "Source_Encapsulated",
        )
        _place(source, capsule, reg, z=(d.capsule.height - d.height) / 2 - col.window)
        beam = lv(
            _tube("collimator_beam", col.beam_width / 2, col.beam_height, reg),
            "air",
            "Collimator_Beam",
        )
        top = lv(
            geant4.solid.Box("collimator", col.width, col.depth, col.height, reg),
            "G4_Cu",
            "Source_Collimated",
        )
        _place(beam, top, reg, z=(col.height - col.beam_height) / 2)
        _place(
            capsule,
            top,
            reg,
            z=-d.capsule.height / 2 - col.beam_height + col.height / 2,
        )

    elif source_type == "am_HS6":
        source = lv(_tube("source", d.width / 2, d.height, reg), "acrylic", "Source")
        top = lv(
            geant4.solid.Box(
                "source_capsule",
                d.capsule.width,
                d.capsule.depth,
                d.capsule.height,
                reg,
            ),
            "acrylic",
            "Source_Encapsulated",
        )
        _place(source, top, reg)

    elif source_type in ["ba_HS4", "co_HS5"]:
        # source on a foil, surrounded by an aluminium ring
        ring = d.al_ring
        source = lv(_tube("source", d.width / 2, d.height, reg), "hd1000", "Source")
        foil = lv(
            _tube("source_foil", ring.width_min / 2, d.foil.height, reg),
            "hd1000",
            "Source_foil",
        )
        _place(source, foil, reg)
        al_ring = lv(
            _tube(
                "source_Alring",
                ring.width_max / 2,
                ring.height,
                reg,
                r_min=ring.width_min / 2,
            ),
            "aluminium",
            "Source_Alring",
        )
        top = lv(
            _tube("source_vacuum", ring.width_max / 2, ring.height, reg),
            "vacuum",
            "Source_Encapsulated",
        )
        _place(foil, top, reg)
        _place(al_ring, top, reg)

    elif source_type == "th_HS2":
        # encapsulated source with epoxy, in the air cavity of a copper
        # holder. The copper holder is a cylinder with a narrower bottom.
        cu = d.copper
        cu_all_height = cu.height + cu.bottom_height
        source = lv(_tube("source", d.width / 2, d.height, reg), "quartz", "Source")
        epoxy = lv(
            _tube("source_epoxy", d.epoxy.width / 2, d.epoxy.height, reg),
            "epoxy",
            "Source_Epoxy",
        )
        capsule = lv(
            _tube("source_capsule", d.capsule.width / 2, d.capsule.height, reg),
            "steel",
            "Source_Encapsulated",
        )
        _place(source, capsule, reg)
        _place(epoxy, capsule, reg, z=(d.capsule.height - d.epoxy.height) / 2)
        cavity = lv(
            _polycone(
                "CuSource_holder_cavity",
                [
                    (0, 0, cu.cavity_width / 2),
                    (cu_all_height, 0, cu.cavity_width / 2),
                ],
                reg,
            ),
            "air",
            "CuSource_Holder_Cavity",
        )
        _place(
            capsule,
            cavity,
            reg,
            z=cu_all_height - d.capsule.height / 2 - d.offset_height,
        )
        top = lv(
            _polycone(
                "CuSource_holder",
                [
                    (0, 0, cu.width / 2),
                    (cu.height, 0, cu.width / 2),
                    (cu.height, 0, cu.bottom_width / 2),
                    (cu_all_height, 0, cu.bottom_width / 2),
                ],
                reg,
            ),
            "copper",
            "CuSource_Holder",
        )
        _place(cavity, top, reg)

    else:
        msg = f"source type of {source_type} is not defined."
        raise RuntimeError(msg)

    return top


def create_th_plate(source_dims: AttrsDict) -> geant4.LogicalVolume:
    """Construct the plate for the Th source

    Parameters
    ----------
    source_dims
        See :func:`create_source` for more information.
    """
    reg = geant4.Registry()
    plates = source_dims.plates
    tube = _tube(
        "source_plates",
        plates.width / 2,
        plates.height,
        reg,
        r_min=plates.cavity_width / 2,
    )
    return geant4.LogicalVolume(tube, get_material("G4_Pb", reg), "Source_Plates", reg)


def create_source_holder(
    source_type: str, holder_dims: AttrsDict, source_z: float, meas_type: str = "lat"
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
    """
    reg = geant4.Registry()
    h = holder_dims
    r_out = h.outer_width / 2
    r_in = h.inner_width / 2

    if source_type in ["am_HS1", "ba_HS4", "co_HS5", "th_HS2"] and meas_type == "lat":
        # tube around the cryostat, with a radial hole for the source
        holder = geant4.solid.Subtraction(
            "source_holder",
            _tube("cylinder_source_holder", r_out, h.height, reg, r_min=r_in),
            _tube("cavity_source_holder", h.cavity_width / 2, h.cavity_height, reg),
            [[np.pi / 2, 0, 0], [0, (r_in + r_out) / 2, 0]],
            reg,
        )

    elif source_type in ["am_HS1", "ba_HS4", "co_HS5", "th_HS2", "am_HS6"]:
        # cap on top of the cryostat (z = 0), with a pocket for the source
        # in the top plate, extending down to the source position
        s = h.source
        z_cryo = source_z + s.top_plate_height / 2
        z_end = source_z + s.top_bottom_height
        sides = [
            (s.top_height, r_in, r_out),
            (z_cryo, r_in, r_out),
            (z_cryo, s.bottom_inner_width / 2, r_out),
            (z_end, s.bottom_inner_width / 2, r_out),
        ]

        if source_type != "am_HS6":
            holder = _polycone(
                "source_holder",
                [
                    (0, s.top_plate_width / 2, r_out),
                    (s.top_plate_height, s.top_plate_width / 2, r_out),
                    (s.top_plate_height, s.top_inner_width / 2, r_out),
                    (s.top_height, s.top_inner_width / 2, r_out),
                    *sides,
                ],
                reg,
            )
        else:
            # the pockets for the Am HS6 source are rectangular
            holder = geant4.solid.Subtraction(
                "source_holder_endcap",
                _polycone(
                    "source_holder_cylinder",
                    [(0, 0, r_out), (s.top_height, 0, r_out), *sides],
                    reg,
                ),
                geant4.solid.Box(
                    "rectangular_plate",
                    s.top_plate_width,
                    s.top_plate_depth,
                    s.top_plate_height,
                    reg,
                ),
                [[0, 0, 0], [0, 0, s.top_plate_height / 2]],
                reg,
            )
            holder = geant4.solid.Subtraction(
                "source_holder_sub",
                holder,
                geant4.solid.Box(
                    "source_holder_top_inner",
                    s.top_inner_width,
                    s.top_inner_depth,
                    s.top_height,
                    reg,
                ),
                [[0, 0, 0], [0, 0, s.top_height / 2 + s.top_plate_height]],
                reg,
            )
    else:
        msg = f"source type {source_type} not implemented."
        raise RuntimeError(msg)

    return geant4.LogicalVolume(
        holder, get_material("acrylic_source_holder", reg), "Source_Holder", reg
    )


def create_cryostat(cryostat_meta: AttrsDict) -> geant4.LogicalVolume:
    """Create the cryostat logical volume.

    Parameters
    ----------
    cryostat_meta
        Metadata describing the cryostat geometry (see :func:`create_vacuum_cavity`).
    """
    # closed cylinder with a vacuum cavity. z = 0 is the cryostat top.
    reg = geant4.Registry()
    r_out = cryostat_meta.width / 2
    r_in = r_out - cryostat_meta.thickness
    start = cryostat_meta.position_cavity_from_top
    end = cryostat_meta.height - cryostat_meta.position_cavity_from_bottom

    cryostat = _polycone(
        "cryostat",
        [
            (0, 0, r_out),
            (start, 0, r_out),
            (start, r_in, r_out),
            (end, r_in, r_out),
            (end, 0, r_out),
            (cryostat_meta.height, 0, r_out),
        ],
        reg,
    )
    return geant4.LogicalVolume(
        cryostat, get_material("en_aw_2011t8", reg), "Cryostat", reg
    )
