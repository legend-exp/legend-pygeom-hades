from __future__ import annotations

import pytest

pytestmark = pytest.mark.needs_remage


def test_overlaps(gdml_file):
    from remage import remage_run

    macro = [
        "/RMG/Geometry/RegisterDetectorsFromGDML Germanium",
        "/run/initialize",
    ]

    remage_run(
        macro,
        gdml_files=str(gdml_file),
        raise_on_error=True,
        raise_on_warning=True,
    )
