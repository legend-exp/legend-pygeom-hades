from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from dbetto import utils
from pyg4ometry import gdml, geant4
from pygeomtools import viewer

from pygeomhades import cli
from pygeomhades.cli import _parse_cli_args, dump_gdml_cli

CONFIG = str(Path(__file__).parent / "test.yaml")


def test_parse_cli_args():
    args = _parse_cli_args(["--config", CONFIG, "out.gdml"])
    assert args.config == CONFIG
    assert args.filename == "out.gdml"


# pygeomtools.geometry.print_volumes() uses a deprecated pandas call
@pytest.mark.filterwarnings("ignore:Passing a list to DataFrame.from_dict")
def test_dump_gdml(tmp_path, capsys):
    out = tmp_path / "hades.gdml"
    dump_gdml_cli(
        [
            *("--public-geom", "--verbose", "--print-volumes", "logical"),
            *("--config", CONFIG, str(out)),
        ]
    )

    assert "Source" in capsys.readouterr().out

    reg = gdml.Reader(str(out)).getRegistry()
    assert {"Source", "Cryostat", "Wrap", "Holder"} <= set(reg.logicalVolumeDict)


def test_options(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(viewer, "visualize", lambda reg, scene: calls.append(scene))
    # the real overlap check takes a long time, and the finer mesh would
    # persist for all following tests
    monkeypatch.setattr(
        geant4.LogicalVolume,
        "checkOverlaps",
        lambda self, recursive: calls.append("overlaps"),
    )
    monkeypatch.setattr(cli.meshconfig, "setGlobalMeshSliceAndStack", calls.append)

    scene_file = tmp_path / "scene.yaml"
    scene_file.write_text("window_size: [100, 100]\n")
    dump_gdml_cli(
        [
            *("--public-geom", "--check-overlaps", "--clip-geometry"),
            *("--visualize", str(scene_file), "--config", CONFIG),
        ]
    )

    scene = calls.pop()
    assert scene["window_size"] == [100, 100]
    assert "clipper" in scene
    assert calls == [100, "overlaps"]


@pytest.mark.parametrize(
    ("scene", "mesh_calls"), [(None, [100]), ("fine_mesh: false\n", [])]
)
def test_fine_mesh(tmp_path, monkeypatch, scene, mesh_calls):
    calls = []
    monkeypatch.setattr(viewer, "visualize", lambda reg, scene: None)
    monkeypatch.setattr(cli.meshconfig, "setGlobalMeshSliceAndStack", calls.append)

    vis_args = ["--visualize"]
    if scene is not None:
        scene_file = tmp_path / "scene.yaml"
        scene_file.write_text(scene)
        vis_args.append(str(scene_file))

    dump_gdml_cli(["--public-geom", "--config", CONFIG, *vis_args])
    assert calls == mesh_calls


@pytest.mark.parametrize(
    "argv",
    [
        [],
        ["--print-volumes", "nonsense"],
        ["--config", CONFIG],
        ["--config", CONFIG, "--detector", "V13049A", "out.gdml"],
        ["--config", CONFIG, "--campaign", "c1", "out.gdml"],
        ["--public-geom", "--detector", "V13049A", "out.gdml"],
    ],
)
def test_bad_arguments(argv):
    with pytest.raises(SystemExit):
        _parse_cli_args(argv)


@pytest.fixture
def meta_dir(tmp_path, monkeypatch):
    config = utils.load_dict(CONFIG)
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
def constructed(monkeypatch):
    configs = []
    monkeypatch.setattr(
        cli.core, "construct", lambda config, **_: configs.append(config)
    )
    monkeypatch.setattr(cli, "write_pygeom", lambda *_: None)
    return configs


def test_select_from_file(meta_dir, constructed):
    runs_file = str(meta_dir / "V13049A" / "c1" / "th_HS2_top_psa.yaml")
    dump_gdml_cli(["--config", runs_file, "--run", "run0002", "out.gdml"])
    assert constructed[-1].run == "run0002"

    with pytest.raises(ValueError, match="run run0003 not found"):
        dump_gdml_cli(["--config", runs_file, "--run", "run0003", "out.gdml"])

    with pytest.raises(ValueError, match=r"--run: run0001, run0002$"):
        dump_gdml_cli(["--config", runs_file, "out.gdml"])


def test_select_from_metadata(meta_dir, constructed):
    dump_gdml_cli(["--detector", "B00000B", "out.gdml"])
    config = constructed[-1]
    assert (config.detector, config.campaign, config.run) == (
        "B00000B",
        "c1",
        "run0001",
    )

    dump_gdml_cli(
        [
            *("--detector", "V13049A", "--campaign", "c1"),
            *("--measurement", "th_HS2_top_psa", "--run", "run0002", "out.gdml"),
        ]
    )
    config = constructed[-1]
    assert (config.campaign, config.measurement, config.run) == (
        "c1",
        "th_HS2_top_psa",
        "run0002",
    )


@pytest.mark.parametrize(
    ("argv", "error"),
    [
        (["--detector", "V0"], "detector V0 not found, available: B00000B, V13049A"),
        (["--detector", "V13049A"], "--campaign: c1, c2$"),
        (
            ["--detector", "V13049A", "--campaign", "c1"],
            "--measurement: am_HS1_top_dlt, th_HS2_top_psa$",
        ),
        (
            ["--detector", "V13049A", "--campaign", "c2"],
            r"--run: run0001, run0002, run0003, \.\.\., run0012 \(12 runs\)$",
        ),
    ],
)
def test_select_errors(meta_dir, constructed, argv, error):
    with pytest.raises(ValueError, match=error):
        dump_gdml_cli([*argv, "out.gdml"])
