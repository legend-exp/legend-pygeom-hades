from __future__ import annotations

import contextlib
import logging
from datetime import UTC, datetime

import numpy as np
import pygeomtools
from dbetto import AttrsDict
from git import GitCommandError
from legendmeta import HadesMetadata, LegendMetadata
from pyg4ometry import geant4
from pygeomhpges import make_hpge

from . import colors, plot
from .castle import make_bottom_plate, make_lead_castle
from .cryostat import make_cryostat, make_holder, make_vacuum_cavity, make_wrap
from .metadata import (
    PublicHadesMetadataProxy,
    PublicLegendMetadataProxy,
    merge_configs,
    parse_measurement,
)
from .plot import get_profile
from .solids import place
from .sources import place_source

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

      The card interface gives the measurement table (``efb1``: static table 1,
      ``efb2``: static table 2, ``efb3``: scanning table, without lead castle),
      except for the runs listed in ``hardware/setup/table_exceptions``. The
      lead castle of the table is taken at ``run_start_time`` (format
      ``YYMMDDTHHMMSS``), or for the current setup if it is missing.
      Without ``source_position``, no source is built.
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
    top_wall = cryostat.top_thickness_in_mm

    reg = geant4.Registry()

    # Create the world volume
    world = geant4.solid.Box("world", 20, 20, 20, reg, "m")
    world_lv = geant4.LogicalVolume(world, "G4_Galactic", "world_lv", reg)
    reg.setWorld(world_lv)

    # place a box rotated 180 deg so the geometry is not upside down
    lab = geant4.solid.Box("lab", 18, 18, 18, reg, "m")
    lab_lv = geant4.LogicalVolume(lab, "G4_AIR", "lab_lv", reg)

    place(lab_lv, world_lv, reg, name="lab", rotation=(0, np.pi, 0))

    cavity_lv = make_vacuum_cavity(cryostat, reg)

    # save the info for plotting
    profiles["cavity"] = get_profile(cavity_lv.solid) | {"offset": top_wall}

    place(cavity_lv, lab_lv, reg, name="cavity_pv", z=top_wall)

    # construct the wrap
    wrap_lv = make_wrap(hpge.hades.wrap.geometry)

    z = hpge.hades.wrap.position_in_mm - top_wall
    pv = place(wrap_lv, cavity_lv, reg, name="wrap_pv", z=z)

    profiles["wrap"] = get_profile(wrap_lv.solid) | {"offset": z + top_wall}
    reg.addVolumeRecursive(pv)

    # construct the holder
    holder_lv = make_holder(hpge.hades.holder.geometry, hpge.type)

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
    cryostat_lv = make_cryostat(cryostat)

    pv = place(cryostat_lv, lab_lv, reg, name="cryo_pv")
    profiles["cryo"] = get_profile(cryostat_lv.solid) | {"offset": 0}

    reg.addVolumeRecursive(pv)

    if source_position is not None:
        place_source(
            hmeta.hardware, source_type, position, source_position, lab_lv, reg
        )

    # the measurement table is given by the FlashCam card, except for the runs
    # listed in hardware/setup/table_exceptions
    setup = hmeta.hardware.setup
    card = config.daq_settings.flashcam.card_interface
    tables = {"efb1": "table1", "efb2": "table2", "efb3": "scanning"}
    if card not in tables:
        msg = f"unknown card interface {card!r}, expected one of {list(tables)}"
        raise ValueError(msg)
    table = setup.table_exceptions.get(hpge_name, {}).get(
        config.measurement, tables[card]
    )

    # the static tables have a lead castle standing on the bottom plate
    if table != "scanning":
        # depth of the top of the bottom plate, on which the castle stands, below
        # the cryostat top. Not measured: assumed for all detectors and tables
        plate_depth_in_mm = 250.0

        plate = setup.bottom_plate
        plate_lv = make_bottom_plate(plate)

        z = plate_depth_in_mm + plate.height_in_mm / 2
        pv = place(plate_lv, lab_lv, reg, name="plate_pv", z=z)
        reg.addVolumeRecursive(pv)

        # the castle of each table depends on the date of the run (validity in
        # hardware/setup/table_castles); without a date, the current setup
        castles = setup.table_castles.on(
            f"20{config.run_start_time}Z"
            if "run_start_time" in config
            else datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        )
        castle = setup.lead_castle[castles[table]]
        castle_lv = make_lead_castle(castle)

        z = plate_depth_in_mm - castle.base.height_in_mm / 2
        pv = place(castle_lv, lab_lv, reg, name="castle_pv", z=z)
        reg.addVolumeRecursive(pv)

    colors.set_colors(reg)

    if plot_profiles:
        plot.plot_profiles(profiles, title=hpge_name, show=True)

    return reg
