"""Helpers to build and place solids. Lengths are in mm, angles in rad."""

from __future__ import annotations

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

#: gap (mm) between volumes that touch in the real setup, so that they do not
#: share a surface (Geant4 cannot tell on which side of a shared surface a
#: point is). Much larger than the Geant4 surface tolerance (1e-9 mm), much
#: smaller than any physical effect.
SAFETY_GAP_IN_MM = 1e-3


def polycone(
    name: str, planes: list[tuple[float, float, float]], registry: geant4.Registry
) -> geant4.solid.Polycone:
    """Full-turn polycone from a list of ``(z, r_min, r_max)`` planes, in mm."""
    z, r_min, r_max = zip(*planes, strict=True)
    return geant4.solid.Polycone(
        name, 0, 2 * np.pi, list(z), list(r_min), list(r_max), registry
    )


def tube(
    name: str,
    r_max: float,
    height: float,
    registry: geant4.Registry,
    r_min: float = 0,
) -> geant4.solid.Tubs:
    """Full-turn tube, with dimensions in mm (`height` is the full length)."""
    return geant4.solid.Tubs(name, r_min, r_max, height, 0, 2 * np.pi, registry)


def box(name: str, dims: AttrsDict, registry: geant4.Registry) -> geant4.solid.Box:
    """Box from the ``width_in_mm``, ``depth_in_mm`` and ``height_in_mm`` fields."""
    return geant4.solid.Box(
        name, dims.width_in_mm, dims.depth_in_mm, dims.height_in_mm, registry
    )


def place(
    lv: geant4.LogicalVolume,
    mother: geant4.LogicalVolume,
    registry: geant4.Registry,
    *,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> geant4.PhysicalVolume:
    """Place `lv` in `mother` at (`x`, `y`, `z`) mm, rotated by `rotation` (rad).

    The physical volume has the name of `lv`.
    """
    return geant4.PhysicalVolume(
        [*rotation, "rad"],
        [x, y, z, "mm"],
        lv,
        lv.name,
        mother,
        registry=registry,
    )
