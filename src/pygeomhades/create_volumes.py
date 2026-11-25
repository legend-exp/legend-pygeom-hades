"""Construction of the HADES geometry components.

All dimensions are in mm and are read from the HADES metadata (``hardware/``
folder of hades-metadata). Each function returns a logical volume.
"""

from __future__ import annotations

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import get_material
from .utils import place


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


def create_wrap(wrap: AttrsDict) -> geant4.LogicalVolume:
    """Create the detector wrap (HD1000 polyethylene), a cup closed at z = 0.

    `wrap` is the ``wrap.geometry`` block of
    ``hardware/cryostat/<detector>``.

    .. warning::

        The returned logical volume belongs to its own registry,
        it is necessary to call :func:`reg.addVolumeRecursive` on
        the produced PhysicalVolume to get a sane registry.
    """
    reg = geant4.Registry()
    r_out = wrap.outer.radius_in_mm
    r_in = wrap.inner.radius_in_mm
    height = wrap.outer.height_in_mm
    top = height - wrap.inner.height_in_mm

    solid = _polycone(
        "wrap",
        [(0, 0, r_out), (top, 0, r_out), (top, r_in, r_out), (height, r_in, r_out)],
        reg,
    )
    return geant4.LogicalVolume(solid, get_material("hd1000", reg), "Wrap", reg)


def create_holder(holder: AttrsDict, det_type: str, order: int) -> geant4.LogicalVolume:
    """Create the detector holder.

    Parameters
    ----------
    holder
        The ``holder.geometry`` block of ``hardware/cryostat/<detector>``.
    det_type
        Detector type (``icpc`` or ``bege``).
    order
        The detector production batch.
    """
    reg = geant4.Registry()
    cyl = holder.cylinder
    r_in = cyl.inner.radius_in_mm
    r_out = cyl.outer.radius_in_mm
    h_in = cyl.inner.height_in_mm
    h_out = cyl.outer.height_in_mm

    if det_type == "icpc":
        # cylinder open at z = 0, with an annular bottom continued by a
        # smaller closed cylinder (the "bottom cylinder")
        bot = holder.bottom_cyl
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
            rings = holder.rings
            r_max = rings.radius_in_mm
            edge = holder.edge.height_in_mm
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
        rings = holder.rings
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

    solid = _polycone("holder", planes, reg)
    return geant4.LogicalVolume(solid, get_material("en_aw_2011t8", reg), "Holder", reg)


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


def create_lead_castle(table: int, castle: AttrsDict) -> geant4.LogicalVolume:
    """Create the lead solid of table 1 or 2.

    `castle` is ``hardware/setup/lead_castle/table<table>``.
    """
    reg = geant4.Registry()

    if table == 1:
        # the cavity is the inner cavity plus a box shifted towards +y
        cavity = geant4.solid.Union(
            "total_cavity_1",
            _box("inner_cavity_base_1", castle.inner_cavity, reg),
            _box("cavity_base_1", castle.cavity, reg),
            [
                [0, 0, 0],
                [
                    0,
                    castle.inner_cavity.depth_in_mm / 2
                    + (castle.base.depth_in_mm - castle.inner_cavity.depth_in_mm) / 4,
                    (castle.inner_cavity.height_in_mm - castle.cavity.height_in_mm) / 2,
                ],
            ],
            reg,
        )
        solid = geant4.solid.Subtraction(
            "base_cavity_1",
            _box("base_lead_castle_1", castle.base, reg),
            cavity,
            [[0, 0, 0], [0, 0, 0]],
            reg,
        )
        # the top and front blocks overlap the base by 0.01 mm, so that
        # the union has no coincident surfaces
        solid = geant4.solid.Union(
            "top_base_1",
            solid,
            _box("top_lead_castle_1", castle.top, reg),
            [
                [0, 0, 0],
                [
                    0,
                    0,
                    -(castle.base.height_in_mm + castle.top.height_in_mm) / 2 - 0.01,
                ],
            ],
            reg,
        )
        solid = geant4.solid.Union(
            "final_lead_castle_1",
            solid,
            _box("front_1", castle.front, reg),
            [
                [0, 0, 0],
                [
                    0,
                    (castle.base.depth_in_mm + castle.front.depth_in_mm) / 2 - 0.01,
                    (castle.base.height_in_mm - castle.front.height_in_mm) / 2,
                ],
            ],
            reg,
        )
        return geant4.LogicalVolume(
            solid, get_material("lead", reg), "Lead_castle", reg
        )

    # table 2: the top block is separated from the base by the copper plate
    cu_height = castle.copper_plate.height_in_mm
    solid = geant4.solid.Subtraction(
        "base_cavity_2",
        _box("base_lead_castle_2", castle.base, reg),
        _box("inner_cavity_lead_castle_2", castle.inner_cavity, reg),
        [[0, 0, 0], [0, 0, 0]],
        reg,
    )
    solid = geant4.solid.Union(
        "final_lead_castle_2",
        solid,
        _box("top_lead_castle_2", castle.top, reg),
        [
            [0, 0, 0],
            [
                0,
                0,
                -((castle.base.height_in_mm + castle.top.height_in_mm) / 2 + cu_height),
            ],
        ],
        reg,
    )
    castle_lv = geant4.LogicalVolume(
        solid, get_material("lead_table2", reg), "Lead_castle", reg
    )
    # FIXME: the copper plate lies in the gap between base and top, i.e.
    # outside of its mother volume
    plate_lv = geant4.LogicalVolume(
        _box("copper_plate", castle.copper_plate, reg),
        get_material("copper", reg),
        "Copper_plate",
        reg,
    )
    place(plate_lv, castle_lv, reg, z=-(castle.base.height_in_mm + cu_height) / 2)
    return castle_lv


def create_source(
    source_type: str, source: AttrsDict, position: str
) -> geant4.LogicalVolume:
    """Create the source with its capsule, collimator or holder.

    Parameters
    ----------
    source_type
        The source name, e.g. ``th_HS2``.
    source
        ``hardware/sources/<source_type>``.
    position
        The measurement position (``top`` or ``lat``).
    """
    reg = geant4.Registry()

    def lv(solid, material, name):
        return geant4.LogicalVolume(solid, get_material(material, reg), name, reg)

    def active(material):
        return lv(
            _tube("source", source.width_in_mm / 2, source.height_in_mm, reg),
            material,
            "Source",
        )

    if source_type == "am_HS1":
        # encapsulated source inside a collimator with a cylindrical beam
        # channel above it
        col = source.collimator
        cap_height = source.capsule.height_in_mm
        src = active("quartz")
        capsule = lv(
            _tube("source_capsule", source.capsule.width_in_mm / 2, cap_height, reg),
            "steel",
            "Source_Encapsulated",
        )
        place(
            src,
            capsule,
            reg,
            z=(cap_height - source.height_in_mm) / 2 - col.window_in_mm,
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
        outer = lv(_box("collimator", col, reg), "G4_Cu", "Source_Collimated")
        place(beam, outer, reg, z=(col.height_in_mm - col.beam_height_in_mm) / 2)
        place(
            capsule,
            outer,
            reg,
            z=-cap_height / 2 - col.beam_height_in_mm + col.height_in_mm / 2,
        )

    elif source_type == "am_HS6":
        src = active("acrylic")
        outer = lv(
            _box("source_capsule", source.capsule, reg),
            "acrylic",
            "Source_Encapsulated",
        )
        place(src, outer, reg)

    elif source_type in ["ba_HS4", "co_HS5"]:
        # source on a foil, surrounded by an aluminium ring
        ring = source.al_ring
        src = active("hd1000")
        foil = lv(
            _tube(
                "source_foil",
                source.foil.width_in_mm / 2,
                source.foil.height_in_mm,
                reg,
            ),
            "hd1000",
            "Source_foil",
        )
        place(src, foil, reg)
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
        outer = lv(
            _tube("source_vacuum", ring.width_max_in_mm / 2, ring.height_in_mm, reg),
            "vacuum",
            "Source_Encapsulated",
        )
        place(foil, outer, reg)
        place(al_ring, outer, reg)

    elif source_type == "th_HS2":
        # encapsulated source with epoxy, in the air cavity of a copper
        # holder. The copper holder is a cylinder with a wider bottom.
        cu = source.copper
        cu_all_height = cu.height_in_mm + cu.bottom_height_in_mm
        cap_height = source.capsule.height_in_mm
        src = active("quartz")
        epoxy = lv(
            _tube(
                "source_epoxy",
                source.epoxy.width_in_mm / 2,
                source.epoxy.height_in_mm,
                reg,
            ),
            "epoxy",
            "Source_Epoxy",
        )
        capsule = lv(
            _tube("source_capsule", source.capsule.width_in_mm / 2, cap_height, reg),
            "steel",
            "Source_Encapsulated",
        )
        place(src, capsule, reg)
        place(epoxy, capsule, reg, z=(cap_height - source.epoxy.height_in_mm) / 2)
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
        place(
            capsule,
            cavity,
            reg,
            z=cu_all_height - cap_height / 2 - source.offset_height_in_mm[position],
        )
        outer = lv(
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
        place(cavity, outer, reg)

    else:
        msg = f"source type {source_type} is not implemented"
        raise NotImplementedError(msg)

    return outer


def create_th_plates(plates: AttrsDict) -> geant4.LogicalVolume:
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


def create_source_holder(
    source_holder: AttrsDict, source_z: float
) -> geant4.LogicalVolume:
    """Create the acrylic source holder.

    The shape follows the metadata in ``hardware/source_holders/``: a ring around
    the cryostat with a radial hole (lateral holder, has ``cavity_width_in_mm``),
    or a cap on the cryostat top (z = 0) with a round or rectangular (has
    ``top_plate_depth_in_mm``) pocket for the source.

    Parameters
    ----------
    source_holder
        ``hardware/source_holders/<name>``.
    source_z
        The z position of the source from the cryostat top, in mm.
    """
    reg = geant4.Registry()
    r_out = source_holder.outer_width_in_mm / 2
    r_in = source_holder.inner_width_in_mm / 2

    if "cavity_width_in_mm" in source_holder:
        solid = geant4.solid.Subtraction(
            "source_holder",
            _tube(
                "cylinder_source_holder",
                r_out,
                source_holder.height_in_mm,
                reg,
                r_min=r_in,
            ),
            _tube(
                "cavity_source_holder",
                source_holder.cavity_width_in_mm / 2,
                source_holder.cavity_height_in_mm,
                reg,
            ),
            [[np.pi / 2, 0, 0], [0, (r_in + r_out) / 2, 0]],
            reg,
        )
        return geant4.LogicalVolume(
            solid, get_material("acrylic_source_holder", reg), "Source_Holder", reg
        )

    # the pocket in the top plate extends down to the source position
    z_cryo = source_z + source_holder.top_plate_height_in_mm / 2
    z_end = source_z + source_holder.top_bottom_height_in_mm
    sides = [
        (source_holder.top_height_in_mm, r_in, r_out),
        (z_cryo, r_in, r_out),
        (z_cryo, source_holder.bottom_inner_width_in_mm / 2, r_out),
        (z_end, source_holder.bottom_inner_width_in_mm / 2, r_out),
    ]

    if "top_plate_depth_in_mm" not in source_holder:
        solid = _polycone(
            "source_holder",
            [
                (0, source_holder.top_plate_width_in_mm / 2, r_out),
                (
                    source_holder.top_plate_height_in_mm,
                    source_holder.top_plate_width_in_mm / 2,
                    r_out,
                ),
                (
                    source_holder.top_plate_height_in_mm,
                    source_holder.top_inner_width_in_mm / 2,
                    r_out,
                ),
                (
                    source_holder.top_height_in_mm,
                    source_holder.top_inner_width_in_mm / 2,
                    r_out,
                ),
                *sides,
            ],
            reg,
        )
    else:
        solid = geant4.solid.Subtraction(
            "source_holder_endcap",
            _polycone(
                "source_holder_cylinder",
                [(0, 0, r_out), (source_holder.top_height_in_mm, 0, r_out), *sides],
                reg,
            ),
            geant4.solid.Box(
                "rectangular_plate",
                source_holder.top_plate_width_in_mm,
                source_holder.top_plate_depth_in_mm,
                source_holder.top_plate_height_in_mm,
                reg,
            ),
            [[0, 0, 0], [0, 0, source_holder.top_plate_height_in_mm / 2]],
            reg,
        )
        solid = geant4.solid.Subtraction(
            "source_holder_sub",
            solid,
            geant4.solid.Box(
                "source_holder_top_inner",
                source_holder.top_inner_width_in_mm,
                source_holder.top_inner_depth_in_mm,
                source_holder.top_height_in_mm,
                reg,
            ),
            [
                [0, 0, 0],
                [
                    0,
                    0,
                    source_holder.top_height_in_mm / 2
                    + source_holder.top_plate_height_in_mm,
                ],
            ],
            reg,
        )

    return geant4.LogicalVolume(
        solid, get_material("acrylic_source_holder", reg), "Source_Holder", reg
    )
