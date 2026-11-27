"""Radioactive sources and source holders (``hardware/sources`` and
``hardware/source_holders`` in hades-metadata)."""

from __future__ import annotations

import logging
import math

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .metadata import measurement_table
from .solids import SAFETY_GAP_IN_MM, box, place, polycone, tube

log = logging.getLogger(__name__)


def make_source(
    source_type: str,
    source: AttrsDict,
    position: str,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
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
    registry, materials
        The registries of the volumes and of their materials.
    """

    def lv(solid, material):
        return geant4.LogicalVolume(solid, material, solid.name, registry)

    def active(material):
        return lv(
            tube(
                "source_active", source.width_in_mm / 2, source.height_in_mm, registry
            ),
            material,
        )

    # g separates surfaces that touch in reality (see SAFETY_GAP_IN_MM)
    g = SAFETY_GAP_IN_MM

    if source_type == "am_HS1":
        # encapsulated source inside a collimator with a cylindrical beam
        # channel above it. The channel ends a safety gap below the collimator
        # top.
        col = source.collimator
        cap_height = source.capsule.height_in_mm
        src = active(materials.silica)
        capsule = lv(
            tube(
                "source_capsule_steel",
                source.capsule.width_in_mm / 2,
                cap_height,
                registry,
            ),
            materials.metal_steel,
        )
        place(
            src,
            capsule,
            registry,
            z=(cap_height - source.height_in_mm) / 2 - col.window_in_mm,
        )
        beam = lv(
            tube(
                "source_collimator_channel_air",
                col.beam_width_in_mm / 2,
                col.beam_height_in_mm - g,
                registry,
            ),
            materials.air,
        )
        outer = lv(
            box("source_collimator_copper", col, registry),
            materials.metal_copper,
        )
        place(
            beam,
            outer,
            registry,
            z=(col.height_in_mm - col.beam_height_in_mm - g) / 2,
        )
        place(
            capsule,
            outer,
            registry,
            z=-cap_height / 2 - col.beam_height_in_mm + col.height_in_mm / 2 - g,
        )

    elif source_type == "am_HS6":
        src = active(materials.pmma)
        outer = lv(
            box("source_capsule_pmma", source.capsule, registry),
            materials.pmma,
        )
        place(src, outer, registry)

    elif source_type in ["ba_HS4", "co_HS5"]:
        # source on a foil, surrounded by an aluminium ring. The ring and the
        # envelope are a safety gap wider than the foil and the ring.
        ring = source.al_ring
        src = active(materials.hdpe)
        foil = lv(
            tube(
                "source_foil_hdpe",
                source.foil.width_in_mm / 2,
                source.foil.height_in_mm,
                registry,
            ),
            materials.hdpe,
        )
        place(src, foil, registry)
        al_ring = lv(
            tube(
                "source_ring_aluminium",
                ring.width_max_in_mm / 2,
                ring.height_in_mm,
                registry,
                r_min=ring.width_min_in_mm / 2 + g,
            ),
            materials.metal_aluminium,
        )
        outer = lv(
            tube(
                "source_envelope_vacuum",
                ring.width_max_in_mm / 2 + g,
                ring.height_in_mm + 2 * g,
                registry,
            ),
            materials.vacuum,
        )
        place(foil, outer, registry)
        place(al_ring, outer, registry)

    elif source_type == "th_HS2":
        # encapsulated source with epoxy, in the air cavity of a copper
        # holder. The copper holder is a cylinder with a wider bottom. The
        # cavity is closed by a safety gap of copper at both ends.
        cu = source.copper
        cu_all_height = cu.height_in_mm + cu.bottom_height_in_mm
        cap_height = source.capsule.height_in_mm
        src = active(materials.silica)
        epoxy = lv(
            tube(
                "source_epoxy",
                source.epoxy.width_in_mm / 2,
                source.epoxy.height_in_mm,
                registry,
            ),
            materials.th_source_epoxy,
        )
        capsule = lv(
            tube(
                "source_capsule_steel",
                source.capsule.width_in_mm / 2,
                cap_height,
                registry,
            ),
            materials.metal_steel,
        )
        place(src, capsule, registry)
        place(
            epoxy,
            capsule,
            registry,
            z=(cap_height - source.epoxy.height_in_mm) / 2 - g,
        )
        cavity = lv(
            polycone(
                "source_holder_bore_air",
                [
                    (g, 0, cu.cavity_width_in_mm / 2),
                    (cu_all_height - g, 0, cu.cavity_width_in_mm / 2),
                ],
                registry,
            ),
            materials.air,
        )
        place(
            capsule,
            cavity,
            registry,
            z=cu_all_height
            - cap_height / 2
            - source.offset_height_in_mm[position]
            - 2 * g,
        )
        outer = lv(
            polycone(
                "source_holder_copper",
                [
                    (0, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.bottom_width_in_mm / 2),
                    (cu_all_height, 0, cu.bottom_width_in_mm / 2),
                ],
                registry,
            ),
            materials.metal_copper,
        )
        place(cavity, outer, registry)

    else:
        msg = f"source type {source_type} is not implemented"
        raise NotImplementedError(msg)

    return outer


def make_th_plates(
    plates: AttrsDict, registry: geant4.Registry, materials: HadesMaterialRegistry
) -> geant4.LogicalVolume:
    """Create the Pb plates (an annulus) of the Th source.

    `plates` is the ``plates`` block of ``hardware/sources/th_HS2``.
    """
    solid = tube(
        "source_holder_plate_lead",
        plates.width_in_mm / 2,
        plates.height_in_mm,
        registry,
        r_min=plates.cavity_width_in_mm / 2,
    )
    return geant4.LogicalVolume(solid, materials.metal_lead, solid.name, registry)


def make_source_holder(
    source_holder: AttrsDict,
    source_z: float,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
) -> geant4.LogicalVolume:
    """Create the acrylic source holder.

    The shape follows the metadata in ``hardware/source_holders/``: a ring around
    the cryostat with a radial hole (lateral holder, has ``cavity_width_in_mm``),
    or a cap on the cryostat top (z = 0) with a round or rectangular (has
    ``top_plate_depth_in_mm``) pocket for the source. The holder, its pocket
    and its ring are larger by safety gaps than the volumes they hold or
    surround (see :data:`.solids.SAFETY_GAP_IN_MM`).

    Parameters
    ----------
    source_holder
        ``hardware/source_holders/<name>``.
    source_z
        The z position of the source from the cryostat top, in mm.
    registry, materials
        The registries of the volumes and of their materials.
    """
    g = SAFETY_GAP_IN_MM
    r_out = source_holder.outer_width_in_mm / 2
    r_in = source_holder.inner_width_in_mm / 2

    if "cavity_width_in_mm" in source_holder:
        # the hole, centred in the ring wall, goes from the ring axis through
        # the whole wall
        solid = geant4.solid.Subtraction(
            "source_holder_pmma",
            tube(
                "source_holder_pmma_ring",
                r_out,
                source_holder.height_in_mm,
                registry,
                r_min=r_in + g,
            ),
            tube(
                "source_holder_pmma_hole",
                source_holder.cavity_width_in_mm / 2 + g,
                r_in + r_out,
                registry,
            ),
            [[np.pi / 2, 0, 0], [0, (r_in + r_out) / 2, 0]],
            registry,
        )
        return geant4.LogicalVolume(solid, materials.pmma, solid.name, registry)

    # the pocket in the top plate extends down to the source position
    z_cryo = source_z + source_holder.top_plate_height_in_mm / 2
    z_end = z_cryo + source_holder.bottom_height_in_mm
    sides = [
        (source_holder.top_height_in_mm, r_in, r_out),
        (z_cryo - g, r_in, r_out),
        (z_cryo - g, source_holder.bottom_inner_width_in_mm / 2, r_out),
        (z_end, source_holder.bottom_inner_width_in_mm / 2, r_out),
    ]
    pocket_height = source_holder.top_plate_height_in_mm + 2 * g

    if "top_plate_depth_in_mm" not in source_holder:
        solid = polycone(
            "source_holder_pmma",
            [
                (0, source_holder.top_plate_width_in_mm / 2 + 2 * g, r_out),
                (
                    pocket_height,
                    source_holder.top_plate_width_in_mm / 2 + 2 * g,
                    r_out,
                ),
                (
                    pocket_height,
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
            registry,
        )
    else:
        solid = geant4.solid.Subtraction(
            "source_holder_pmma_step1",
            polycone(
                "source_holder_pmma_cylinder",
                [(0, 0, r_out), (source_holder.top_height_in_mm, 0, r_out), *sides],
                registry,
            ),
            # the box extends above the holder, so that the subtraction does
            # not leave a coincident surface
            geant4.solid.Box(
                "source_holder_pmma_plate_pocket",
                source_holder.top_plate_width_in_mm + 4 * g,
                source_holder.top_plate_depth_in_mm + 4 * g,
                2 * pocket_height,
                registry,
            ),
            [[0, 0, 0], [0, 0, 0]],
            registry,
        )
        solid = geant4.solid.Subtraction(
            "source_holder_pmma",
            solid,
            geant4.solid.Box(
                "source_holder_pmma_top_pocket",
                source_holder.top_inner_width_in_mm,
                source_holder.top_inner_depth_in_mm,
                source_holder.top_height_in_mm,
                registry,
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
            registry,
        )

    return geant4.LogicalVolume(solid, materials.pmma, solid.name, registry)


def place_source(
    hardware: AttrsDict,
    source_type: str,
    position: str,
    source_position: AttrsDict,
    mother_lv: geant4.LogicalVolume,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
    axis_in_mm: float = 0.0,
) -> None:
    """Build the source of a run with its source holder and place them in `mother_lv`.

    `hardware` is the ``hardware`` folder of hades-metadata. The origin of
    `mother_lv` is at the cryostat top, with z pointing down. `axis_in_mm` is the
    value of r on the cryostat axis (see :func:`source_xyz`).
    """
    if source_type not in ["am_HS1", "th_HS2"] and position == "lat":
        msg = f"lateral position not implemented for source type {source_type}"
        raise NotImplementedError(msg)

    source = hardware.sources[source_type]
    holder_name = source.get("source_holder", {}).get(position)
    source_holder = hardware.source_holders[holder_name] if holder_name else None

    source_lv = make_source(source_type, source, position, registry, materials)

    # source position in the detector frame
    x, y, z = source_xyz(source_position, axis_in_mm)
    source_y = y
    lateral_th = source_type == "th_HS2" and position == "lat"

    if source_type == "am_HS1":
        source_z = -(z + source.collimator.height_in_mm / 2)
    elif lateral_th:
        source_y = (
            source_holder.outer_width_in_mm / 2 + source.copper.bottom_height_in_mm
        )
        source_z = z
        holder_z = z
    else:
        holder_z = -(z + source_holder.top_plate_height_in_mm / 2)
        source_z = -z

    if source_type == "th_HS2" and position == "top":
        copper = source.copper
        plates = source.plates
        source_z = (
            holder_z
            - copper.height_in_mm
            - copper.bottom_height_in_mm
            - SAFETY_GAP_IN_MM
        )
        th_plates_lv = make_th_plates(plates, registry, materials)
        place(
            th_plates_lv,
            mother_lv,
            registry,
            z=holder_z + plates.height_in_mm / 2,
        )

    place(
        source_lv,
        mother_lv,
        registry,
        x=x,
        y=source_y,
        z=source_z,
        rotation=(-np.pi / 2, 0, 0) if lateral_th else (0, 0, 0),
    )

    if source_holder is not None:
        source_holder_lv = make_source_holder(source_holder, z, registry, materials)

        place(source_holder_lv, mother_lv, registry, z=holder_z)


def scanning_axis_in_mm(
    hardware: AttrsDict, detector: str, campaign: str | None
) -> float:
    """Return the arm position r (in mm) of the cryostat axis on the scanning table.

    The ``am_HS1_top_dlt`` runs of the detector campaign on the scanning table
    are assumed to include one with the source above the detector centre: the
    middle one of three arm positions, or else the one closest to 66 mm. Without
    such runs, the axis is assumed at 66 mm.
    """
    nominal = 66.0
    try:
        runs = hardware.configuration[detector][campaign].am_HS1_top_dlt
    except (AttributeError, KeyError, TypeError, FileNotFoundError):
        runs = {}

    positions = sorted(
        {
            run.source_position.r_in_mm
            for run in runs.values()
            if measurement_table(hardware.setup, run) == "scanning"
        }
    )

    if len(positions) == 3:
        return positions[1]

    if not positions:
        axis = nominal
        msg = (
            f"no am_HS1_top_dlt runs of {detector} (campaign {campaign}) on the "
            f"scanning table, assuming the cryostat axis at r = {axis} mm"
        )
    else:
        axis = min(positions, key=lambda r: abs(r - nominal))
        msg = (
            f"am_HS1_top_dlt runs of {detector} (campaign {campaign}) at "
            f"{len(positions)} arm positions instead of 3, assuming the cryostat "
            f"axis at the one closest to {nominal} mm: r = {axis} mm"
        )
    log.warning(msg)
    return axis


def source_xyz(
    source_position: AttrsDict, axis_in_mm: float = 0.0
) -> tuple[float, float, float]:
    """Convert the ``source_position`` (r, phi, z) of a run to x, y, z in mm.

    `axis_in_mm` is the value of r on the cryostat axis. A negative r measured
    from the axis puts the source on the opposite side (phi + 180 deg).
    """
    r = source_position.r_in_mm - axis_in_mm
    phi = math.radians(source_position.phi_in_deg)

    if r < 0:
        r = -r
        phi += math.pi

    return r * math.cos(phi), -r * math.sin(phi), source_position.z_in_mm
