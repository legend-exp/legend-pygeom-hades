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


def _geometry_configs() -> dict[str, tuple[AttrsDict, str | None]]:
    """Return the geometries checked with remage and their known-failure reason, by test ID."""
    configs: dict[str, tuple[AttrsDict, str | None]] = {
        f"dummy-{meas}": (AttrsDict(next(iter(runs.values()))), None)
        for meas, runs in TextDB(Path(__file__).parent / "dummy_prod" / "c1").items()
    }
    measurements = ("th_HS2_top_psa", "th_HS2_lat_psa")

    if public_geom:
        for det in PublicHadesMetadataProxy().hardware.cryostat.keys():  # noqa: SIM118
            for meas in measurements:
                configs[f"{det}-{meas}"] = (
                    AttrsDict(configs[f"dummy-{meas}"][0] | {"detector": det}),
                    None,
                )
        return configs

    # the first Th top and lateral run of every detector in hades-metadata
    hardware = Path(HadesMetadata(lazy=True).__path__) / "hardware"
    conf_dir = hardware / "configuration"
    for det in sorted(p.stem for p in (hardware / "cryostat").glob("*.yaml")):
        cryostat = utils.load_dict(str(hardware / "cryostat" / f"{det}.yaml"))
        for meas in measurements:
            files = sorted(conf_dir.glob(f"{det}/*/{meas}.yaml"))
            if not files:
                continue
            runs = utils.load_dict(str(files[0]))
            run = next(iter(runs))
            run_key = f"{det}-{files[0].parent.name}-{meas}-{run}"

            reason = None
            if cryostat["cryostat"]["width_in_mm"] == 114.3:
                reason = "source holder overlaps the 114.3 mm cryostat (legend-exp/hades-metadata#10)"
            elif "lat" in meas and runs[run]["source_position"]["r_in_mm"] != 0:
                reason = "lateral source with r_in_mm != 0 (legend-exp/legend-pygeom-hades#24)"

            configs[run_key] = (AttrsDict({"run_key": run_key}), reason)
    return configs


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    # the geometries are built by the gdml_file fixture, only for the tests
    # that are selected
    if "gdml_file" in metafunc.fixturenames:
        # the geantino check is random: it can miss a known overlap and pass
        strict = metafunc.function.__name__ != "test_surface_overlaps"
        params = [
            pytest.param(
                config,
                id=test_id,
                marks=pytest.mark.xfail(reason=reason, strict=strict) if reason else (),
            )
            for test_id, (config, reason) in _geometry_configs().items()
        ]
        metafunc.parametrize("gdml_file", params, indirect=True, scope="session")


def pytest_terminal_summary(terminalreporter) -> None:
    """Group the remage test results by problem and measurement.

    On GitHub Actions, also written to the job summary, and failures as
    error annotations.
    """
    groups: dict[tuple[str, str, str, str], set[str]] = {}
    for status in ("failed", "xfailed"):
        for rep in terminalreporter.stats.get(status, []):
            if "test_remage.py" not in rep.nodeid or rep.when != "call":
                continue
            test_id = rep.nodeid.partition("[")[2].removesuffix("]")
            parts = test_id.split("-")
            meas = next((p for p in parts if "_HS" in p), "?")
            crash = getattr(rep.longrepr, "reprcrash", None)
            if "XPASS(strict)" in str(rep.longrepr):
                keys = ["overlap gone, remove the xfail marker"]
            else:
                keys = dict(rep.user_properties).get("remage_findings") or [
                    crash.message.splitlines()[0][:120]
                    if crash
                    else "see the test failure"
                ]
            known = getattr(rep, "wasxfail", "")
            for key in keys:
                groups.setdefault((status, key, meas, known), set()).add(parts[0])

    if not groups:
        return

    terminalreporter.section("remage checks: problems by measurement")
    rows = []
    for (status, key, meas, known), det_set in sorted(groups.items()):
        dets = sorted(det_set)
        where = f"{meas} ({len(dets)}): {' '.join(dets)}"
        terminalreporter.write_line(f"{status.upper():8} {key}")
        terminalreporter.write_line(f"         {where}")
        if known:
            terminalreporter.write_line(f"         known: {known}")
        rows.append(
            f"| {status} | {key} | {known} | {meas} | {len(dets)} | {' '.join(dets)} |"
        )

        if status == "failed" and os.getenv("GITHUB_ACTIONS") == "true":
            # workflow command: error annotation shown on the run page
            terminalreporter.write_line(
                f"::error title=remage check failed::{key}%0A{where}"
            )

    if summary := os.getenv("GITHUB_STEP_SUMMARY"):
        with Path(summary).open("a") as f:
            f.write(
                "### remage checks: problems by measurement\n\n"
                "| Status | Problem | Known issue | Measurement | N | Detectors |\n"
                "|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n\n"
            )


@pytest.fixture(scope="session")
def gdml_file(request, tmp_path_factory):
    import pygeomtools

    reg = core.construct(request.param, public_geometry=public_geom)
    pygeomtools.geometry.check_registry_sanity(reg, reg)
    path = tmp_path_factory.mktemp("gdml") / "hades.gdml"
    pygeomtools.write_pygeom(reg, path)
    return path
