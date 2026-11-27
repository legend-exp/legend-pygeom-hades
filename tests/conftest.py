from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest
from dbetto import AttrsDict, TextDB, utils
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


def _geometry_configs() -> dict[str, AttrsDict]:
    """Return the configurations of the geometries checked with remage, by test ID."""
    configs = {
        f"dummy-{meas}": AttrsDict(next(iter(runs.values())))
        for meas, runs in TextDB(Path(__file__).parent / "dummy_prod" / "c1").items()
    }
    measurements = ("th_HS2_top_psa", "th_HS2_lat_psa")

    if public_geom:
        for det in PublicHadesMetadataProxy().hardware.cryostat.keys():  # noqa: SIM118
            for meas in measurements:
                configs[f"{det}-{meas}"] = AttrsDict(
                    configs[f"dummy-{meas}"] | {"detector": det}
                )
        return configs

    # the first Th top and lateral run of every detector in hades-metadata
    hardware = Path(HadesMetadata(lazy=True).__path__) / "hardware"
    conf_dir = hardware / "configuration"
    for det in sorted(p.stem for p in (hardware / "cryostat").glob("*.yaml")):
        for meas in measurements:
            files = sorted(conf_dir.glob(f"{det}/*/{meas}.yaml"))
            if files:
                run = next(iter(utils.load_dict(str(files[0]))))
                run_key = f"{det}-{files[0].parent.name}-{meas}-{run}"
                configs[run_key] = AttrsDict({"run_key": run_key})
    return configs


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    # the geometries are built by the gdml_file fixture, only for the tests
    # that are selected
    if "gdml_file" in metafunc.fixturenames:
        configs = _geometry_configs()
        metafunc.parametrize(
            "gdml_file",
            list(configs.values()),
            ids=list(configs),
            indirect=True,
            scope="session",
        )


@pytest.fixture(scope="session")
def gdml_file(request, tmp_path_factory):
    import pygeomtools

    reg = core.construct(request.param, public_geometry=public_geom)
    pygeomtools.geometry.check_registry_sanity(reg, reg)
    path = tmp_path_factory.mktemp("gdml") / "hades.gdml"
    pygeomtools.write_pygeom(reg, path)
    return path
