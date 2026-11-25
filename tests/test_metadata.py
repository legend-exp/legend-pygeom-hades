from __future__ import annotations

from dbetto import AttrsDict

from pygeomhades.metadata import (
    PublicHadesMetadataProxy,
    PublicLegendMetadataProxy,
    merge_configs,
    parse_measurement,
)


def test_legend_metada_proxy():
    lmeta = PublicLegendMetadataProxy()
    assert isinstance(lmeta.hardware.detectors.germanium.diodes["V123456A"], AttrsDict)


def test_hades_metada_proxy():
    lmeta = PublicHadesMetadataProxy()
    assert isinstance(lmeta.hardware.cryostat["V123456A"], AttrsDict)


def test_merge_config():
    meta = PublicLegendMetadataProxy()

    hpge = merge_configs(
        meta.hardware.detectors.germanium.diodes["V07302A"], {"dimensions": 1}
    )

    assert hpge.hades.dimensions == 1
    assert hpge.production.enrichment.val is not None


def test_parse_measurement_basic():
    out = parse_measurement("cs_HS2_bottom_foo")

    assert out.source == "cs_HS2"
    assert out.position == "bottom"
    assert out.id == "foo"

    out = parse_measurement("am_HS1_top_dlt")

    assert out.source == "am_HS1"
    assert out.position == "top"
    assert out.id == "dlt"

    out = parse_measurement("am_HS6_top_dlt")

    assert out.source == "am_HS6"  # no renaming
