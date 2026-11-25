from __future__ import annotations

import math
import re
from pathlib import Path

import dbetto
import pytest
from dbetto import AttrsDict
from pyg4ometry import geant4

from pygeomhades import create_volumes, materials
from pygeomhades.core import construct


def _num(x):
    """Evaluate pyg4ometry expressions to floats, recursively."""
    if hasattr(x, "eval"):
        x = x.eval()
    if isinstance(x, list | tuple):
        return [_num(v) for v in x]
    return float(x) if isinstance(x, int | float) else x


def _diff(a, b, path):
    """Differences between two nested lists of numbers."""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return [f"{path}: length {len(a)} != {len(b)}"]
        return [
            d
            for i, (x, y) in enumerate(zip(a, b, strict=True))
            for d in _diff(x, y, f"{path}[{i}]")
        ]
    if isinstance(a, float) and isinstance(b, float):
        if math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9):
            return []
        return [f"{path}: {a} != {b}"]
    return [] if a == b else [f"{path}: {a!r} != {b!r}"]


def compare_solids(a, b, path):
    if type(a) is not type(b):
        return [f"{path}: solid type {type(a).__name__} != {type(b).__name__}"]
    diffs = []
    for unit in ("lunit", "aunit"):
        diffs += _diff(getattr(a, unit, None), getattr(b, unit, None), f"{path}.{unit}")
    for var in a.varNames:
        if var in ("obj1", "obj2"):
            diffs += compare_solids(getattr(a, var), getattr(b, var), f"{path}.{var}")
        else:
            diffs += _diff(
                _num(getattr(a, var)), _num(getattr(b, var)), f"{path}.{var}"
            )
    return diffs


def _composition(mat):
    """Element (Z, A), amount and kind of amount of each component, ordered by Z.

    Elements made of isotopes have no single A and are identified by name.
    """
    return sorted(
        ((el.Z, el.name if el.A is None else el.A), float(n), kind)
        for el, n, kind in mat.components
    )


def compare_materials(a, b, path):
    # pyg4ometry appends _0, _1, ... to duplicated names when merging registries
    name_a, name_b = (re.sub(r"_\d+$", "", m.name) for m in (a, b))
    if name_a.startswith("G4_") or name_b.startswith("G4_"):
        return [] if name_a == name_b else [f"{path}: material {name_a} != {name_b}"]

    diffs = _diff(float(a.density), float(b.density), f"{path}.density")
    comp_a, comp_b = _composition(a), _composition(b)
    same = len(comp_a) == len(comp_b) and all(
        za == zb
        and ka == kb
        # atomic masses differ by up to 0.004 g/mol between the GDML templates
        and (aa == ab or math.isclose(aa, ab, rel_tol=1e-4))
        and math.isclose(na, nb)
        for ((za, aa), na, ka), ((zb, ab), nb, kb) in zip(comp_a, comp_b, strict=True)
    )
    if not same:
        diffs.append(f"{path}: composition {comp_a} != {comp_b}")
    return diffs


def compare_volumes(pv_a, pv_b, path=""):
    """Differences between two physical volumes and their daughters."""
    path = f"{path}/{pv_a.name}"
    diffs = _diff(pv_a.name, pv_b.name, f"{path}.name")
    diffs += _diff(_num(pv_a.position), _num(pv_b.position), f"{path}.position")
    diffs += _diff(_num(pv_a.rotation), _num(pv_b.rotation), f"{path}.rotation")
    diffs += _diff(pv_a.copyNumber, pv_b.copyNumber, f"{path}.copyNumber")
    diffs += _diff(
        getattr(pv_a, "pygeom_active_detector", None),
        getattr(pv_b, "pygeom_active_detector", None),
        f"{path}.pygeom_active_detector",
    )

    lv_a, lv_b = pv_a.logicalVolume, pv_b.logicalVolume
    diffs += _diff(lv_a.name, lv_b.name, f"{path}.lv")
    diffs += compare_materials(lv_a.material, lv_b.material, f"{path}.material")
    diffs += compare_solids(lv_a.solid, lv_b.solid, f"{path}.solid")
    diffs += _diff(
        _num(getattr(lv_a, "pygeom_color_rgba", None)),
        _num(getattr(lv_b, "pygeom_color_rgba", None)),
        f"{path}.pygeom_color_rgba",
    )
    return diffs + _compare_daughters(lv_a, lv_b, path)


def _compare_daughters(lv_a, lv_b, path):
    names_a = [d.name for d in lv_a.daughterVolumes]
    names_b = [d.name for d in lv_b.daughterVolumes]
    if names_a != names_b:
        return [f"{path}: daughters {names_a} != {names_b}"]
    return [
        d
        for da, db in zip(lv_a.daughterVolumes, lv_b.daughterVolumes, strict=True)
        for d in compare_volumes(da, db, path)
    ]


def compare_registries(reg_a, reg_b):
    """Differences between two geometries, by walking their volume trees."""
    wa, wb = reg_a.getWorldVolume(), reg_b.getWorldVolume()
    diffs = compare_materials(wa.material, wb.material, "/world.material")
    diffs += compare_solids(wa.solid, wb.solid, "/world.solid")
    return diffs + _compare_daughters(wa, wb, "")


class _Exact(float):
    """A float that is formatted with all its digits, whatever the format spec."""

    def __format__(self, spec):
        return repr(float(self))


@pytest.fixture
def exact_gdml(monkeypatch):
    """Fill the GDML templates with exact values instead of rounding to 0.1 mm."""
    read = create_volumes.read_gdml_with_replacements
    monkeypatch.setattr(
        create_volumes,
        "read_gdml_with_replacements",
        lambda path, repl: read(path, {k: _Exact(v) for k, v in repl.items()}),
    )


def _configs():
    configs = [
        pytest.param(next(iter(runinfo.values())), id=meas)
        for meas, runinfo in dbetto.TextDB(
            Path(__file__).parent / "dummy_prod" / "c1"
        ).items()
    ]
    for det in ("B99000A", "V99000A"):
        for table in ("efb1", "efb2"):
            config = {
                "detector": det,
                "campaign": "c1",
                "measurement": "am_HS6_top_dlt",
                "daq_settings": {"flashcam": {"card_interface": table}},
            }
            configs.append(pytest.param(AttrsDict(config), id=f"{det}-{table}"))
    return configs


@pytest.mark.usefixtures("exact_gdml")
@pytest.mark.parametrize("config", _configs())
def test_same_as_gdml(config):
    reg_gdml = construct(config, public_geometry=True, from_gdml=True)
    reg_python = construct(config, public_geometry=True, from_gdml=False)
    assert compare_registries(reg_gdml, reg_python) == []


def test_holders():
    holder = AttrsDict(
        {
            "cylinder": {
                "inner": {"height_in_mm": 100, "radius_in_mm": 40},
                "outer": {"height_in_mm": 104, "radius_in_mm": 42},
            },
            "bottom_cyl": {
                "inner": {"height_in_mm": 5, "radius_in_mm": 10},
                "outer": {"height_in_mm": 8, "radius_in_mm": 12},
            },
            "rings": {
                "position_top_ring_in_mm": 20,
                "position_bottom_ring_in_mm": 60,
                "radius_in_mm": 50,
                "height_in_mm": 10,
            },
            "edge": {"height_in_mm": 3},
        }
    )
    for det_type, order in [("bege", 0), ("icpc", 0), ("icpc", 6)]:
        a = create_volumes.create_holder(holder, det_type, order, from_gdml=True)
        b = create_volumes.create_holder(holder, det_type, order, from_gdml=False)
        assert compare_solids(a.solid, b.solid, det_type) == []
        assert compare_materials(a.material, b.material, det_type) == []

    with pytest.raises(NotImplementedError):
        create_volumes.create_holder(holder, "coax", 0, from_gdml=False)


def test_compare_finds_differences():
    reg = geant4.Registry()
    box = geant4.solid.Box("a", 1, 2, 3, reg)
    assert compare_solids(box, geant4.solid.Box("b", 1, 2, 3.5, reg), "x") != []
    assert compare_solids(box, geant4.solid.Tubs("t", 0, 1, 3, 0, 1, reg), "x") != []

    lead = materials.get_material("lead", reg)
    assert compare_materials(lead, materials.get_material("lead_table2", reg), "x")


@pytest.mark.parametrize("key", list(materials._MATERIALS))
def test_materials(key):
    reg = geant4.Registry()
    mat = materials.get_material(key, reg)
    assert isinstance(mat, geant4.Material)
    assert materials.get_material(key, reg) is mat
