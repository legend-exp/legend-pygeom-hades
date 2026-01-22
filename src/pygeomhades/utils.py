from __future__ import annotations

import logging
import tempfile
from collections.abc import Mapping
from pathlib import Path

from dbetto import AttrsDict
from pyg4ometry import gdml, geant4
from pygeomtools import write_pygeom as write_gdml

log = logging.getLogger(__name__)


def merge_configs(diode_meta: AttrsDict, extra_meta: Mapping, *, extra_name: str = "hades") -> AttrsDict:
    """Merge the configs from `lmeta` to the extra information
    provided in `config`.

    This also adds the needed `enrichment` value if this is not present.

    Parameters
    ----------
    diode_meta
        The standard metadata for the diode.
    extra_meta
        Extra metadata to add.
    extra_name
        name of the subdictionary to add the extra metadata to.
    """
    # make sure there is an enrichment value
    if diode_meta["production"]["enrichment"]["val"] is None:
        diode_meta["production"]["enrichment"]["val"] = 0.9  # reasonable value

    diode_meta[extra_name] = extra_meta

    return diode_meta


def amend_gdml(
    dummy_gdml_path: Path,
    replacements: dict,
    write_file: bool = False,
    gdml_file_name: str | Path = "test.gdml",
) -> geant4.Registry:
    gdml_text = dummy_gdml_path.read_text()

    for key, val in replacements.items():
        gdml_text = gdml_text.replace(key, f"{val:.{1}f}")

    with tempfile.NamedTemporaryFile("w+", suffix=".gdml") as f:
        f.write(gdml_text)
        f.flush()
        reader = gdml.Reader(f.name)

        if write_file:
            write_gdml(reader.getRegistry(), gdml_file_name)

        return reader.getRegistry()
