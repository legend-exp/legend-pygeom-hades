from __future__ import annotations

from pathlib import Path

import pytest
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


@pytest.mark.parametrize("argv", [[], ["--print-volumes", "nonsense"]])
def test_bad_arguments(argv):
    with pytest.raises(SystemExit):
        _parse_cli_args(argv)
