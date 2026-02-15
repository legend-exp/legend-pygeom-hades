from __future__ import annotations

from dbetto import AttrsDict

from pygeomhades.metadata import PublicHadesMetadataProxy, PublicLegendMetadataProxy


def test_legend_metada_proxy():
    lmeta = PublicLegendMetadataProxy()
    assert isinstance(lmeta.hardware.detectors.germanium.diodes["V123456A"], AttrsDict)


def test_hades_metada_proxy():
    lmeta = PublicHadesMetadataProxy()
    assert isinstance(lmeta.hardware.cryostat["V123456A"], AttrsDict)
