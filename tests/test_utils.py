from __future__ import annotations

from pygeomhades.metadata import PublicMetadataProxy
from pygeomhades.utils import merge_configs


def test_merge_config():
    meta = PublicMetadataProxy()

    hpge_meta = merge_configs(meta.hardware.detectors.germanium.diodes["V07302A"], {"dimensions": 1})

    assert hpge_meta.hades.dimensions == 1
    assert hpge_meta.production.enrichment.val is not None
