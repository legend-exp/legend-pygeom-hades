from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from dbetto import utils
from legendmeta import HadesMetadata, LegendMetadata

from pygeomhades import cli, core
from pygeomhades.metadata import PublicHadesMetadataProxy, PublicLegendMetadataProxy

public_geom = os.getenv("LEGEND_METADATA", "") == ""


@pytest.fixture
def meta_dir(tmp_path, monkeypatch):
    config = utils.load_dict(str(Path(__file__).parent / "test.yaml"))
    conf_dir = tmp_path / "hardware" / "configuration"
    for meas_path, n_runs in [
        ("V13049A/c1/th_HS2_top_psa", 2),
        ("V13049A/c1/am_HS1_top_dlt", 1),
        ("V13049A/c2/th_HS2_top_psa", 12),
        ("B00000B/c1/th_HS2_top_psa", 1),
    ]:
        det, campaign, meas = meas_path.split("/")
        runs = {
            f"run{i:04d}": {
                **config,
                "detector": det,
                "campaign": campaign,
                "measurement": meas,
                "run": f"run{i:04d}",
            }
            for i in range(1, n_runs + 1)
        }
        path = conf_dir / f"{meas_path}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        utils.write_dict(runs, str(path))

    monkeypatch.setattr(
        cli, "HadesMetadata", lambda lazy: SimpleNamespace(__path__=tmp_path)
    )
    return conf_dir


@pytest.fixture
def private_meta(meta_dir, monkeypatch):
    """Let ``core.construct`` read the runs of `meta_dir` and the public hardware data."""
    hmeta = SimpleNamespace(
        hardware=PublicHadesMetadataProxy().hardware, __path__=meta_dir.parents[1]
    )
    monkeypatch.setattr(core, "HadesMetadata", lambda lazy: hmeta)
    monkeypatch.setattr(
        core, "LegendMetadata", lambda lazy: PublicLegendMetadataProxy()
    )


@pytest.fixture(scope="session")
def metadatas():
    if public_geom:
        return PublicLegendMetadataProxy(), PublicHadesMetadataProxy()
    return LegendMetadata(), HadesMetadata()


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "gdml_file" not in metafunc.fixturenames:
        return

    # collection-time imports
    import dbetto
    import pygeomtools
    from dbetto import AttrsDict
    from pyg4ometry import geant4

    from pygeomhades import core
    from pygeomhades.core import construct
    from pygeomhades.metadata import PublicHadesMetadataProxy, PublicLegendMetadataProxy

    # use pytest's base temp dir for the session
    outdir = metafunc.config._tmp_path_factory.mktemp("gdml")

    if public_geom:
        _, hmeta = PublicLegendMetadataProxy(), PublicHadesMetadataProxy()
    else:
        _, hmeta = LegendMetadata(), HadesMetadata()

    files: list[Path] = []

    test_daq_meta = dbetto.TextDB(f"{Path(__file__).parent}/dummy_prod/c1")
    for meas, runinfo in test_daq_meta.items():
        config = next(iter(runinfo.values()))
        reg = core.construct(config, public_geometry=public_geom)
        gdml_file = outdir / f"{meas}_{config.detector}.gdml"
        pygeomtools.geometry.check_registry_sanity(reg, reg)
        pygeomtools.write_pygeom(reg, gdml_file)
        files.append(gdml_file)

    for det in hmeta.hardware.cryostat.keys():  # noqa: SIM118
        reg = construct(
            AttrsDict(
                {
                    "detector": det,
                    "campaign": "c1",
                    "measurement": "am_HS1_top_dlt",
                    "daq_settings": {"flashcam": {"card_interface": "efb3"}},
                }
            ),
            public_geometry=public_geom,
        )
        assert isinstance(reg, geant4.Registry)
        gdml_file = outdir / f"am_HS1_top_dlt_{det}.gdml"
        pygeomtools.write_pygeom(reg, gdml_file)
        files.append(gdml_file)

    metafunc.parametrize("gdml_file", files, ids=lambda p: Path(p).name)
