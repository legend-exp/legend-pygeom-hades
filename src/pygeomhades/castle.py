"""Lead castle and bottom plate (``hardware/setup`` in hades-metadata)."""

from __future__ import annotations

from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .solids import box, place


def make_bottom_plate(
    plate: AttrsDict, registry: geant4.Registry, materials: HadesMaterialRegistry
) -> geant4.LogicalVolume:
    """Create the bottom plate, a box with a cavity centered on its edge at y = +depth/2.

    `plate` is ``hardware/setup/bottom_plate``. The cavity goes through the
    whole plate.
    """
    slot = geant4.solid.Box(
        "castle_bottom_plate_aluminium_slot",
        plate.cavity.width_in_mm,
        plate.cavity.depth_in_mm,
        2 * plate.height_in_mm,
        registry,
    )
    solid = geant4.solid.Subtraction(
        "castle_bottom_plate_aluminium",
        box("castle_bottom_plate_aluminium_box", plate, registry),
        slot,
        [[0, 0, 0], [0, plate.depth_in_mm / 2, 0]],
        registry,
    )
    return geant4.LogicalVolume(
        solid, materials.metal_aluminium, "castle_bottom_plate_aluminium", registry
    )


def make_lead_castle(
    castle: AttrsDict, registry: geant4.Registry, materials: HadesMaterialRegistry
) -> geant4.LogicalVolume:
    """Create a lead castle.

    `castle` is a design of ``hardware/setup/lead_castle``: the current castle
    (``legend``, with port and sliding door) or the castle of the GERDA era
    (``gerda``, with a copper plate between base and top block). The inner
    cavity goes through the whole height of the base, and the port through the
    whole front wall.
    """
    base = castle.base
    inner = castle.inner_cavity
    inner_cavity = geant4.solid.Box(
        "castle_lead_inner_cavity",
        inner.width_in_mm,
        inner.depth_in_mm,
        base.height_in_mm,
        registry,
    )

    if "front" in castle:
        # the cavity is the inner cavity plus the port in the front (+y) wall
        wall = (base.depth_in_mm - inner.depth_in_mm) / 2
        port = geant4.solid.Box(
            "castle_lead_port",
            castle.cavity.width_in_mm,
            wall,
            castle.cavity.height_in_mm,
            registry,
        )
        cavity = geant4.solid.Union(
            "castle_lead_cavity_with_port",
            inner_cavity,
            port,
            [
                [0, 0, 0],
                [
                    0,
                    (inner.depth_in_mm + wall) / 2,
                    (base.height_in_mm - castle.cavity.height_in_mm) / 2,
                ],
            ],
            registry,
        )
        solid = geant4.solid.Subtraction(
            "castle_lead_step1",
            box("castle_lead_base", base, registry),
            cavity,
            [[0, 0, 0], [0, 0, 0]],
            registry,
        )
        # the top and front blocks overlap the base by 0.01 mm, so that
        # the union has no coincident surfaces
        solid = geant4.solid.Union(
            "castle_lead_step2",
            solid,
            box("castle_lead_top", castle.top, registry),
            [
                [0, 0, 0],
                [
                    0,
                    0,
                    -(base.height_in_mm + castle.top.height_in_mm) / 2 - 0.01,
                ],
            ],
            registry,
        )
        solid = geant4.solid.Union(
            "castle_lead",
            solid,
            box("castle_lead_door", castle.front, registry),
            [
                [0, 0, 0],
                [
                    0,
                    (base.depth_in_mm + castle.front.depth_in_mm) / 2 - 0.01,
                    (base.height_in_mm - castle.front.height_in_mm) / 2,
                ],
            ],
            registry,
        )
        return geant4.LogicalVolume(
            solid, materials.metal_lead, "castle_lead", registry
        )

    # GERDA-era castle: the top block is separated from the base by the copper plate
    cu_height = castle.copper_plate.height_in_mm
    solid = geant4.solid.Subtraction(
        "castle_lead_step1",
        box("castle_lead_base", base, registry),
        inner_cavity,
        [[0, 0, 0], [0, 0, 0]],
        registry,
    )
    solid = geant4.solid.Union(
        "castle_lead",
        solid,
        box("castle_lead_top", castle.top, registry),
        [
            [0, 0, 0],
            [
                0,
                0,
                -((base.height_in_mm + castle.top.height_in_mm) / 2 + cu_height),
            ],
        ],
        registry,
    )
    castle_lv = geant4.LogicalVolume(
        solid, materials.metal_lead, "castle_lead", registry
    )
    # FIXME: the copper plate lies in the gap between base and top, i.e.
    # outside of its mother volume
    plate_lv = geant4.LogicalVolume(
        box("castle_plate_copper", castle.copper_plate, registry),
        materials.metal_copper,
        "castle_plate_copper",
        registry,
    )
    place(plate_lv, castle_lv, registry, z=-(base.height_in_mm + cu_height) / 2)
    return castle_lv
