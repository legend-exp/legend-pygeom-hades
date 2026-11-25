"""Vacuum cryostat, detector holder and wrap (``hardware/cryostat`` in hades-metadata)."""

from __future__ import annotations

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import get_material
from .solids import polycone


def make_vacuum_cavity(
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


def make_cryostat(cryostat: AttrsDict) -> geant4.LogicalVolume:
    """Create the cryostat, a closed cylinder with a vacuum cavity.

    `cryostat` is the ``cryostat`` block of ``hardware/cryostat/<detector>``.
    z = 0 is the cryostat top.
    """
    reg = geant4.Registry()
    r_out = cryostat.width_in_mm / 2
    r_in = r_out - cryostat.thickness_in_mm
    start = cryostat.position_cavity_from_top_in_mm
    end = cryostat.height_in_mm - cryostat.position_cavity_from_bottom_in_mm

    solid = polycone(
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


def make_wrap(wrap: AttrsDict) -> geant4.LogicalVolume:
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

    solid = polycone(
        "wrap",
        [(0, 0, r_out), (top, 0, r_out), (top, r_in, r_out), (height, r_in, r_out)],
        reg,
    )
    return geant4.LogicalVolume(solid, get_material("hd1000", reg), "Wrap", reg)


def make_holder(holder: AttrsDict, det_type: str, order: int) -> geant4.LogicalVolume:
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

    solid = polycone("holder", planes, reg)
    return geant4.LogicalVolume(solid, get_material("en_aw_2011t8", reg), "Holder", reg)
