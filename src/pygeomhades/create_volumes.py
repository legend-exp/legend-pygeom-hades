"""Construction of the HADES geometry components.

All dimensions are in mm and are read from the HADES metadata (``hardware/``
folder of hades-metadata). Each function returns a logical volume.
"""

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


def _box(name: str, dims: AttrsDict, registry: geant4.Registry) -> geant4.solid.Box:
    """Box from the ``width_in_mm``, ``depth_in_mm`` and ``height_in_mm`` fields."""
    return geant4.solid.Box(
        name, dims.width_in_mm, dims.depth_in_mm, dims.height_in_mm, registry
    )


def _place(
    lv: geant4.LogicalVolume,
    mother: geant4.LogicalVolume,
    registry: geant4.Registry,
    z: float = 0,
) -> None:
    """Place `lv` inside `mother`, shifted by `z` mm along the z axis."""
    geant4.PhysicalVolume([0, 0, 0], [0, 0, z], lv, f"{lv.name}_PV", mother, registry)


def create_vacuum_cavity(
    cryostat: AttrsDict, registry: geant4.Registry
) -> geant4.LogicalVolume:
    """Construct the vacuum cavity of the cryostat.

    `cryostat` is the ``cryostat`` block of ``hardware/cryostat/<detector>``.
    The cavity starts at z = 0.
    """
    radius = cryostat.width_in_mm / 2 - cryostat.thickness_in_mm
    height = (
        cryostat.height_in_mm
        - cryostat.position_cavity_from_top_in_mm
        - cryostat.position_cavity_from_bottom_in_mm
    )
    vacuum_cavity = geant4.solid.GenericPolycone(
        "vacuum_cavity",
        0.0,
        2.0 * np.pi,
        pR=[0.0, radius, radius, 0.0],
        pZ=[0.0, 0.0, height, height],
        lunit="mm",
        aunit="rad",
        registry=registry,
    )
    return geant4.LogicalVolume(vacuum_cavity, "G4_Galactic", "cavity_lv", registry)


def create_cryostat(cryostat: AttrsDict) -> geant4.LogicalVolume:
    """Create the cryostat, a closed cylinder with a vacuum cavity.

    `cryostat` is the ``cryostat`` block of ``hardware/cryostat/<detector>``.
    z = 0 is the cryostat top.
    """
    reg = geant4.Registry()
    r_out = cryostat.width_in_mm / 2
    r_in = r_out - cryostat.thickness_in_mm
    start = cryostat.position_cavity_from_top_in_mm
    end = cryostat.height_in_mm - cryostat.position_cavity_from_bottom_in_mm

    solid = _polycone(
        "cryostat",
        [
            (0, 0, r_out),
            (start, 0, r_out),
            (start, r_in, r_out),
            (end, r_in, r_out),
            (end, 0, r_out),
            (cryostat.height_in_mm, 0, r_out),
        ],
        reg,
    )
    return geant4.LogicalVolume(
        solid, get_material("en_aw_2011t8", reg), "Cryostat", reg
    )


def create_wrap(wrap_metadata: AttrsDict) -> geant4.LogicalVolume:
    """Create the detector wrap (HD1000 polyethylene), a cup closed at z = 0.

    `wrap_metadata` is the ``wrap.geometry`` block of
    ``hardware/cryostat/<detector>``.

    .. warning::

        The returned logical volume belongs to its own registry,
        it is necessary to call :func:`reg.addVolumeRecursive` on
        the produced PhysicalVolume to get a sane registry.
    """
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
    """Create the detector holder.

    Parameters
    ----------
    holder_meta
        The ``holder.geometry`` block of ``hardware/cryostat/<detector>``.
    det_type
        Detector type (``icpc`` or ``bege``).
    order
        The detector production batch.
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


def create_bottom_plate(plate: AttrsDict) -> geant4.LogicalVolume:
    """Create the bottom plate, a box with a cavity centered on its edge at y = +depth/2.

    `plate` is ``hardware/setup/bottom_plate``.
    """
    reg = geant4.Registry()
    solid = geant4.solid.Subtraction(
        "final_bottom_plate",
        _box("bottom_plate", plate, reg),
        _box("cavity_bottom_plate", plate.cavity, reg),
        [[0, 0, 0], [0, plate.depth_in_mm / 2, 0]],
        reg,
    )
    return geant4.LogicalVolume(
        solid, get_material("aluminium", reg), "Bottom_plate", reg
    )


def create_lead_castle(table_num: int, dims: AttrsDict) -> geant4.LogicalVolume:
    """Create the lead castle of table 1 or 2.

    `dims` is ``hardware/setup/lead_castle/table<table_num>``.
    """
    reg = geant4.Registry()

    if table_num == 1:
        # the cavity is the inner cavity plus a box shifted towards +y
        cavity = geant4.solid.Union(
            "total_cavity_1",
            _box("inner_cavity_base_1", dims.inner_cavity, reg),
            _box("cavity_base_1", dims.cavity, reg),
            [
                [0, 0, 0],
                [
                    0,
                    dims.inner_cavity.depth_in_mm / 2
                    + (dims.base.depth_in_mm - dims.inner_cavity.depth_in_mm) / 4,
                    (dims.inner_cavity.height_in_mm - dims.cavity.height_in_mm) / 2,
                ],
            ],
            reg,
        )
        castle = geant4.solid.Subtraction(
            "base_cavity_1",
            _box("base_lead_castle_1", dims.base, reg),
            cavity,
            [[0, 0, 0], [0, 0, 0]],
            reg,
        )
        # the top and front blocks overlap the base by 0.01 mm, so that
        # the union has no coincident surfaces
        castle = geant4.solid.Union(
            "top_base_1",
            castle,
            _box("top_lead_castle_1", dims.top, reg),
            [
                [0, 0, 0],
                [0, 0, -(dims.base.height_in_mm + dims.top.height_in_mm) / 2 - 0.01],
            ],
            reg,
        )
        castle = geant4.solid.Union(
            "final_lead_castle_1",
            castle,
            _box("front_1", dims.front, reg),
            [
                [0, 0, 0],
                [
                    0,
                    (dims.base.depth_in_mm + dims.front.depth_in_mm) / 2 - 0.01,
                    (dims.base.height_in_mm - dims.front.height_in_mm) / 2,
                ],
            ],
            reg,
        )
        return geant4.LogicalVolume(
            castle, get_material("lead", reg), "Lead_castle", reg
        )

    # table 2: the top block is separated from the base by the copper plate
    cu_height = dims.copper_plate.height_in_mm
    castle = geant4.solid.Subtraction(
        "base_cavity_2",
        _box("base_lead_castle_2", dims.base, reg),
        _box("inner_cavity_lead_castle_2", dims.inner_cavity, reg),
        [[0, 0, 0], [0, 0, 0]],
        reg,
    )
    castle = geant4.solid.Union(
        "final_lead_castle_2",
        castle,
        _box("top_lead_castle_2", dims.top, reg),
        [
            [0, 0, 0],
            [0, 0, -((dims.base.height_in_mm + dims.top.height_in_mm) / 2 + cu_height)],
        ],
        reg,
    )
    castle_lv = geant4.LogicalVolume(
        castle, get_material("lead_table2", reg), "Lead_castle", reg
    )
    # FIXME: the copper plate lies in the gap between base and top, i.e.
    # outside of its mother volume
    plate_lv = geant4.LogicalVolume(
        _box("copper_plate", dims.copper_plate, reg),
        get_material("copper", reg),
        "Copper_plate",
        reg,
    )
    _place(plate_lv, castle_lv, reg, z=-(dims.base.height_in_mm + cu_height) / 2)
    return castle_lv


def create_source(
    source_type: str, dims: AttrsDict, position: str
) -> geant4.LogicalVolume:
    """Create the source with its capsule, collimator or holder.

    Parameters
    ----------
    source_type
        The source name, e.g. ``th_HS2``.
    dims
        ``hardware/sources/<source_type>``.
    position
        The measurement position (``top`` or ``lat``).
    """
    reg = geant4.Registry()
    d = dims

    def lv(solid, material, name):
        return geant4.LogicalVolume(solid, get_material(material, reg), name, reg)

    def source(material):
        return lv(
            _tube("source", d.width_in_mm / 2, d.height_in_mm, reg), material, "Source"
        )

    if source_type == "am_HS1":
        # encapsulated source inside a collimator with a cylindrical beam
        # channel above it
        col = d.collimator
        cap_height = d.capsule.height_in_mm
        src = source("quartz")
        capsule = lv(
            _tube("source_capsule", d.capsule.width_in_mm / 2, cap_height, reg),
            "steel",
            "Source_Encapsulated",
        )
        _place(
            src, capsule, reg, z=(cap_height - d.height_in_mm) / 2 - col.window_in_mm
        )
        beam = lv(
            _tube(
                "collimator_beam",
                col.beam_width_in_mm / 2,
                col.beam_height_in_mm,
                reg,
            ),
            "air",
            "Collimator_Beam",
        )
        top = lv(_box("collimator", col, reg), "G4_Cu", "Source_Collimated")
        _place(beam, top, reg, z=(col.height_in_mm - col.beam_height_in_mm) / 2)
        _place(
            capsule,
            top,
            reg,
            z=-cap_height / 2 - col.beam_height_in_mm + col.height_in_mm / 2,
        )

    elif source_type == "am_HS6":
        src = source("acrylic")
        top = lv(
            _box("source_capsule", d.capsule, reg), "acrylic", "Source_Encapsulated"
        )
        _place(src, top, reg)

    elif source_type in ["ba_HS4", "co_HS5"]:
        # source on a foil, surrounded by an aluminium ring
        ring = d.al_ring
        src = source("hd1000")
        foil = lv(
            _tube("source_foil", d.foil.width_in_mm / 2, d.foil.height_in_mm, reg),
            "hd1000",
            "Source_foil",
        )
        _place(src, foil, reg)
        al_ring = lv(
            _tube(
                "source_Alring",
                ring.width_max_in_mm / 2,
                ring.height_in_mm,
                reg,
                r_min=ring.width_min_in_mm / 2,
            ),
            "aluminium",
            "Source_Alring",
        )
        top = lv(
            _tube("source_vacuum", ring.width_max_in_mm / 2, ring.height_in_mm, reg),
            "vacuum",
            "Source_Encapsulated",
        )
        _place(foil, top, reg)
        _place(al_ring, top, reg)

    elif source_type == "th_HS2":
        # encapsulated source with epoxy, in the air cavity of a copper
        # holder. The copper holder is a cylinder with a wider bottom.
        cu = d.copper
        cu_all_height = cu.height_in_mm + cu.bottom_height_in_mm
        cap_height = d.capsule.height_in_mm
        src = source("quartz")
        epoxy = lv(
            _tube("source_epoxy", d.epoxy.width_in_mm / 2, d.epoxy.height_in_mm, reg),
            "epoxy",
            "Source_Epoxy",
        )
        capsule = lv(
            _tube("source_capsule", d.capsule.width_in_mm / 2, cap_height, reg),
            "steel",
            "Source_Encapsulated",
        )
        _place(src, capsule, reg)
        _place(epoxy, capsule, reg, z=(cap_height - d.epoxy.height_in_mm) / 2)
        cavity = lv(
            _polycone(
                "CuSource_holder_cavity",
                [
                    (0, 0, cu.cavity_width_in_mm / 2),
                    (cu_all_height, 0, cu.cavity_width_in_mm / 2),
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
            z=cu_all_height - cap_height / 2 - d.offset_height_in_mm[position],
        )
        top = lv(
            _polycone(
                "CuSource_holder",
                [
                    (0, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.bottom_width_in_mm / 2),
                    (cu_all_height, 0, cu.bottom_width_in_mm / 2),
                ],
                reg,
            ),
            "copper",
            "CuSource_Holder",
        )
        _place(cavity, top, reg)

    else:
        msg = f"source type {source_type} is not implemented"
        raise NotImplementedError(msg)

    return top


def create_th_plate(plates: AttrsDict) -> geant4.LogicalVolume:
    """Create the Pb plates (an annulus) of the Th source.

    `plates` is the ``plates`` block of ``hardware/sources/th_HS2``.
    """
    reg = geant4.Registry()
    tube = _tube(
        "source_plates",
        plates.width_in_mm / 2,
        plates.height_in_mm,
        reg,
        r_min=plates.cavity_width_in_mm / 2,
    )
    return geant4.LogicalVolume(tube, get_material("G4_Pb", reg), "Source_Plates", reg)


def create_source_holder(holder: AttrsDict, source_z: float) -> geant4.LogicalVolume:
    """Create the acrylic source holder.

    The shape follows the metadata in ``hardware/source_holders/``: a ring around
    the cryostat with a radial hole (lateral holder, has ``cavity_width_in_mm``),
    or a cap on the cryostat top (z = 0) with a round or rectangular (has
    ``top_plate_depth_in_mm``) pocket for the source.

    Parameters
    ----------
    holder
        The source holder dimensions.
    source_z
        The z position of the source from the cryostat top, in mm.
    """
    reg = geant4.Registry()
    h = holder
    r_out = h.outer_width_in_mm / 2
    r_in = h.inner_width_in_mm / 2

    if "cavity_width_in_mm" in h:
        solid = geant4.solid.Subtraction(
            "source_holder",
            _tube("cylinder_source_holder", r_out, h.height_in_mm, reg, r_min=r_in),
            _tube(
                "cavity_source_holder",
                h.cavity_width_in_mm / 2,
                h.cavity_height_in_mm,
                reg,
            ),
            [[np.pi / 2, 0, 0], [0, (r_in + r_out) / 2, 0]],
            reg,
        )
        return geant4.LogicalVolume(
            solid, get_material("acrylic_source_holder", reg), "Source_Holder", reg
        )

    # the pocket in the top plate extends down to the source position
    z_cryo = source_z + h.top_plate_height_in_mm / 2
    z_end = source_z + h.top_bottom_height_in_mm
    sides = [
        (h.top_height_in_mm, r_in, r_out),
        (z_cryo, r_in, r_out),
        (z_cryo, h.bottom_inner_width_in_mm / 2, r_out),
        (z_end, h.bottom_inner_width_in_mm / 2, r_out),
    ]

    if "top_plate_depth_in_mm" not in h:
        solid = _polycone(
            "source_holder",
            [
                (0, h.top_plate_width_in_mm / 2, r_out),
                (h.top_plate_height_in_mm, h.top_plate_width_in_mm / 2, r_out),
                (h.top_plate_height_in_mm, h.top_inner_width_in_mm / 2, r_out),
                (h.top_height_in_mm, h.top_inner_width_in_mm / 2, r_out),
                *sides,
            ],
            reg,
        )
    else:
        solid = geant4.solid.Subtraction(
            "source_holder_endcap",
            _polycone(
                "source_holder_cylinder",
                [(0, 0, r_out), (h.top_height_in_mm, 0, r_out), *sides],
                reg,
            ),
            geant4.solid.Box(
                "rectangular_plate",
                h.top_plate_width_in_mm,
                h.top_plate_depth_in_mm,
                h.top_plate_height_in_mm,
                reg,
            ),
            [[0, 0, 0], [0, 0, h.top_plate_height_in_mm / 2]],
            reg,
        )
        solid = geant4.solid.Subtraction(
            "source_holder_sub",
            solid,
            geant4.solid.Box(
                "source_holder_top_inner",
                h.top_inner_width_in_mm,
                h.top_inner_depth_in_mm,
                h.top_height_in_mm,
                reg,
            ),
            [[0, 0, 0], [0, 0, h.top_height_in_mm / 2 + h.top_plate_height_in_mm]],
            reg,
        )

    return geant4.LogicalVolume(
        solid, get_material("acrylic_source_holder", reg), "Source_Holder", reg
    )
