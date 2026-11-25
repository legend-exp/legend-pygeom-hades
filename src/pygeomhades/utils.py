from __future__ import annotations

import copy
import logging
from collections.abc import Mapping

from dbetto import AttrsDict
from pyg4ometry import geant4

log = logging.getLogger(__name__)


def parse_measurement(measurement: str) -> AttrsDict:
    """Parse a measurement string into its components.

    The measurement string is expected to be in the format
    ``{source}_{HSX}_{position}_{ID}``, e.g. "am_HS1_top_dlt".

    For more details see
    [link](https://legend-exp.atlassian.net/wiki/spaces/LEGEND/pages/1826750480/Analysis+of+characterization+data+WIP).

    Parameters
    ----------
    measurement
        The measurement string, e.g., "am_HS1_top_dlt".

    Returns
    -------
    AttrsDict
        A dictionary with keys "source", "position", and "id" containing the
        parsed components of the measurement string.  For example, for
        "am_HS1_top_dlt", the returned dictionary would be ``{"source":
        "am_HS1", "position": "top", "id": "dlt"}``.
    """

    split = measurement.split("_")

    if len(split) != 4:
        msg = f"Measurement string '{measurement}' is not in the expected format '{{source_HSX}}_{{position}}_{{ID}}'."
        raise ValueError(msg)

    return AttrsDict(
        {"source": split[0] + "_" + split[1], "position": split[2], "id": split[3]}
    )


def merge_configs(diode_meta: AttrsDict, hades_meta: Mapping) -> AttrsDict:
    """Return a copy of `diode_meta` with `hades_meta` added as ``hades``.

    A missing enrichment is set to 0.9, since the detector construction needs one.
    """
    hpge = copy.deepcopy(diode_meta)
    if hpge.production.enrichment.val is None:
        hpge.production.enrichment.val = 0.9
    hpge.hades = hades_meta
    return hpge


def place(
    lv: geant4.LogicalVolume,
    mother: geant4.LogicalVolume,
    registry: geant4.Registry,
    *,
    name: str | None = None,
    x: float = 0,
    y: float = 0,
    z: float = 0,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> geant4.PhysicalVolume:
    """Place `lv` in `mother` at (`x`, `y`, `z`) mm, rotated by `rotation` (rad).

    The physical volume is called `name`, or ``<lv name>_PV`` if not given.
    """
    return geant4.PhysicalVolume(
        [*rotation, "rad"],
        [x, y, z, "mm"],
        lv,
        name if name is not None else f"{lv.name}_PV",
        mother,
        registry=registry,
    )


def get_profile(
    solid: geant4.solid.GenericPolycone | geant4.solid.Polycone, flip: bool = False
) -> dict[str, list[float]]:
    """Get the (r,z) pairs making up the profile of a solid. Only works for polycones.

    Parameters
    ----------
    solid
        The solid to get the profile of.
    flip
        Whether to flip the z. This is needed for the detector, which is placed
        with inverted axes in the cryostat.
    """
    sign = -1 if flip else 1

    if isinstance(solid, geant4.solid.GenericPolycone):
        return {
            "r": [*solid.pR, solid.pR[0]],
            "z": [sign * zt for zt in [*solid.pZ, solid.pZ[0]]],
        }
    if isinstance(solid, geant4.solid.Polycone):
        return {
            "z": [sign * zt for zt in [*solid.pZpl, *solid.pZpl[::-1], solid.pZpl[0]]],
            "r": [*solid.pRMin, *solid.pRMax[::-1], solid.pRMin[0]],
        }
    msg = f"Solid of type {type(solid)} is not supported for profile extraction."
    raise ValueError(msg)
