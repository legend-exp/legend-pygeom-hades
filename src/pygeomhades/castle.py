"""Lead castle and bottom plate (``hardware/setup`` in hades-metadata)."""

from __future__ import annotations

from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .solids import SAFETY_GAP_IN_MM, box, place


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


def place_lead_castle(
    castle: AttrsDict,
    z: float,
    mother_lv: geant4.LogicalVolume,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
) -> None:
    """Build a lead castle and place it in `mother_lv`, with the base centred at `z` (mm).

    `castle` is a design of ``hardware/setup/lead_castle``: the current castle
    (``legend``, with port and sliding door) or the castle of the GERDA era
    (``gerda``, with a copper plate between base and top block). The inner
    cavity goes through the whole height of the base, and the port through the
    whole front wall. z points down.
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
        lv = geant4.LogicalVolume(solid, materials.metal_lead, "castle_lead", registry)
        place(lv, mother_lv, registry, z=z)
        return

    # GERDA-era castle: the copper plate lies between base and top block, the
    # three parts are separated by a gap so that they do not share a surface
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
                -(
                    (base.height_in_mm + castle.top.height_in_mm) / 2
                    + cu_height
                    + 2 * SAFETY_GAP_IN_MM
                ),
            ],
        ],
        registry,
    )
    castle_lv = geant4.LogicalVolume(
        solid, materials.metal_lead, "castle_lead", registry
    )
    place(castle_lv, mother_lv, registry, z=z)

    plate_lv = geant4.LogicalVolume(
        box("castle_plate_copper", castle.copper_plate, registry),
        materials.metal_copper,
        "castle_plate_copper",
        registry,
    )
    plate_z = z - (base.height_in_mm + cu_height) / 2 - SAFETY_GAP_IN_MM
    place(plate_lv, mother_lv, registry, z=plate_z)
