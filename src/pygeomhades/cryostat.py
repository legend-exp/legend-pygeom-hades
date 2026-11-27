"""Vacuum cryostat, detector holder and wrap (``hardware/cryostat`` in hades-metadata)."""

from __future__ import annotations

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .solids import polycone


def make_vacuum_cavity(
    cryostat: AttrsDict, registry: geant4.Registry
) -> geant4.LogicalVolume:
    """Construct the vacuum cavity of the cryostat.

    `cryostat` is the ``cryostat`` block of ``hardware/cryostat/<detector>``.
    The cavity starts at z = 0.
    """
    radius = cryostat.width_in_mm / 2 - cryostat.side_thickness_in_mm
    height = (
        cryostat.height_in_mm
        - cryostat.top_thickness_in_mm
        - cryostat.bottom_thickness_in_mm
    )
    vacuum_cavity = geant4.solid.GenericPolycone(
        "cryostat_vacuum",
        0.0,
        2.0 * np.pi,
        pR=[0.0, radius, radius, 0.0],
        pZ=[0.0, 0.0, height, height],
        lunit="mm",
        aunit="rad",
        registry=registry,
    )
    return geant4.LogicalVolume(
        vacuum_cavity, "G4_Galactic", "cryostat_vacuum", registry
    )


def make_cryostat(
    cryostat: AttrsDict, registry: geant4.Registry, materials: HadesMaterialRegistry
) -> geant4.LogicalVolume:
    """Create the cryostat, a closed cylinder with a vacuum cavity.

    `cryostat` is the ``cryostat`` block of ``hardware/cryostat/<detector>``.
    z = 0 is the cryostat top.
    """
    r_out = cryostat.width_in_mm / 2
    r_in = r_out - cryostat.side_thickness_in_mm
    start = cryostat.top_thickness_in_mm
    end = cryostat.height_in_mm - cryostat.bottom_thickness_in_mm

    solid = polycone(
        "cryostat_wall_aluminium",
        [
            (0, 0, r_out),
            (start, 0, r_out),
            (start, r_in, r_out),
            (end, r_in, r_out),
            (end, 0, r_out),
            (cryostat.height_in_mm, 0, r_out),
        ],
        registry,
    )
    return geant4.LogicalVolume(
        solid, materials.metal_aluminium_2011T8, "cryostat_wall_aluminium", registry
    )


def make_wrap(
    wrap: AttrsDict,
    crystal_radius: float,
    max_height: float,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
) -> geant4.LogicalVolume:
    """Create the detector wrap (HD1000 polyethylene), a cup closed at z = 0.

    `wrap` is the ``wrap.geometry`` block of ``hardware/cryostat/<detector>``.
    The inner radius is at least `crystal_radius` (mm), so the wrap does not
    enter the crystal. A cup taller than `max_height` (mm) is cut at its open
    end.
    """
    r_out = wrap.outer.radius_in_mm
    r_in = max(wrap.inner.radius_in_mm, crystal_radius)
    top = wrap.outer.height_in_mm - wrap.inner.height_in_mm
    height = min(wrap.outer.height_in_mm, max_height)

    solid = polycone(
        "hpge_wrap_hdpe",
        [(0, 0, r_out), (top, 0, r_out), (top, r_in, r_out), (height, r_in, r_out)],
        registry,
    )
    return geant4.LogicalVolume(solid, materials.hdpe, "hpge_wrap_hdpe", registry)


def make_holder(
    holder: AttrsDict,
    det_type: str,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
) -> geant4.LogicalVolume:
    """Create the detector holder.

    Parameters
    ----------
    holder
        The ``holder.geometry`` block of ``hardware/cryostat/<detector>``.
    det_type
        Detector type (``icpc`` or ``bege``). ICPC holders without ``rings`` (e.g.
        production order 6) are built without rings and lip.
    registry, materials
        The registries of the volumes and of their materials.
    """
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

        if "rings" not in holder:
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

    solid = polycone("hpge_holder_aluminium", planes, registry)
    return geant4.LogicalVolume(
        solid, materials.metal_aluminium_2011T8, "hpge_holder_aluminium", registry
    )
