from __future__ import annotations

import re
from collections import Counter

import pytest

pytestmark = pytest.mark.needs_remage


def overlap_findings(log: str) -> list[tuple[str, str]]:
    """Return the problems found in the remage output `log`, as (key, detail).

    The key names the problem without numbers (e.g. the overlapping volume
    pair) so that it is the same for all geometries that have it. Reports each
    Geant4 overlap warning (GeomVol1002) and, for the geantino check, the first
    error of each geantino with the number of geantinos that hit it. Later
    errors of a geantino follow from its first one. remage warnings are reported
    only if nothing else is found.
    """
    findings = []

    for block in re.findall(r"G4Exception-START.*?G4Exception-END", log, re.DOTALL):
        lines = [line.strip() for line in block.splitlines()[1:-1]]
        code = lines[0].removeprefix("*** G4Exception : ")
        text = " ".join(
            line
            for line in lines[1:]
            if line and not line.startswith(("issued by", "NOTE:", "***"))
        )
        volumes = sorted(set(re.findall(r"(\w+)(?::\d+)? \(G4\w+\)", text)))
        key = f"{code}: {' ↔ '.join(volumes)}" if volumes else f"{code}: {text}"
        findings.append((key, f"{code}: {text}"))

    first_errors = {}
    other = Counter()
    warnings = Counter()
    for line in log.splitlines():
        m = re.match(r"^\[Error ---> \[(\d+)\] (.*?), steps: (.*)$", line)
        if m:
            first_errors.setdefault(m[1], (m[2], m[3].strip()))
        elif re.match(r"^\[(Error|Fatal)\b", line):
            other[line.strip()] += 1
        elif line.startswith("[Warning"):
            warnings[line.strip()] += 1

    errors = Counter(msg for msg, _ in first_errors.values())
    for msg, n in errors.most_common():
        steps = next(s for m, s in first_errors.values() if m == msg)
        m = re.match(r"post-step (\w+) is no daughter of pre-step (\w+)", msg)
        key = f"geantino: {' ↔ '.join(sorted(m.groups()))}" if m else msg
        findings.append((key, f"{msg} ({n} geantinos, e.g. steps: {steps})"))

    for lines in (other, warnings):
        findings += [
            (line, f"{line} (x{n})" if n > 1 else line) for line, n in lines.items()
        ]
        if findings:
            break

    return findings


def check_remage_output(request, capfd, ec: int, ok_codes: tuple[int, ...]) -> None:
    """Fail the test with the problems found in the remage output, if any."""
    out, err = capfd.readouterr()
    if ec in ok_codes:
        return

    findings = overlap_findings(out + err)
    request.node.user_properties.append(
        ("remage_findings", sorted({key for key, _ in findings}))
    )

    report = [detail for _, detail in findings] or [
        "no problem found in the remage output, last lines:",
        *(out + err).splitlines()[-20:],
    ]
    pytest.fail(
        f"remage exit code {ec}\n" + "\n".join(f"  {line}" for line in report),
        pytrace=False,
    )


def test_overlaps(gdml_file, request, capfd):
    from remage import remage_run

    macro = [
        "/RMG/Geometry/RegisterDetectorsFromGDML Germanium",
        "/run/initialize",
    ]

    ec, _ = remage_run(macro, gdml_files=str(gdml_file), raise_on_error=False)
    check_remage_output(request, capfd, ec, ok_codes=(0,))


def test_surface_overlaps(gdml_file, request, capfd):
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

    # exit code 2: remage warnings only, the geantino check reports errors
    ec, _ = remage_run(macro, gdml_files=str(gdml_file), raise_on_error=False)
    check_remage_output(request, capfd, ec, ok_codes=(0, 2))
