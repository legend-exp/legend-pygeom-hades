from __future__ import annotations

import copy
from collections.abc import Mapping
from importlib import resources

from dbetto import AttrsDict, TextDB


class PublicLegendMetadataProxy:
    def __init__(self):
        dummy = TextDB(resources.files("pygeomhades") / "configs/dummy/diodes")
        self.hardware = AttrsDict(
            {"detectors": {"germanium": {"diodes": _DummyProxy(dummy, diode=True)}}}
        )


class PublicHadesMetadataProxy:
    def __init__(self):
        dummy = TextDB(resources.files("pygeomhades") / "configs/dummy")
        self.hardware = AttrsDict(
            {
                "cryostat": _DummyProxy(dummy.cryostat),
                "setup": dummy.setup,
                "sources": dummy.sources,
                "source_holders": dummy.source_holders,
            }
        )


class _DummyProxy:
    """Map any detector name to the dummy entry of its type (``V99000A``, ...).

    For diodes, the production order is also taken from the detector name.
    """

    def __init__(self, dummies: TextDB, diode: bool = False):
        self.dummies = dummies
        self.diode = diode

    def __getitem__(self, det_name: str) -> AttrsDict:
        m = copy.deepcopy(self.dummies[det_name[0] + "99000A"])
        m.name = det_name
        if self.diode:
            m.production.order = int(det_name[1:3])
            m.production.slice = "A"
        return m

    def keys(self):
        return self.dummies.keys()


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
