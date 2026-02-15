from __future__ import annotations

import copy
from importlib import resources

from dbetto import AttrsDict, TextDB


class PublicLegendMetadataProxy:
    def __init__(self):
        dummy = TextDB(resources.files("pygeomhades") / "configs/dummy/diodes")
        self.hardware = AttrsDict(
            {"detectors": {"germanium": {"diodes": _DiodeProxy(dummy)}}}
        )


class _DiodeProxy:
    def __init__(self, dummy_detectors: TextDB):
        self.dummy_detectors = dummy_detectors

    def __getitem__(self, det_name: str) -> AttrsDict:
        det = self.dummy_detectors[det_name[0] + "99000A"]
        m = copy.copy(det)
        m.name = det_name
        m.production.order = int(det_name[1:3])
        m.production.slice = "A"
        return m

    def keys(self):
        return self.dummy_detector.keys()


class PublicHadesMetadataProxy:
    def __init__(self):
        dummy = TextDB(resources.files("pygeomhades") / "configs/dummy/cryostat")
        self.hardware = AttrsDict({"cryostat": _CryostatProxy(dummy)})


class _CryostatProxy:
    def __init__(self, dummy_cryostats: TextDB):
        self.dummy_cryostats = dummy_cryostats

    def __getitem__(self, det_name: str) -> AttrsDict:
        det = self.dummy_cryostats[det_name[0] + "99000A"]
        m = copy.copy(det)
        m.name = det_name
        return m

    def keys(self):
        return self.dummy_cryostats.keys()
