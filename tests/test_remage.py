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


def test_surface_overlaps(gdml_file):
    from remage import remage_run

    # geantinos start on the surface of a 1 m box in the lab air, around the
    # lead castle and the bottom plate. remage logs an error if a geantino
    # enters a volume that is not a daughter of the current one.
    macro = [
        "/RMG/Geometry/GDMLDisableOverlapCheck",
        "/RMG/Output/ActivateOutputScheme GeometryCheck",
        "/run/initialize",
        "/RMG/Generator/Confine Volume",
        "/RMG/Generator/Confinement/SampleOnSurface",
        "/RMG/Generator/Confinement/FirstSamplingVolume Geometrical",
        "/RMG/Generator/Confinement/Geometrical/AddSolid Box",
        "/RMG/Generator/Confinement/Geometrical/CenterPositionX 0 m",
        "/RMG/Generator/Confinement/Geometrical/CenterPositionY 0 m",
        "/RMG/Generator/Confinement/Geometrical/CenterPositionZ 0 m",
        "/RMG/Generator/Confinement/Geometrical/Box/XLength 1 m",
        "/RMG/Generator/Confinement/Geometrical/Box/YLength 1 m",
        "/RMG/Generator/Confinement/Geometrical/Box/ZLength 1 m",
        "/RMG/Generator/Select GPS",
        "/gps/particle geantino",
        "/gps/energy 1 MeV",
        "/gps/ang/type iso",
        "/run/beamOn 100000",
    ]

    remage_run(macro, gdml_files=str(gdml_file), raise_on_error=True)
