from __future__ import annotations

import copy
import logging
from collections.abc import Iterable, Mapping
from importlib import resources
from pathlib import Path

from dbetto import AttrsDict, TextDB, utils

log = logging.getLogger(__name__)


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


def measurement_table(setup: AttrsDict, run: AttrsDict) -> str:
    """Return the measurement table (``table1``, ``table2`` or ``scanning``) of a run.

    The table is given by the FlashCam card of the run, except for the runs listed
    in ``hardware/setup/table_exceptions``.
    """
    card = run.daq_settings.flashcam.card_interface
    tables = {"efb1": "table1", "efb2": "table2", "efb3": "scanning"}
    if card not in tables:
        msg = f"unknown card interface {card!r}, expected one of {list(tables)}"
        raise ValueError(msg)
    return setup.table_exceptions.get(run.detector, {}).get(
        run.measurement, tables[card]
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


def select_run(
    path: str | Path,
    detector: str | None = None,
    campaign: str | None = None,
    measurement: str | None = None,
    run: str | None = None,
) -> AttrsDict:
    """Return the configuration of a run in hades-metadata.

    The runs are stored in
    ``hardware/configuration/<detector>/<campaign>/<measurement>.yaml``, keyed by
    run name. A key left as ``None`` is taken if it has only one choice.
    Otherwise, a :class:`ValueError` lists the choices.

    Parameters
    ----------
    path
        path to the hades-metadata repository.
    """
    path = Path(path) / "hardware" / "configuration"
    for level, value in (("detector", detector), ("campaign", campaign)):
        dirs = [p.name for p in path.iterdir() if p.is_dir()]
        path /= _choose(dirs, level, value)

    files = {p.stem: p for p in path.iterdir() if p.suffix in (".yaml", ".json")}
    runs = AttrsDict(
        utils.load_dict(str(files[_choose(files, "measurement", measurement)]))
    )
    return runs[_choose(runs, "run", run)]


def _choose(options: Iterable[str], level: str, value: str | None) -> str:
    """Return the selected option, or the only one if none is selected."""
    options = sorted(options)
    if value is not None and value in options:
        return value
    if value is None and len(options) == 1:
        log.info("selected %s %s", level, options[0])
        return options[0]

    listed = ", ".join(options)
    if len(options) > 10:
        listed = (
            f"{', '.join(options[:3])}, ..., {options[-1]} ({len(options)} {level}s)"
        )
    if value is None:
        msg = f"select a {level} with --{level}: {listed}"
    else:
        msg = f"{level} {value} not found, available: {listed}"
    raise ValueError(msg)
