from __future__ import annotations

import copy
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
