"""Lead castle and bottom plate (``hardware/setup`` in hades-metadata)."""

from __future__ import annotations

from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .solids import box, place


def make_bottom_plate(plate: AttrsDict) -> geant4.LogicalVolume:
    """Create the bottom plate, a box with a cavity centered on its edge at y = +depth/2.

    `plate` is ``hardware/setup/bottom_plate``.
    """
    reg = geant4.Registry()
    mats = HadesMaterialRegistry(reg)
    solid = geant4.solid.Subtraction(
        "final_bottom_plate",
        box("bottom_plate", plate, reg),
        box("cavity_bottom_plate", plate.cavity, reg),
        [[0, 0, 0], [0, plate.depth_in_mm / 2, 0]],
        reg,
    )
    return geant4.LogicalVolume(solid, mats.metal_aluminium, "Bottom_plate", reg)


def make_lead_castle(castle: AttrsDict) -> geant4.LogicalVolume:
    """Create a lead castle.

    `castle` is a design of ``hardware/setup/lead_castle``: the current castle
    (``legend``, with port and sliding door) or the castle of the GERDA era
    (``gerda``, with a copper plate between base and top block).
    """
    reg = geant4.Registry()
    mats = HadesMaterialRegistry(reg)

    if "front" in castle:
        # the cavity is the inner cavity plus a box shifted towards +y
        cavity = geant4.solid.Union(
            "total_cavity_1",
            box("inner_cavity_base_1", castle.inner_cavity, reg),
            box("cavity_base_1", castle.cavity, reg),
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
            box("base_lead_castle_1", castle.base, reg),
            cavity,
            [[0, 0, 0], [0, 0, 0]],
            reg,
        )
        # the top and front blocks overlap the base by 0.01 mm, so that
        # the union has no coincident surfaces
        solid = geant4.solid.Union(
            "top_base_1",
            solid,
            box("top_lead_castle_1", castle.top, reg),
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
            box("front_1", castle.front, reg),
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
        return geant4.LogicalVolume(solid, mats.metal_lead, "Lead_castle", reg)

    # GERDA-era castle: the top block is separated from the base by the copper plate
    cu_height = castle.copper_plate.height_in_mm
    solid = geant4.solid.Subtraction(
        "base_cavity_2",
        box("base_lead_castle_2", castle.base, reg),
        box("inner_cavity_lead_castle_2", castle.inner_cavity, reg),
        [[0, 0, 0], [0, 0, 0]],
        reg,
    )
    solid = geant4.solid.Union(
        "final_lead_castle_2",
        solid,
        box("top_lead_castle_2", castle.top, reg),
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
    castle_lv = geant4.LogicalVolume(solid, mats.metal_lead, "Lead_castle", reg)
    # FIXME: the copper plate lies in the gap between base and top, i.e.
    # outside of its mother volume
    plate_lv = geant4.LogicalVolume(
        box("copper_plate", castle.copper_plate, reg),
        mats.metal_copper,
        "Copper_plate",
        reg,
    )
    place(plate_lv, castle_lv, reg, z=-(castle.base.height_in_mm + cu_height) / 2)
    return castle_lv
