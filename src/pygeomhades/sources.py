"""Radioactive sources and source holders (``hardware/sources`` and
``hardware/source_holders`` in hades-metadata)."""

from __future__ import annotations

import logging
import math

import numpy as np
from dbetto import AttrsDict
from pyg4ometry import geant4

from .materials import HadesMaterialRegistry
from .solids import box, place, polycone, tube

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

    def lv(solid, material, name):
        return geant4.LogicalVolume(solid, material, name, registry)

    def active(material):
        return lv(
            tube("source", source.width_in_mm / 2, source.height_in_mm, registry),
            material,
            "Source",
        )

    if source_type == "am_HS1":
        # encapsulated source inside a collimator with a cylindrical beam
        # channel above it
        col = source.collimator
        cap_height = source.capsule.height_in_mm
        src = active(materials.silica)
        capsule = lv(
            tube(
                "source_capsule", source.capsule.width_in_mm / 2, cap_height, registry
            ),
            materials.metal_steel,
            "Source_Encapsulated",
        )
        place(
            src,
            capsule,
            registry,
            z=(cap_height - source.height_in_mm) / 2 - col.window_in_mm,
        )
        beam = lv(
            tube(
                "collimator_beam",
                col.beam_width_in_mm / 2,
                col.beam_height_in_mm,
                registry,
            ),
            materials.air,
            "Collimator_Beam",
        )
        outer = lv(
            box("collimator", col, registry),
            materials.metal_copper,
            "Source_Collimated",
        )
        place(beam, outer, registry, z=(col.height_in_mm - col.beam_height_in_mm) / 2)
        place(
            capsule,
            outer,
            registry,
            z=-cap_height / 2 - col.beam_height_in_mm + col.height_in_mm / 2,
        )

    elif source_type == "am_HS6":
        src = active(materials.pmma)
        outer = lv(
            box("source_capsule", source.capsule, registry),
            materials.pmma,
            "Source_Encapsulated",
        )
        place(src, outer, registry)

    elif source_type in ["ba_HS4", "co_HS5"]:
        # source on a foil, surrounded by an aluminium ring
        ring = source.al_ring
        src = active(materials.hdpe)
        foil = lv(
            tube(
                "source_foil",
                source.foil.width_in_mm / 2,
                source.foil.height_in_mm,
                registry,
            ),
            materials.hdpe,
            "Source_foil",
        )
        place(src, foil, registry)
        al_ring = lv(
            tube(
                "source_Alring",
                ring.width_max_in_mm / 2,
                ring.height_in_mm,
                registry,
                r_min=ring.width_min_in_mm / 2,
            ),
            materials.metal_aluminium,
            "Source_Alring",
        )
        outer = lv(
            tube(
                "source_vacuum", ring.width_max_in_mm / 2, ring.height_in_mm, registry
            ),
            materials.vacuum,
            "Source_Encapsulated",
        )
        place(foil, outer, registry)
        place(al_ring, outer, registry)

    elif source_type == "th_HS2":
        # encapsulated source with epoxy, in the air cavity of a copper
        # holder. The copper holder is a cylinder with a wider bottom.
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
            "Source_Epoxy",
        )
        capsule = lv(
            tube(
                "source_capsule", source.capsule.width_in_mm / 2, cap_height, registry
            ),
            materials.metal_steel,
            "Source_Encapsulated",
        )
        place(src, capsule, registry)
        place(epoxy, capsule, registry, z=(cap_height - source.epoxy.height_in_mm) / 2)
        cavity = lv(
            polycone(
                "CuSource_holder_cavity",
                [
                    (0, 0, cu.cavity_width_in_mm / 2),
                    (cu_all_height, 0, cu.cavity_width_in_mm / 2),
                ],
                registry,
            ),
            materials.air,
            "CuSource_Holder_Cavity",
        )
        place(
            capsule,
            cavity,
            registry,
            z=cu_all_height - cap_height / 2 - source.offset_height_in_mm[position],
        )
        outer = lv(
            polycone(
                "CuSource_holder",
                [
                    (0, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.width_in_mm / 2),
                    (cu.height_in_mm, 0, cu.bottom_width_in_mm / 2),
                    (cu_all_height, 0, cu.bottom_width_in_mm / 2),
                ],
                registry,
            ),
            materials.metal_copper,
            "CuSource_Holder",
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
        "source_plates",
        plates.width_in_mm / 2,
        plates.height_in_mm,
        registry,
        r_min=plates.cavity_width_in_mm / 2,
    )
    return geant4.LogicalVolume(solid, materials.metal_lead, "Source_Plates", registry)


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
    ``top_plate_depth_in_mm``) pocket for the source.

    Parameters
    ----------
    source_holder
        ``hardware/source_holders/<name>``.
    source_z
        The z position of the source from the cryostat top, in mm.
    registry, materials
        The registries of the volumes and of their materials.
    """
    r_out = source_holder.outer_width_in_mm / 2
    r_in = source_holder.inner_width_in_mm / 2

    if "cavity_width_in_mm" in source_holder:
        solid = geant4.solid.Subtraction(
            "source_holder",
            tube(
                "cylinder_source_holder",
                r_out,
                source_holder.height_in_mm,
                registry,
                r_min=r_in,
            ),
            tube(
                "cavity_source_holder",
                source_holder.cavity_width_in_mm / 2,
                source_holder.cavity_height_in_mm,
                registry,
            ),
            [[np.pi / 2, 0, 0], [0, (r_in + r_out) / 2, 0]],
            registry,
        )
        return geant4.LogicalVolume(solid, materials.pmma, "Source_Holder", registry)

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
        solid = polycone(
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
            registry,
        )
    else:
        solid = geant4.solid.Subtraction(
            "source_holder_endcap",
            polycone(
                "source_holder_cylinder",
                [(0, 0, r_out), (source_holder.top_height_in_mm, 0, r_out), *sides],
                registry,
            ),
            geant4.solid.Box(
                "rectangular_plate",
                source_holder.top_plate_width_in_mm,
                source_holder.top_plate_depth_in_mm,
                source_holder.top_plate_height_in_mm,
                registry,
            ),
            [[0, 0, 0], [0, 0, source_holder.top_plate_height_in_mm / 2]],
            registry,
        )
        solid = geant4.solid.Subtraction(
            "source_holder_sub",
            solid,
            geant4.solid.Box(
                "source_holder_top_inner",
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

    return geant4.LogicalVolume(solid, materials.pmma, "Source_Holder", registry)


def place_source(
    hardware: AttrsDict,
    source_type: str,
    position: str,
    source_position: AttrsDict,
    mother_lv: geant4.LogicalVolume,
    registry: geant4.Registry,
    materials: HadesMaterialRegistry,
) -> None:
    """Build the source of a run with its source holder and place them in `mother_lv`.

    `hardware` is the ``hardware`` folder of hades-metadata. The origin of
    `mother_lv` is at the cryostat top, with z pointing down.
    """
    if source_type not in ["am_HS1", "th_HS2"] and position == "lat":
        msg = f"lateral position not implemented for source type {source_type}"
        raise NotImplementedError(msg)

    source = hardware.sources[source_type]
    holder_name = source.get("source_holder", {}).get(position)
    source_holder = hardware.source_holders[holder_name] if holder_name else None

    source_lv = make_source(source_type, source, position, registry, materials)

    # source position in the detector frame
    x, y, z = source_xyz(source_position, source_type)
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
        source_z = holder_z - copper.height_in_mm - copper.bottom_height_in_mm
        th_plates_lv = make_th_plates(plates, registry, materials)
        place(
            th_plates_lv,
            mother_lv,
            registry,
            name="th_plate_pv",
            z=holder_z + plates.height_in_mm / 2,
        )

    place(
        source_lv,
        mother_lv,
        registry,
        name="source_pv",
        x=x,
        y=source_y,
        z=source_z,
        rotation=(-np.pi / 2, 0, 0) if lateral_th else (0, 0, 0),
    )

    if source_holder is not None:
        source_holder_lv = make_source_holder(source_holder, z, registry, materials)

        place(
            source_holder_lv, mother_lv, registry, name="source_holder_pv", z=holder_z
        )


def source_xyz(
    source_position: AttrsDict, source_type: str
) -> tuple[float, float, float]:
    """Convert the ``source_position`` (r, phi, z) of a run to x, y, z in mm.

    For ``am_HS1`` (scanning table), r is a motor position and the cryostat axis
    is assumed at r = 66 mm. This offset is not well known.
    """
    r = source_position.r_in_mm
    phi = source_position.phi_in_deg

    if source_type == "am_HS1" and r != 0:
        r += -66  # update this condition
        if r < 0:
            phi += 180
            r = abs(r)

        msg = (
            "Translation to detector from for am_HS1 and "
            "r!=0 is uncertain. Proceed with caution."
        )
        log.warning(msg)

    phi = phi * math.pi / 180.0
    x = r * math.cos(phi)
    y = -r * math.sin(phi)

    return x, y, source_position.z_in_mm
