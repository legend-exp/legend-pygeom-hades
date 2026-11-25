from __future__ import annotations

import contextlib
import logging
import math

import numpy as np
import pygeomtools
from dbetto import AttrsDict
from git import GitCommandError
from legendmeta import HadesMetadata, LegendMetadata
from pyg4ometry import geant4
from pygeomhpges import make_hpge

from . import colors, plot
from . import create_volumes as create
from .metadata import PublicHadesMetadataProxy, PublicLegendMetadataProxy
from .utils import get_profile, merge_configs, parse_measurement, place

log = logging.getLogger(__name__)


def construct(
    config: AttrsDict,
    public_geometry: bool = False,
    plot_profiles: bool = False,
) -> geant4.Registry:
    """Construct the HADES geometry.

    Returns the registry containing the world volume. The dimensions of all
    components are read from the HADES metadata (``hardware/`` folder).

    Parameters
    ----------
    config
      configuration dictionary defining the geometry, e.g.,

      .. code-block:: yaml

          detector: V13049A
          measurement: th_HS2_top_psa
          daq_settings:
            flashcam:
              card_interface: efb1
          source_position:
            phi_in_deg: 0.0
            r_in_mm: 0.0
            z_in_mm: 38.0

      The card interface selects the measurement table and its lead castle
      (``efb1``: table 1, ``efb2``: table 2). It is not needed for ``am_HS1``
      (scanning table, no castle). Without ``source_position``, no source is
      built.
    public_geometry
      if true, uses the public geometry metadata instead of the LEGEND-internal
      legend-metadata.
    plot_profiles
        if true, plots the profiles of the volumes in the geometry using matplotlib.
    """

    profiles = {}
    hpge_name = config.detector
    source_position = config.get("source_position")

    lmeta = None
    hmeta = None
    if not public_geometry:
        with contextlib.suppress(GitCommandError):
            lmeta = LegendMetadata(lazy=True)
            hmeta = HadesMetadata(lazy=True)

    # require user action to construct a testdata-only geometry (i.e. to avoid
    # accidental creation of "wrong" geometries by LEGEND members).
    if lmeta is None and not public_geometry:
        msg = "cannot construct geometry from public testdata only, if not explicitly instructed"
        raise RuntimeError(msg)

    if lmeta is None:
        log.warning("CONSTRUCTING GEOMETRY FROM PUBLIC DATA ONLY")
        lmeta = PublicLegendMetadataProxy()
        hmeta = PublicHadesMetadataProxy()

    measurement = parse_measurement(config.measurement)
    position = measurement.position
    source_type = measurement.source

    hpge = merge_configs(
        lmeta.hardware.detectors.germanium.diodes[hpge_name],
        hmeta.hardware.cryostat[hpge_name],
    )
    cryostat = hpge.hades.cryostat
    # the vacuum cavity starts below the top wall of the cryostat
    top_wall = cryostat.position_cavity_from_top_in_mm

    reg = geant4.Registry()

    # Create the world volume
    world = geant4.solid.Box("world", 20, 20, 20, reg, "m")
    world_lv = geant4.LogicalVolume(world, "G4_Galactic", "world_lv", reg)
    reg.setWorld(world_lv)

    # place a box rotated 180 deg so the geometry is not upside down
    lab = geant4.solid.Box("lab", 18, 18, 18, reg, "m")
    lab_lv = geant4.LogicalVolume(lab, "G4_AIR", "lab_lv", reg)

    place(lab_lv, world_lv, reg, name="lab", rotation=(0, np.pi, 0))

    cavity_lv = create.create_vacuum_cavity(cryostat, reg)

    # save the info for plotting
    profiles["cavity"] = get_profile(cavity_lv.solid) | {"offset": top_wall}

    place(cavity_lv, lab_lv, reg, name="cavity_pv", z=top_wall)

    # construct the wrap
    wrap_lv = create.create_wrap(hpge.hades.wrap.geometry)

    z = hpge.hades.wrap.position_in_mm - top_wall
    pv = place(wrap_lv, cavity_lv, reg, name="wrap_pv", z=z)

    profiles["wrap"] = get_profile(wrap_lv.solid) | {"offset": z + top_wall}
    reg.addVolumeRecursive(pv)

    # construct the holder
    holder_lv = create.create_holder(
        hpge.hades.holder.geometry, hpge.type, hpge.production.order
    )

    z = hpge.hades.holder.position_in_mm - top_wall
    pv = place(holder_lv, cavity_lv, reg, name="holder_pv", z=z)
    reg.addVolumeRecursive(pv)

    profiles["holder"] = get_profile(holder_lv.solid) | {"offset": z + top_wall}

    # construct the hpge, for now do not allow cylindrical asymmetry
    detector_lv = make_hpge(
        hpge, name=hpge.name, registry=reg, allow_cylindrical_asymmetry=False
    )

    # an extra offset is needed to account for the different reference point
    # this is the top of the crystal for the holder and wrap, but it's the p+
    # contact for the detector
    extra_offset = max(detector_lv.get_profile()[1])
    z = hpge.hades.detector.position_in_mm - top_wall + extra_offset

    # we need to flip the detector axes when placing it in the cryostat
    pv = place(detector_lv, cavity_lv, reg, name=hpge.name, z=z, rotation=(0, np.pi, 0))

    profiles["detector"] = get_profile(detector_lv.solid, flip=True) | {
        "offset": z + top_wall
    }

    # register the detector info for remage
    pv.set_pygeom_active_detector(
        pygeomtools.RemageDetectorInfo(
            "germanium",
            1,  # detector id in remage.
            hpge,
        )
    )
    # construct the cryostat
    cryostat_lv = create.create_cryostat(cryostat)

    pv = place(cryostat_lv, lab_lv, reg, name="cryo_pv")
    profiles["cryo"] = get_profile(cryostat_lv.solid) | {"offset": 0}

    reg.addVolumeRecursive(pv)

    if source_position is not None:
        if source_type not in ["am_HS1", "th_HS2"] and position == "lat":
            msg = f"lateral position not implemented for source type {source_type}"
            raise NotImplementedError(msg)

        source = hmeta.hardware.sources[source_type]
        holder_name = source.get("source_holder", {}).get(position)
        source_holder = (
            hmeta.hardware.source_holders[holder_name] if holder_name else None
        )

        source_lv = create.create_source(source_type, source, position)

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
            th_plates_lv = create.create_th_plates(plates)
            pv = place(
                th_plates_lv,
                lab_lv,
                reg,
                name="th_plate_pv",
                z=holder_z + plates.height_in_mm / 2,
            )
            reg.addVolumeRecursive(pv)

        pv = place(
            source_lv,
            lab_lv,
            reg,
            name="source_pv",
            x=x,
            y=source_y,
            z=source_z,
            rotation=(-np.pi / 2, 0, 0) if lateral_th else (0, 0, 0),
        )
        reg.addVolumeRecursive(pv)

        if source_holder is not None:
            source_holder_lv = create.create_source_holder(source_holder, source_z=z)

            pv = place(
                source_holder_lv, lab_lv, reg, name="source_holder_pv", z=holder_z
            )
            reg.addVolumeRecursive(pv)

    # construct lead castle and bottom plate

    if source_type != "am_HS1":  # for am_HS1 the castle and plate are not present
        setup = hmeta.hardware.setup

        # depth of the top of the bottom plate, on which the castle stands, below
        # the cryostat top. Not measured: assumed for all detectors and tables
        plate_depth_in_mm = 250.0

        plate = setup.bottom_plate
        plate_lv = create.create_bottom_plate(plate)

        z = plate_depth_in_mm + plate.height_in_mm / 2
        pv = place(plate_lv, lab_lv, reg, name="plate_pv", z=z)
        reg.addVolumeRecursive(pv)

        card = config.daq_settings.flashcam.card_interface
        table = {"efb1": 1, "efb2": 2}.get(card)
        if table is None:
            msg = (
                f"card interface {card!r} is not one of the static tables (efb1, efb2)"
            )
            raise ValueError(msg)

        castle = setup.lead_castle[f"table{table}"]
        castle_lv = create.create_lead_castle(table, castle)

        z = plate_depth_in_mm - castle.base.height_in_mm / 2
        pv = place(castle_lv, lab_lv, reg, name="castle_pv", z=z)
        reg.addVolumeRecursive(pv)

    colors.set_colors(reg)

    if plot_profiles:
        plot.plot_profiles(profiles, title=hpge_name, show=True)

    return reg


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
    x = round(r * math.cos(phi), 2)
    y = round(-r * math.sin(phi), 2)

    return x, y, source_position.z_in_mm
